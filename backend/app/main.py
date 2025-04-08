"""
Main FastAPI application for the MCP server.
This module provides the main FastAPI application with API endpoints and WebSocket support.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from .kit_client.api import KitClient, KitClientConfig
from .intent_service.claude import ClaudeIntentService
from .conversation.manager import ConversationManager
from .mcp_server.server import KitMCPServer
from .api import status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kit.com MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router)

conversation_manager = ConversationManager()

websocket_connections = {}

@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/api/chat")
async def chat(request: Request):
    """
    Chat endpoint for processing messages.
    """
    try:
        data = await request.json()
        message = data.get("message", "")
        conversation_id = data.get("conversation_id")
        
        kit_api_key = request.headers.get("X-Kit-API-Key") or os.getenv("KIT_API_KEY", "")
        claude_api_key = request.headers.get("X-Claude-API-Key") or os.getenv("CLAUDE_API_KEY", "")
        
        if not kit_api_key:
            raise HTTPException(status_code=400, detail="Kit.com API key is required")
        
        if not claude_api_key:
            raise HTTPException(status_code=400, detail="Claude API key is required")
        
        kit_client = KitClient(KitClientConfig(api_key=kit_api_key))
        intent_service = ClaudeIntentService(api_key=claude_api_key)
        mcp_server = KitMCPServer(kit_client, intent_service, conversation_manager)
        
        result = await mcp_server.process_message(message, conversation_id)
        
        await kit_client.close()
        
        return result
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    """
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    websocket_connections[connection_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message = message_data.get("message", "")
                conversation_id = message_data.get("conversation_id")
                kit_api_key = message_data.get("kit_api_key", "")
                claude_api_key = message_data.get("claude_api_key", "")
                
                if not kit_api_key:
                    await websocket.send_json({
                        "error": "Kit.com API key is required",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                if not claude_api_key:
                    await websocket.send_json({
                        "error": "Claude API key is required",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                kit_client = KitClient(KitClientConfig(api_key=kit_api_key))
                intent_service = ClaudeIntentService(api_key=claude_api_key)
                mcp_server = KitMCPServer(kit_client, intent_service, conversation_manager)
                
                result = await mcp_server.process_message(message, conversation_id)
                
                await kit_client.close()
                
                result["timestamp"] = datetime.now().isoformat()
                
                await websocket.send_json(result)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                await websocket.send_json({
                    "error": f"Error processing message: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if connection_id in websocket_connections:
            del websocket_connections[connection_id]
