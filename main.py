"""
CogniVera Main Module
====================

Main entry point for conversational human-robot collaboration system.
Orchestrates input, processing, and robot interaction loop.

Reference: https://doi.org/10.1109/ACCESS.2025.3565918
"""

import logging
import time
import sys
from typing import Optional

from controller import AgentController
from functionCaller import RobotFunctionCaller
from logger import ExperimentLogger
from voice import VoiceHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CogniVeraSession:
    """
    Main conversational session for human-robot collaboration.

    Manages complete interaction loop: input capture, LLM processing,
    function execution, and feedback collection.

    Attributes:
        use_voice (bool): Enable voice input/output
        use_keyboard (bool): Enable keyboard input
        use_test_file (bool): Read requests from test file
    """

    def __init__(
            self,
            use_voice: bool = True,
            use_keyboard: bool = False,
            use_test_file: bool = False,
            api_key: Optional[str] = None,
            robot_on: bool = True,
            enable_validation: bool = True
    ):
        """
        Initialize session.

        Args:
            use_voice (bool): Enable voice interface. Default: True
            use_keyboard (bool): Enable keyboard input. Default: False
            use_test_file (bool): Use test file for requests. Default: False
            api_key (str, optional): OpenAI API key
            robot_on (bool): Enable robot hardware. Default: True
            enable_validation (bool): Enable validation agent. Default: True
        """
        # Input modes
        self.use_voice = use_voice
        self.use_keyboard = use_keyboard
        self.use_test_file = use_test_file

        # Initialize components
        try:
            self.controller = AgentController(
                api_key=api_key,
                use_validation=enable_validation
            )
            logger.info("Controller initialized")
        except ValueError as e:
            logger.error(f"Failed to initialize controller: {str(e)}")
            raise

        try:
            self.robot = RobotFunctionCaller(
                robot_on=robot_on,
                api_key=api_key
            )
            logger.info("Robot function caller initialized")
        except Exception as e:
            logger.warning(f"Robot unavailable: {str(e)}")
            self.robot = None

        try:
            self.voice = VoiceHandler(api_key=api_key) if use_voice else None
            if self.voice:
                logger.info("Voice handler initialized")
        except ValueError as e:
            logger.warning(f"Voice unavailable: {str(e)}")
            self.voice = None
            self.use_voice = False

        self.logger = ExperimentLogger()

        # Session state
        self.state = "IDLE"
        self.session_start = time.time()

    def run(self) -> None:
        """Run main interaction loop."""
        logger.info("Starting CogniVera session...")

        try:
            while True:
                # Get user input
                user_input = self._get_input()

                if user_input is None or user_input.lower() == "exit":
                    logger.info("User exit requested")
                    break

                # Process through controller
                request_json = {
                    "IP": {"Type": "Request", "Data": user_input},
                    "State": self.state
                }

                user_id = self.logger.log_request("User", user_input, None)
                request_start = time.time()

                response_json, score = self.controller.process_request(request_json)
                request_end = time.time()

                # Log response
                self.logger.log_reply(
                    user_id,
                    str(response_json["OP"].get("Reply", "No reply")),
                    str(response_json["OP"].get("Function", {})),
                    request_end - request_start,
                    score
                )

                # Output response
                self._output_response(response_json["OP"].get("Reply", ""))

                # Execute function if requested
                if response_json["OP"]["Function"].get("Name") not in ["0", 0]:
                    self._execute_function(response_json)

                # Update state
                self.state = response_json.get("State", self.state)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Session error: {str(e)}", exc_info=True)
        finally:
            self._cleanup()

    def _get_input(self) -> Optional[str]:
        """Get input from configured source."""
        if self.use_voice and self.voice:
            return self.voice.speech_to_text()
        elif self.use_keyboard:
            try:
                return input("You: ").strip()
            except EOFError:
                return None
        elif self.use_test_file:
            return self._get_test_input()
        else:
            return input("You: ").strip()

    def _get_test_input(self) -> Optional[str]:
        """Read input from test file."""
        if not hasattr(self, 'test_file'):
            try:
                self.test_file = open("test_requests.txt", "r")
            except FileNotFoundError:
                logger.error("Test file not found: test_requests.txt")
                return None

        line = self.test_file.readline().strip()
        if line:
            print(f"[Test] {line}")
            return line
        else:
            self.test_file.close()
            return None

    def _output_response(self, response: str) -> None:
        """Output response using configured method."""
        if self.use_voice and self.voice:
            self.voice.text_to_speech(response)
        else:
            print(f"Robot: {response}")

    def _execute_function(self, response_json: dict) -> None:
        """Execute robot function."""
        if self.robot is None:
            logger.warning("Robot not available, skipping function execution")
            return

        function = response_json["OP"]["Function"]
        function_name = function.get("Name")
        params = function.get("Params", {})

        try:
            logger.info(f"Executing function: {function_name}")
            result = self.robot.execute_function({
                "Name": function_name,
                "Params": params
            })

            # Log function execution
            func_id = self.logger.log_request("Function", function_name, None)
            self.logger.log_reply(
                func_id,
                result.get("update", result.get("message", "Executed")),
                function_name,
                0.0,
                10.0 if result.get("status") == "success" else 0.0
            )

            logger.info(f"Function result: {result}")

        except Exception as e:
            logger.error(f"Function execution error: {str(e)}")

    def _cleanup(self) -> None:
        """Cleanup resources."""
        session_duration = time.time() - self.session_start
        logger.info(f"Session ended. Duration: {session_duration:.2f}s")

        if self.robot:
            self.robot.close()

        if self.voice:
            try:
                self.voice.recognizer.recognizer_instance.close()
            except:
                pass

        print("\nThank you for using CogniVera!")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CogniVera: Human-Robot Collaboration Framework"
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        default=True,
        help="Enable voice interface"
    )
    parser.add_argument(
        "--no-voice",
        action="store_false",
        dest="voice",
        help="Disable voice interface"
    )
    parser.add_argument(
        "--keyboard",
        action="store_true",
        help="Enable keyboard input"
    )
    parser.add_argument(
        "--test-file",
        action="store_true",
        help="Use test file for requests"
    )
    parser.add_argument(
        "--no-robot",
        action="store_true",
        help="Disable robot hardware"
    )
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Disable validation agent"
    )

    args = parser.parse_args()

    try:
        session = CogniVeraSession(
            use_voice=args.voice,
            use_keyboard=args.keyboard,
            use_test_file=args.test_file,
            robot_on=not args.no_robot,
            enable_validation=not args.no_validation
        )
        session.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()