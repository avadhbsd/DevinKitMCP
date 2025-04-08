"""
Kit.com MCP Server for integrating Kit.com API with Claude API.
This module provides a server for handling MCP requests and responses.
"""

from typing import Any, Dict, List, Optional
import logging
import json
import os
from fastapi import HTTPException

from ..kit_client.api import KitClient
from ..intent_service.claude import ClaudeIntentService
from ..conversation.manager import ConversationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KitMCPServer:
    """Server for handling MCP requests and responses."""

    def __init__(self, kit_client: KitClient, intent_service: ClaudeIntentService, 
                conversation_manager: ConversationManager):
        """
        Initialize the Kit.com MCP Server.

        Args:
            kit_client: Kit.com API client
            intent_service: Intent recognition service
            conversation_manager: Conversation manager
        """
        self.kit_client = kit_client
        self.intent_service = intent_service
        self.conversation_manager = conversation_manager
        logger.info("KitMCPServer initialized successfully")

    async def process_message(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a message and return a response.

        Args:
            message: User's message
            conversation_id: Conversation ID

        Returns:
            Response information
        """
        if not conversation_id:
            conversation_id = self.conversation_manager.create_conversation()

        context = self.conversation_manager.get_context(conversation_id)

        intent_result = await self.intent_service.determine_intent(message, context)
        self.conversation_manager.update_context(conversation_id, message, intent_result)

        if intent_result.get("needs_clarification"):
            response = intent_result.get("clarification_question")
        else:
            tool_name = intent_result.get("tool")
            tool_params = intent_result.get("parameters", {})

            response = await self._execute_tool(tool_name, tool_params, context)

        self.conversation_manager.add_response(conversation_id, response)

        return {
            "response": response,
            "conversation_id": conversation_id
        }

    async def _execute_tool(self, tool_name: str, tool_params: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Execute a tool and return a response.

        Args:
            tool_name: Name of the tool to execute
            tool_params: Parameters for the tool
            context: Conversation context

        Returns:
            Response from the tool
        """
        tool_map = {
            "get_tags": self.kit_client.get_tags,
            "count_tags": self._count_tags,
            "create_tag": self.kit_client.create_tag,
            "tag_subscriber": self._tag_subscriber,
            "get_subscribers": self.kit_client.get_subscribers,
            "count_subscribers": self.kit_client.count_subscribers,
            "get_subscriber_details": self.kit_client.get_subscriber_by_email,
            "get_forms": self.kit_client.get_forms,
            "create_form": self.kit_client.create_form,
            "explain_concept": self._explain_concept
        }

        if tool_name not in tool_map:
            return await self.intent_service.generate_response(
                f"I don't know how to {tool_name.replace('_', ' ')}.", context
            )

        try:
            result = await tool_map[tool_name](**tool_params)
            return await self.intent_service.format_response(tool_name, result, context)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return f"I'm sorry, I encountered an error while trying to {tool_name.replace('_', ' ')}. Error: {str(e)}"

    async def _count_tags(self) -> int:
        """
        Count the number of tags.

        Returns:
            Number of tags
        """
        tags = await self.kit_client.get_tags()
        return len(tags)

    async def _tag_subscriber(self, email: str, tag_name: str) -> Dict[str, Any]:
        """
        Tag a subscriber with a specific tag.

        Args:
            email: Email address of the subscriber
            tag_name: Name of the tag

        Returns:
            Result of the tagging operation
        """
        tags = await self.kit_client.get_tags()
        tag_id = None

        for tag in tags:
            if tag.get("name") == tag_name:
                tag_id = tag.get("id")
                break

        if not tag_id:
            new_tag = await self.kit_client.create_tag(tag_name)
            tag_id = new_tag.get("id")

        if not tag_id:
            raise HTTPException(status_code=404, detail=f"Tag '{tag_name}' not found and could not be created")

        return await self.kit_client.tag_subscriber_by_email(email, tag_id)

    async def _explain_concept(self, concept: str) -> str:
        """
        Explain a Kit.com concept.

        Args:
            concept: Concept to explain

        Returns:
            Explanation of the concept
        """
        documentation = """
        Tags are labels that you can apply to subscribers to segment your audience.
        They help you organize subscribers based on interests, behaviors, or other criteria.

        Subscribers are people who have signed up to receive your emails.
        They can be in different states: active, inactive, cancelled, bounced, or complained.

        Forms are used to collect subscriber information and add them to your list.
        They can be embedded on your website or shared via a direct link.

        Broadcasts are one-time emails sent to segments of your audience.
        They can be scheduled or sent immediately.
        """

        return await self.intent_service.explain_concept(concept, documentation)
