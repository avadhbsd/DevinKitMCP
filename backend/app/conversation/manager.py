"""
Conversation Manager for the MCP server.
This module provides a service for managing conversation state and context.
"""

from typing import Dict, Any, List, Optional
import logging
import uuid
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationManager:
    """Manager for conversation state and context."""

    def __init__(self, max_history: int = 10):
        """
        Initialize the Conversation Manager.

        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.max_history = max_history
        logger.info(f"ConversationManager initialized with max_history={max_history}")

    def create_conversation(self) -> str:
        """
        Create a new conversation.

        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = {
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "context": {},
            "last_updated": time.time()
        }
        logger.info(f"Created new conversation with ID: {conversation_id}")
        return conversation_id

    def get_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the context for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation context
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation ID not found: {conversation_id}")
            return {}
        
        return self.conversations[conversation_id].get("context", {})

    def update_context(self, conversation_id: str, message: str, intent_result: Dict[str, Any]) -> None:
        """
        Update the context for a conversation.

        Args:
            conversation_id: Conversation ID
            message: User message
            intent_result: Intent recognition result
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation ID not found: {conversation_id}")
            return
        
        context = self.conversations[conversation_id].get("context", {})
        
        messages = self.conversations[conversation_id].get("messages", [])
        messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(messages) > self.max_history * 2:  # *2 because we store both user and assistant messages
            messages = messages[-self.max_history * 2:]
        
        context["last_intent"] = intent_result.get("tool")
        context["last_parameters"] = intent_result.get("parameters", {})
        
        context["history"] = messages
        
        self.conversations[conversation_id]["context"] = context
        self.conversations[conversation_id]["messages"] = messages
        self.conversations[conversation_id]["last_updated"] = time.time()
        
        logger.info(f"Updated context for conversation: {conversation_id}")

    def add_response(self, conversation_id: str, response: str) -> None:
        """
        Add an assistant response to a conversation.

        Args:
            conversation_id: Conversation ID
            response: Assistant response
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation ID not found: {conversation_id}")
            return
        
        messages = self.conversations[conversation_id].get("messages", [])
        messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(messages) > self.max_history * 2:  # *2 because we store both user and assistant messages
            messages = messages[-self.max_history * 2:]
        
        self.conversations[conversation_id]["messages"] = messages
        self.conversations[conversation_id]["last_updated"] = time.time()
        
        logger.info(f"Added response to conversation: {conversation_id}")

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get the message history for a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation ID not found: {conversation_id}")
            return []
        
        return self.conversations[conversation_id].get("messages", [])

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False otherwise
        """
        if conversation_id not in self.conversations:
            logger.warning(f"Conversation ID not found: {conversation_id}")
            return False
        
        del self.conversations[conversation_id]
        logger.info(f"Deleted conversation: {conversation_id}")
        return True

    def cleanup_old_conversations(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old conversations.

        Args:
            max_age_seconds: Maximum age of conversations to keep

        Returns:
            Number of conversations deleted
        """
        current_time = time.time()
        to_delete = []
        
        for conversation_id, conversation in self.conversations.items():
            last_updated = conversation.get("last_updated", 0)
            if current_time - last_updated > max_age_seconds:
                to_delete.append(conversation_id)
        
        for conversation_id in to_delete:
            del self.conversations[conversation_id]
        
        logger.info(f"Cleaned up {len(to_delete)} old conversations")
        return len(to_delete)
