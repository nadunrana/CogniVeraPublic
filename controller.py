"""
CogniVera Controller Module
===========================

Orchestrates dual-agent system: Main Agent (task execution) and Validation Agent (quality assurance).
Handles request processing, LLM interactions, and feedback loops.

"""

import json
import logging
import time
from typing import Tuple, Dict, Any, Optional

from assistant import GPTAgent
from logger import ExperimentLogger

# Configure logging
logger = logging.getLogger(__name__)


class AgentController:
    """
    Dual-agent controller for human-robot collaboration.

    Manages Main Agent (generates responses and function calls) and Validation Agent
    (verifies accuracy and provides feedback). Implements feedback loop for correction.

    Attributes:
        main_agent (GPTAgent): Main conversational agent
        validation_agent (GPTAgent): Validation/quality assurance agent
        use_validation (bool): Enable validation feedback loop
        experiment_mode (bool): Alternative function set for experiments
    """

    def __init__(
            self,
            api_key: Optional[str] = None,
            use_validation: bool = True,
            experiment_mode: bool = False
    ):
        """
        Initialize controller with dual agents.

        Args:
            api_key (str, optional): OpenAI API key
            use_validation (bool): Enable validation agent. Default: True
            experiment_mode (bool): Use experimental function set. Default: False
        """
        self.main_agent = GPTAgent(api_key=api_key, json_reply=True)
        self.validation_agent = GPTAgent(api_key=api_key, json_reply=True)
        self.logger = ExperimentLogger()

        self.use_validation = use_validation
        self.experiment_mode = experiment_mode

        # System configuration
        self.environment = self._build_environment_description()
        self.functions = self._build_function_definitions()

        # Define agent prompts
        self._configure_agents()

        logger.info("AgentController initialized")

    def process_request(self, request_json: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """
        Process user request through dual-agent system.

        Args:
            request_json (dict): Request in format {IP: {Type, Data}, State}

        Returns:
            tuple: (response_json, validation_score)
        """
        request_type = request_json.get("IP", {}).get("Type", "Request")
        request_data = request_json.get("IP", {}).get("Data", "")
        state = request_json.get("State", "NULL")

        try:
            # Get Main Agent response
            main_response = self._get_main_agent_response(request_json)

            # Validate if enabled
            if self.use_validation and request_type != "Feedback":
                validation_result = self._validate_response(
                    request_json,
                    main_response
                )
                score = validation_result.get("score", 0)

                # If score is low and we can retry, provide feedback
                if score < 5 and score > 0:
                    feedback = validation_result.get("feedback", "")
                    main_response = self._provide_feedback_correction(
                        request_json,
                        main_response,
                        feedback
                    )
                    score = 10  # Updated response
            else:
                score = 10  # No validation or feedback type

            # Format response
            response_json = {
                "OP": main_response.get("OP", {}),
                "State": state
            }

            logger.info(f"Request processed: score={score}")
            return response_json, score

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                "OP": {
                    "Reply": f"Error processing request: {str(e)}",
                    "Function": {"Name": "0", "Params": {}}
                },
                "State": state
            }, 0

    def _get_main_agent_response(self, request_json: Dict[str, Any]) -> Dict[str, Any]:
        """Get response from Main Agent."""
        request_text = json.dumps(request_json)
        response_text = self.main_agent.chat(request_text)

        try:
            response_json = json.loads(response_text)
            return response_json
        except json.JSONDecodeError:
            logger.error("Main Agent did not return valid JSON")
            return {
                "OP": {
                    "Reply": "Internal error processing response",
                    "Function": {"Name": "0", "Params": {}}
                }
            }

    def _validate_response(
            self,
            request_json: Dict[str, Any],
            response_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate Main Agent response using Validation Agent."""
        validation_input = {
            "IP": request_json.get("IP", {}),
            "OP": response_json.get("OP", {})
        }

        validation_text = json.dumps(validation_input)
        validation_response = self.validation_agent.chat(validation_text)

        try:
            result = json.loads(validation_response)
            score = result.get("Feedback_score", 0)
            feedback = result.get("Feedback", "")
            return {"score": score, "feedback": feedback}
        except json.JSONDecodeError:
            logger.error("Validation Agent did not return valid JSON")
            return {"score": 5, "feedback": ""}

    def _provide_feedback_correction(
            self,
            request_json: Dict[str, Any],
            original_response: Dict[str, Any],
            feedback: str
    ) -> Dict[str, Any]:
        """Use feedback to generate corrected response."""
        feedback_request = {
            "IP": {
                "Type": "Feedback",
                "Data": feedback
            },
            "State": request_json.get("State", "NULL")
        }

        return self._get_main_agent_response(feedback_request)

    def _configure_agents(self) -> None:
        """Configure system prompts for both agents."""
        main_prompt = f"""
        You are the Main Agent controlling a dual-arm collaborative robot.

        Environment:
        {self.environment}

        Available Functions:
        {self.functions}

        Agent Description:
        The Main Agent controls the robot by responding to user requests and robot updates. 
        It generates conversational replies and calls functions when needed to execute actions.

        Behavior Rules:
        - Handle three types of inputs:
          1. "Request" → user commands or questions
             - Respond conversationally
             - Call relevant functions if required
          2. "Update" → robot feedback
             - Use updates to track progress
             - Continue or complete tasks
             - Inform the user when actions are finished
          3. "Feedback" → correction from validation agent
             - Revise your previous reply based on instructions
             - Provide corrected response as if original

        - If no function is required, set Function.Name = "0"
        - Always maintain a natural conversational style for the user
        - Ensure function calls are accurate and aligned with the task
        - Maintain awareness of the current system state
        - If the user says "end session", "stop", "shutdown", or similar:
          Call function "EndSession"
``

        Input Format:
        {{
          "IP": {{
            "Type": "Request | Update | Feedback",
            "Data": "Message content"
          }},
          "State": "Current system state or NULL if initial"
        }}

        Output Format:
        {{
          "OP": {{
            "Reply": "Conversational response to the user",
            "Function": {{
              "Name": "function_name or 0",
              "Params": {{
                "param_name": "value"
              }}
            }}
          }},
          "State": "Updated system state after action"
        }}

        All inputs and outputs MUST be valid JSON.
        """

        validation_prompt = f"""
        You are the Validation Agent for a human-robot collaboration system.

        Available Functions:
        {self.functions}

        Agent Description:
        You are responsible for validating the interaction between the user (IP) and the Main Agent (OP). 
        Your goal is to ensure correctness, safety, and consistency in all robot operations and responses.

        Behavior Rules:
        - Validate both:
          - IP (Input): incoming message
          - OP (Output): Main Agent response before execution

        - Input (IP) Types:
          1. "Request" → User instruction
             - Detect ambiguity (unclear, vague, short commands)
             - Detect invalid instructions (e.g., wrong assembly sequence)
             - Require clarification if necessary
          2. "Update" → Robot state feedback
             - Ensure OP properly reacts to updates
             - Validate correct task continuation or completion
          3. "Feedback" → Correction from validation loop
             - Do NOT re-validate
             - Always assign score = 10

        - Validate OP correctness:
          - Function is appropriate and relevant
          - Parameters are correct and complete
          - No unrelated function is executed
          - Assembly sequences follow valid order
          - Response satisfies the original request

        - Ensure safe human-robot interaction at all times

        Scoring Policy (K):
        - 0 → IP and OP invalid, requires user clarification
        - 1–5 → Major issues, provide corrective feedback
        - 6–9 → Minor issues (acceptable but imperfect)
        - 10 → Fully correct and aligned

        Input Format:
        {{
          "IP": {{
            "Type": "Request | Update | Feedback",
            "Data": "Input content"
          }},
          "OP": {{
            "Reply": "Main Agent reply",
            "Function": {{
              "Name": "function name or 0",
              "Params": {{
                "param_name": "value"
              }}
            }}
          }}
        }}

        Output Format:
        {{
          "Feedback_score": 0-10,
          "Feedback": "Provide guidance only if score ≤ 5, otherwise NULL",
          "State": "Updated system condition"
        }}

        All inputs and outputs MUST be valid JSON.
        """

        self.main_agent.define_prompt(main_prompt)
        self.validation_agent.define_prompt(validation_prompt)

    def _build_environment_description(self) -> str:
        """Build environment context description."""
        return """
The robot is positioned in front of the user. Between them is a workspace table with:
- Assembly components (wood, bolts, etc.)
- Tools (screwdriver, etc.)

Robot coordinate system:
- X-axis: toward user (positive toward user)
- Y-axis: left-right (positive to robot's right)
- Z-axis: vertical (positive upward)
- Units: millimeters (mm)

The robot has two arms (Left and Right) with grippers for object manipulation.
"""

    def _build_function_definitions(self) -> str:
        """Build function definitions for agents."""
        functions = {
            "Functions": [
                {
                    "Name": "Move",
                    "Description": "Increment movement on single axis",
                    "Params": {
                        "Arm": "Left or Right",
                        "Axis": "X, Y, or Z",
                        "Units": "Integer (±mm)"
                    }
                },
                {
                    "Name": "MoveTo",
                    "Description": "Absolute movement to coordinates or named position",
                    "Params": {
                        "Type": "Coordinate or Name",
                        "Arm": "Left or Right",
                        "X/Y/Z": "Coordinates or Define position name"
                    }
                },
                {
                    "Name": "Grip",
                    "Description": "Open (0) or close (1) gripper",
                    "Params": {
                        "Arm": "Left or Right",
                        "State": "0 or 1"
                    }
                },
                {
                    "Name": "Rotate",
                    "Description": "Rotate end-effector",
                    "Params": {
                        "Arm": "Left or Right",
                        "Position": "Forward, Down, or Side"
                    }
                },
                {
                    "Name": "Assembly",
                    "Description": "Execute assembly step (1-14)",
                    "Params": {"Step": "Integer 1-14"}
                },
                {
                    "Name": "Identify",
                    "Description": "Vision-based object identification",
                    "Params": {"Query": "Question about objects in view"}
                },
                {
                    "Name": "EndSession",
                    "Description": "Terminate the session safely",
                    "Params": {}
                }
            ]
        }

        return json.dumps(functions, indent=2)