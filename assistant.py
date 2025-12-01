"""
CogniVera Assistant Module
===========================

This module implements the GPTAgent class for interfacing with OpenAI's LLM API.
It handles message management, system prompts, and JSON-formatted responses.

Reference: https://doi.org/10.1109/ACCESS.2025.3565918
"""

import os
import json
import logging
from typing import Optional
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)


class GPTAgent:
    """
    LLM Agent for conversational AI powered by OpenAI's GPT models.

    This system can also be implemented with any available online/offline model.
    But the prompting(controller.py) and the generation commands will have to be
    changed accordingly.

    This agent manages conversation history, system prompts, and generates
    JSON-formatted responses for structured interaction with robot controllers.

    Attributes:
        system_prompt (str): System prompt defining agent behavior
        messages (list): Conversation history
        json_reply (bool): Whether to enforce JSON response format
        client: OpenAI client instance
    """

    def __init__(self, api_key: Optional[str] = None, json_reply: bool = True):
        """
        Initialize GPT Agent.

        Args:
            api_key (str, optional): OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            json_reply (bool): Enforce JSON format in responses. Default: True
        """
        self.system_prompt = "You are a helpful assistant."
        self.messages = []
        self.json_reply = json_reply

        # Initialize OpenAI client
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)
        logger.info("GPTAgent initialized successfully")

    def chat(self, query: str) -> str:
        """
        Send a query and receive a response.

        Args:
            query (str): User query or request

        Returns:
            str: LLM response (JSON string if json_reply=True)

        Raises:
            ValueError: If API response is invalid
        """
        try:
            response = self._make_openai_request(query)
            message = response.choices[0].message
            self.messages.append(message)
            logger.debug(f"Chat response received: {message.content[:50]}...")
            return message.content
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise

    def _make_openai_request(self, query: str):
        """
        Make API request to OpenAI.

        Args:
            query (str): Query to send

        Returns:
            ChatCompletion: Response object from OpenAI
        """
        # Prepare message history
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.messages,
            {"role": "user", "content": query}
        ]

        # Prepare request parameters
        request_params = {
            "model": "gpt-4-turbo",
            "messages": messages,
        }

        # Add JSON format requirement if needed
        if self.json_reply:
            request_params["response_format"] = {"type": "json_object"}

        logger.debug(f"Sending request with {len(messages)} messages")
        response = self.client.chat.completions.create(**request_params)
        return response

    def define_prompt(self, prompt: str) -> None:
        """
        Define or update the system prompt.

        Args:
            prompt (str): New system prompt
        """
        self.system_prompt = prompt
        self.messages = []  # Clear history with new prompt
        logger.info("System prompt updated, conversation history cleared")

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages = []
        logger.info("Conversation history cleared")

    def get_system_prompt(self) -> str:
        """
        Get current system prompt.

        Returns:
            str: Current system prompt
        """
        return self.system_prompt