"""
Refactored CogniVera Function Caller
- Fully aligned with legacy protocol messaging
- Compatible with updated TCPClient (send_message)
"""

import json
import logging
import base64
from typing import Dict, Any, Optional
import requests

from socketR import TCPClient

logger = logging.getLogger(__name__)


class RobotFunctionCaller:

    FUNCTION_CALL = "80"

    PROTOCOL_COMMANDS = {
        "CHANGEX": "10",
        "CHANGEY": "11",
        "CHANGEZ": "12",
        "MOVE": "13",
        "GRIPPER_OPEN": "20",
        "GRIPPER_CLOSE": "21",
        "ROTATE": "40",
        "ASSEMBLY": "69"
    }

    LEFT = "0"
    RIGHT = "1"

    DEFAULT_COORDS = {
        "R": {
            "Home": [460, -350, 75],
            "HomeR": [480, -327, 140]
        },
        "L": {
            "Home": [460, 350, 75],
            "HomeR": [480, -327, 140]
        }
    }

    DEFAULT_ROTATIONS = {
        "Down": [0, 180, 90],
        "Front": [-90, 0, -90],
        "SideR": [-90, 0, 0],
        "SideL": [-90, 0, 180]
    }

    def __init__(self, robot_on=True, host="192.168.125.1", port=5000, api_key=None):
        self.robot_on = robot_on
        self.api_key = api_key
        self.msg = ""
        self.last_update = "Initialized"

        self.left_position = [0, 0, 0]
        self.right_position = [0, 0, 0]

        self.socket_client = None
        if self.robot_on:
            try:
                self.socket_client = TCPClient(host, port)
                logger.info("Robot connected")
            except Exception as e:
                logger.warning(f"Robot unavailable: {e}")
                self.robot_on = False

    # -----------------------------
    # PUBLIC EXECUTION ENTRY
    # -----------------------------
    def execute_function(self, function_data: Dict[str, Any]) -> Dict[str, Any]:

        name = function_data.get("Name")
        params = function_data.get("Params", {})

        try:
            if name == "Move":
                self._move(params)
            elif name == "MoveTo":
                self._move_to(params)
            elif name == "Grip":
                self._grip(params)
            elif name == "Rotate":
                self._rotate(params)
            elif name == "Assembly":
                self._assembly(params)
            elif name == "Identify":
                return self._identify(params)
            else:
                return {"status": "error", "message": f"Unknown function {name}"}

# ✅ Use correct method from socketR
            if self.robot_on and self.socket_client:
                reply = self.socket_client.send_message(self.msg)
                self._parse_response(reply)

            return { "status": "success",
                     "update": self.last_update,
                     "message": self.msg# helpful for debugging
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # -----------------------------
    # CORE BUILDING
    # -----------------------------
    def _format_xyz(self, x, y, z):
        return (
            ("0" if x >= 0 else "1") + f"{abs(int(x)):03d}" +
            ("0" if y >= 0 else "1") + f"{abs(int(y)):03d}" +
            ("0" if z >= 0 else "1") + f"{abs(int(z)):03d}"
        )

    def _build_msg(self, arm, command, x=0, y=0, z=0):
        return (
            (self.LEFT if arm == "Left" else self.RIGHT) +
            self.FUNCTION_CALL +
            command +
            self._format_xyz(x, y, z)
        )

    # -----------------------------
    # FUNCTION IMPLEMENTATIONS
    # -----------------------------
    def _move(self, p):
        axis = p.get("Axis")
        units = int(p.get("Units", 0))
        arm = p.get("Arm", "Left")

        x = y = z = 0

        if axis == "X":
            x = units
            cmd = self.PROTOCOL_COMMANDS["CHANGEX"]
        elif axis == "Y":
            y = units
            cmd = self.PROTOCOL_COMMANDS["CHANGEY"]
        else:
            z = units
            cmd = self.PROTOCOL_COMMANDS["CHANGEZ"]

        self.msg = self._build_msg(arm, cmd, x, y, z)
        self.last_update = f"Moved {arm} by {units} along {axis}"

    def _move_to(self, p):
        arm = p.get("Arm", "Left")

        if p.get("Type") == "Name":
            coords = self.DEFAULT_COORDS["R" if arm == "Right" else "L"][p.get("Name")]
        else:
            coords = [p.get("X", 0), p.get("Y", 0), p.get("Z", 0)]

        x, y, z = coords

        self.msg = self._build_msg(arm, self.PROTOCOL_COMMANDS["MOVE"], x, y, z)
        self.last_update = f"Moved {arm} to ({x},{y},{z})"

    def _grip(self, p):
        arm = p.get("Arm", "Left")
        state = str(p.get("State", "0"))

        cmd = self.PROTOCOL_COMMANDS["GRIPPER_CLOSE"] if state == "1" else self.PROTOCOL_COMMANDS["GRIPPER_OPEN"]

        self.msg = self._build_msg(arm, cmd, 0, 0, 0)
        self.last_update = f"{arm} gripper {'closed' if state == '1' else 'opened'}"

    def _rotate(self, p):
        arm = p.get("Arm", "Left")
        pos = p.get("Position", "Front")

        if pos == "Side":
            rot = self.DEFAULT_ROTATIONS["SideR" if arm == "Right" else "SideL"]
        else:
            rot = self.DEFAULT_ROTATIONS.get(pos, self.DEFAULT_ROTATIONS["Front"])

        x, y, z = rot

        self.msg = self._build_msg(arm, self.PROTOCOL_COMMANDS["ROTATE"], x, y, z)
        self.last_update = f"{arm} rotated to {pos}"

    def _assembly(self, p):
        step = int(p.get("Step", 0))

        left_steps = {2, 3, 5, 7, 9, 11, 14}
        arm = "Left" if step in left_steps else "Right"

        self.msg = self._build_msg(arm, self.PROTOCOL_COMMANDS["ASSEMBLY"], step, 0, 0)
        self.last_update = f"Assembly step {step} complete"

    # -----------------------------
    # VISION
    # -----------------------------
    def _identify(self, p):
        if not self.api_key:
            return {"status": "error", "message": "No API key"}

        query = p.get("Query")

        with open("frame.jpg", "rb") as f:
            img = base64.b64encode(f.read()).decode()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4-turbo",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img}"}
                    }
                ]
            }]
        }

        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        out = res.json()

        return {"status": "success", "result": out["choices"][0]["message"]["content"]}

    # -----------------------------
    # RESPONSE PARSING
    # -----------------------------
    def _parse_response(self, reply):
        try:
            values = reply.split('|')
            arm = values[0][0]
            pos = list(map(float, values[-3:]))

            if arm == self.LEFT:
                self.left_position = pos
            else:
                self.right_position = pos

        except Exception:
            logger.warning("Failed to parse robot response")

    def close(self):
        if self.socket_client:
            self.socket_client.close()
