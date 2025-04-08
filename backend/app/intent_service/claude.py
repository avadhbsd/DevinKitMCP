"""
Intent Recognition Service using Claude API.
This module provides a service for determining user intent from messages using Claude API.
"""

from typing import Any, Dict, List, Optional
import logging
import json
import os
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeIntentService:
    """Service for determining user intent using Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Claude Intent Service.

        Args:
            api_key: Claude API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"ClaudeIntentService initialized with model {model}")

    async def determine_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the intent of a user message.

        Args:
            message: User's message
            context: Conversation context

        Returns:
            Intent information including tool to use and parameters
        """
        prompt = self._construct_intent_prompt(message, context)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0,
                system="You are an assistant that helps determine user intent for a Kit.com MCP server. Your task is to analyze the user's message and determine which tool to use and what parameters to pass to it. Respond in JSON format only.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text

            try:
                if content.strip().startswith("```json") and content.strip().endswith("```"):
                    json_content = content.strip().replace("```json", "", 1)
                    json_content = json_content.rsplit("```", 1)[0].strip()
                    intent_data = json.loads(json_content)
                else:
                    intent_data = json.loads(content)

                logger.info(f"Intent determined: {intent_data}")
                return intent_data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Claude response as JSON: {content}")
                return {
                    "tool": "explain_concept",
                    "parameters": {"concept": "error"},
                    "needs_clarification": True,
                    "clarification_question": "I'm sorry, I couldn't understand your request. Could you please rephrase it?"
                }

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            if "invalid x-api-key" in str(e) or "authentication_error" in str(e):
                return {
                    "tool": None,
                    "parameters": {},
                    "needs_clarification": True,
                    "clarification_question": "I'm sorry, there's an authentication issue with the Claude API. Please check your API key configuration."
                }
            return {
                "tool": "explain_concept",
                "parameters": {"concept": "error"},
                "needs_clarification": True,
                "clarification_question": "I'm sorry, I encountered an error processing your request. Could you please try again?"
            }

    def _construct_intent_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """
        Construct a prompt for Claude to determine intent.

        Args:
            message: User's message
            context: Conversation context

        Returns:
            Prompt for Claude
        """
        tools_description = """
        Available tools:
        1. get_tags() - Get all tags from Kit.com
        2. count_tags() - Count the number of tags
        3. create_tag(name: str) - Create a new tag
        4. tag_subscriber(email: str, tag_name: str) - Tag a subscriber with a specific tag
        5. get_subscribers(limit: int = 10, sort_by: str = "created_at", sort_order: str = "desc") - Get subscribers
        6. count_subscribers() - Count the number of subscribers
        7. get_subscriber_details(email: str) - Get details for a specific subscriber
        8. get_forms() - Get all forms from Kit.com
        9. create_form(name: str, redirect_url: Optional[str] = None) - Create a new form
        10. explain_concept(concept: str) - Explain a Kit.com concept
        """

        prompt = f"""
        {message}

        {json.dumps(context, indent=2)}

        {tools_description}

        Analyze the user's message and determine which tool to use and what parameters to pass to it.
        If you need more information from the user to determine the intent, indicate that clarification is needed.

        Respond in the following JSON format:
        ```json
        {{
            "tool": "tool_name",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "needs_clarification": false,
            "clarification_question": null
        }}
        ```

        If clarification is needed:
        ```json
        {{
            "tool": null,
            "parameters": {{}},
            "needs_clarification": true,
            "clarification_question": "What specific information do you need?"
        }}
        ```

        JSON response only:
        """

        return prompt

    async def explain_concept(self, concept: str, documentation: str) -> str:
        """
        Explain a Kit.com concept using the documentation.

        Args:
            concept: The concept to explain
            documentation: Kit.com documentation

        Returns:
            Explanation of the concept
        """

        prompt = f"""
        {documentation}

        What are {concept}?

        Provide a clear, concise explanation of the concept of "{concept}" in Kit.com based on the documentation above.
        Format your response using Markdown for better readability.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.2,
                system="You are an assistant that explains Kit.com concepts clearly and accurately based on the provided documentation.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            explanation = response.content[0].text
            logger.info(f"Concept explanation generated for: {concept}")
            return explanation

        except Exception as e:
            logger.error(f"Error calling Claude API for concept explanation: {str(e)}")
            return f"I'm sorry, I encountered an error while trying to explain the concept of {concept}. Please try again later."

    async def format_response(self, tool_name: str, result: Any, context: Dict[str, Any]) -> str:
        """
        Format the response to the user based on the tool result.

        Args:
            tool_name: Name of the tool that was executed
            result: Result of the tool execution
            context: Conversation context

        Returns:
            Formatted response to the user
        """
        prompt = f"""
        {tool_name}

        {json.dumps(result, indent=2)}

        {json.dumps(context, indent=2)}

        Format the result into a helpful, natural language response for the user.
        Use Markdown formatting for better readability.
        Be concise but informative.
        If the result contains IDs or other technical details that might be useful to the user, include them.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                system="You are an assistant that formats technical results into helpful, natural language responses for users.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            formatted_response = response.content[0].text
            logger.info(f"Response formatted for tool: {tool_name}")
            return formatted_response

        except Exception as e:
            logger.error(f"Error calling Claude API for response formatting: {str(e)}")
            if isinstance(result, list):
                return f"Here are the results:\n\n```json\n{json.dumps(result, indent=2)}\n```"
            else:
                return f"Here is the result:\n\n```json\n{json.dumps(result, indent=2)}\n```"

    async def generate_response(self, message: str, context: Dict[str, Any]) -> str:
        """
        Generate a response to a user message when no specific tool matches.

        Args:
            message: User's message
            context: Conversation context

        Returns:
            Generated response
        """
        prompt = f"""
        {message}

        {json.dumps(context, indent=2)}

        Generate a helpful response to the user's message. If you don't know the answer, suggest what tools or information might help.
        Use Markdown formatting for better readability.
        """

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                system="You are an assistant for Kit.com that helps users with their questions and tasks.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            generated_response = response.content[0].text
            logger.info("Generated response for user message")
            return generated_response

        except Exception as e:
            logger.error(f"Error calling Claude API for response generation: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
