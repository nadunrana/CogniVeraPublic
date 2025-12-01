"""
CogniVera Function Caller Module
================================

This module implements robot action execution through function calls.
Translates high-level function requests into low-level protocol commands.

Supports: Movement, Gripper control, Rotation, Assembly tasks, Vision-based identification

Reference: https://doi.org/10.1109/ACCESS.2025.3565918
"""

import json
import logging
import base64
from typing import Optional, Dict, Any, List

import cv2
import numpy as np
import requests

from socketR import TCPClient

# Configure logging
logger = logging.getLogger(__name__)


class RobotFunctionCaller:
    """
    Executes robot functions and manages hardware communication.

    Handles function parsing from JSON commands and translates them into
    robot protocol messages. Supports movement, gripper control, rotation,
    assembly sequences, and vision-based tasks.

    Attributes:
        robot_on (bool): Whether hardware is available
        coordinates (dict): Predefined coordinate positions
        rotations (dict): Predefined rotation configurations
    """

    # Protocol command codes
    PROTOCOL_COMMANDS = {
        "CHANGEX": "10",
        "CHANGEY": "11",
        "CHANGEZ": "12",
        "MOVE": "13",
        "GRIPPER_OPEN": "20",
        "GRIPPER_CLOSE": "21",
        "GET_POSITION": "99",
        "SAVE_POSITION": "91",
        "ROTATE": "40",
        "ASSEMBLY": "69"
    }

    # Arm identifiers
    LEFT = "0"
    RIGHT = "1"

    # Coordinate frames
    DEFAULT_COORDS = {
        "R": {
            "Home": [460, -350, 75],
            "HomeR": [480, -327, 140]
        },
        "L": {
            "Home": [460, 350, 75],
            "HomeL": [480, 327, 140]
        }
    }

    # Rotation presets
    DEFAULT_ROTATIONS = {
        "Down": [0, 180, 90],
        "Front": [-90, 0, -90],
        "SideR": [-90, 0, 0],
        "SideL": [-90, 0, 180]
    }

    def __init__(
            self,
            robot_on: bool = True,
            host: str = "192.168.125.1",
            port: int = 5000,
            api_key: Optional[str] = None
    ):
        """
        Initialize function caller.

        Args:
            robot_on (bool): Enable hardware communication. Default: True
            host (str): Robot controller IP. Default: 192.168.125.1
            port (int): Robot controller port. Default: 5000
            api_key (str, optional): OpenAI API key for vision tasks
        """
        self.robot_on = robot_on
        self.host = host
        self.port = port
        self.api_key = api_key

        # Initialize socket connection if robot is enabled
        self.socket_client: Optional[TCPClient] = None
        if self.robot_on:
            try:
                self.socket_client = TCPClient(host, port)
                logger.info("Robot hardware connected")
            except Exception as e:
                logger.warning(f"Robot hardware unavailable: {str(e)}")
                self.robot_on = False

        # State tracking
        self.left_position = [0, 0, 0]
        self.right_position = [0, 0, 0]
        self.last_update = "Initialized"

    def execute_function(self, function_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a robot function based on JSON specification.

        Args:
            function_data (dict): Function definition with Name and Params

        Returns:
            dict: Update message with status
        """
        function_name = function_data.get("Name")
        params = function_data.get("Params", {})

        try:
            if function_name == "Move":
                self._execute_move(params)
            elif function_name == "MoveTo":
                self._execute_move_to(params)
            elif function_name == "Grip":
                self._execute_grip(params)
            elif function_name == "Rotate":
                self._execute_rotate(params)
            elif function_name == "Assembly":
                self._execute_assembly(params)
            elif function_name == "Identify":
                return self._execute_identify(params)
            else:
                logger.warning(f"Unknown function: {function_name}")
                self.last_update = f"Unknown function: {function_name}"

            # Send message to robot if hardware is available
            if self.robot_on and self.socket_client:
                try:
                    response = self.socket_client.send_message(self._build_message())
                    self._parse_response(response)
                except Exception as e:
                    logger.error(f"Hardware communication error: {str(e)}")

            return {"status": "success", "update": self.last_update}

        except Exception as e:
            logger.error(f"Function execution error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _execute_move(self, params: Dict[str, Any]) -> None:
        """Execute incremental movement command."""
        axis = params.get("Axis", "X")
        units = int(params.get("Units", 0))
        arm = params.get("Arm", "Left")

        if axis == "X":
            command = self.PROTOCOL_COMMANDS["CHANGEX"]
            self.last_update = f"Moved {arm} arm by {units} units along X axis"
        elif axis == "Y":
            command = self.PROTOCOL_COMMANDS["CHANGEY"]
            self.last_update = f"Moved {arm} arm by {units} units along Y axis"
        elif axis == "Z":
            command = self.PROTOCOL_COMMANDS["CHANGEZ"]
            self.last_update = f"Moved {arm} arm by {units} units along Z axis"

        logger.info(self.last_update)

    def _execute_move_to(self, params: Dict[str, Any]) -> None:
        """Execute absolute movement to named position or coordinates."""
        move_type = params.get("Type", "Coordinate")
        arm = params.get("Arm", "Left")

        if move_type == "Coordinate":
            x = int(params.get("X", 0))
            y = int(params.get("Y", 0))
            z = int(params.get("Z", 0))
            self.last_update = f"Moved {arm} to coordinates ({x}, {y}, {z})"
        elif move_type == "Name":
            name = params.get("Name", "Home")
            coords = self.DEFAULT_COORDS["R" if arm == "Right" else "L"].get(name)
            if coords:
                self.last_update = f"Moved {arm} to preset '{name}'"
            else:
                self.last_update = f"Unknown preset position: {name}"

        logger.info(self.last_update)

    def _execute_grip(self, params: Dict[str, Any]) -> None:
        """Execute gripper open/close."""
        arm = params.get("Arm", "Left")
        state = str(params.get("State", "0"))

        if state == "1":
            self.last_update = f"{arm} gripper closed"
        elif state == "0":
            self.last_update = f"{arm} gripper opened"

        logger.info(self.last_update)

    def _execute_rotate(self, params: Dict[str, Any]) -> None:
        """Execute end-effector rotation."""
        arm = params.get("Arm", "Left")
        position = params.get("Position", "Front")

        if position in self.DEFAULT_ROTATIONS:
            rotation = self.DEFAULT_ROTATIONS[position]
            self.last_update = f"{arm} rotated to {position}: {rotation}"
        else:
            self.last_update = f"Unknown rotation: {position}"

        logger.info(self.last_update)

    def _execute_assembly(self, params: Dict[str, Any]) -> None:
        """Execute assembly step."""
        step = int(params.get("Step", 0))
        self.last_update = f"Assembly step {step} completed"
        logger.info(self.last_update)

    def _execute_identify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute vision-based identification."""
        query = params.get("Query", "What do you see?")

        try:
            # Capture image (stub implementation)
            # In production, would use cv2.VideoCapture
            logger.info(f"Vision query: {query}")

            # Call GPT-4 Vision for analysis
            response = self._query_vision(query)
            return {"status": "success", "result": response}

        except Exception as e:
            logger.error(f"Vision identification error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _query_vision(self, query: str, image_path: str = "frame.jpg") -> str:
        """Query GPT-4 Vision for image analysis."""
        if not self.api_key:
            logger.warning("Vision query requested but no API key provided")
            return "Vision unavailable"

        try:
            # Encode image to base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Call GPT-4 Vision API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": "gpt-4-turbo",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }],
                "max_tokens": 300
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )

            result = response.json()
            answer = result['choices'][0]['message']['content']
            logger.info(f"Vision result: {answer}")
            return answer

        except Exception as e:
            logger.error(f"Vision API error: {str(e)}")
            return f"Error: {str(e)}"

    def _build_message(self) -> str:
        """Build protocol message (stub - implement per your robot protocol)."""
        return ""

    def _parse_response(self, response: str) -> None:
        """Parse robot response and update position tracking."""
        try:
            values = response.split('|')
            if len(values) >= 3:
                arm = values[0][0]
                positions = [float(v) for v in values[-3:]]

                if arm == self.LEFT:
                    self.left_position = positions
                elif arm == self.RIGHT:
                    self.right_position = positions

                logger.debug(f"Position updated: {positions}")
        except Exception as e:
            logger.warning(f"Could not parse response: {str(e)}")

    def close(self) -> None:
        """Close hardware connection."""
        if self.socket_client:
            self.socket_client.close()
            logger.info("Hardware connection closed")


# Legacy alias for backward compatibility
functioncall = RobotFunctionCaller