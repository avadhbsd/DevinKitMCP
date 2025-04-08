"""
API status endpoints for the MCP server.
This module provides endpoints for checking the status of the API connections.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
import os
import logging
from typing import Dict, Any

from ..kit_client.api import KitClient, KitClientConfig

router = APIRouter(prefix="/api/status", tags=["status"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/kit")
async def kit_status(request: Request):
    """
    Check the status of the Kit.com API connection.
    """
    api_key = request.headers.get("X-Kit-API-Key") or os.getenv("KIT_API_KEY", "")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="Kit.com API key is required")
    
    try:
        kit_client = KitClient(KitClientConfig(api_key=api_key))
        account_info = await kit_client.get_account_info()
        await kit_client.close()
        
        return {
            "status": "connected",
            "account": account_info.get("account", {}).get("name", "Unknown")
        }
    except Exception as e:
        logger.error(f"Error connecting to Kit.com API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Kit.com API: {str(e)}")

@router.get("/claude")
async def claude_status(request: Request):
    """
    Check the status of the Claude API connection.
    """
    from ..intent_service.claude import ClaudeIntentService
    
    api_key = request.headers.get("X-Claude-API-Key") or os.getenv("CLAUDE_API_KEY", "")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="Claude API key is required")
    
    try:
        intent_service = ClaudeIntentService(api_key=api_key)
        test_result = await intent_service.determine_intent("Test message", {})
        
        if "authentication_error" in str(test_result):
            raise HTTPException(status_code=401, detail="Invalid Claude API key")
        
        return {
            "status": "connected",
            "model": intent_service.model
        }
    except Exception as e:
        logger.error(f"Error connecting to Claude API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Claude API: {str(e)}")
