"""
CogniVera Main Module (ENV-enabled)
===================================


Main entry point for conversational human-robot collaboration system.
Now fully uses .env configuration for flexible deployment.
"""

import logging
import time
import sys
import os
from typing import Optional
from controller import AgentController
from functionCaller import RobotFunctionCaller
from logger import ExperimentLogger
from voice import VoiceHandler
from dotenv import load_dotenv
# ✅ Load .env
load_dotenv()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CogniVeraSession:
    def __init__(
            self,
            use_voice: Optional[bool] = None,
            use_keyboard: Optional[bool] = None,
            use_test_file: Optional[bool] = None,
            api_key: Optional[str] = None,
            robot_on: Optional[bool] = None,
            enable_validation: Optional[bool] = None
    ):
        # ✅ Load config from ENV if not passed
        self.use_voice = use_voice if use_voice is not None else os.getenv("USE_VOICE", "true").lower() == "true"
        self.use_keyboard = use_keyboard if use_keyboard is not None else os.getenv("USE_KEYBOARD", "true").lower() == "true"
        self.use_test_file = use_test_file if use_test_file is not None else os.getenv("USE_TEST_FILE", "false").lower() == "true"
        robot_on = robot_on if robot_on is not None else os.getenv("ROBOT_ON", "true").lower() == "true"
        enable_validation = enable_validation if enable_validation is not None else os.getenv("ENABLE_VALIDATION", "true").lower() == "true"
        # ✅ API key from ENV fallback
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        # ✅ Init Controller
        self.controller = AgentController(
            api_key=api_key,
            use_validation=enable_validation
        )
        logger.info("Controller initialized")
        # ✅ Init Robot
        try:
            self.robot = RobotFunctionCaller(
                robot_on=robot_on,
                api_key=api_key
            )
            logger.info("Robot function caller initialized")
        except Exception as e:
            logger.warning(f"Robot unavailable: {e}")
            self.robot = None
        # ✅ Init Voice
        try:
            self.voice = VoiceHandler(api_key=api_key) if self.use_voice else None
            if self.voice:
                logger.info("Voice handler initialized")
        except Exception as e:
            logger.warning(f"Voice unavailable: {e}")
            self.voice = None
            self.use_voice = False
        self.logger = ExperimentLogger()
        self.state = "IDLE"
        self.session_start = time.time()
    def run(self):
        logger.info("Starting CogniVera session...")
        try:
            while True:
                user_input = self._get_input()
                if user_input is None or user_input.lower() == "exit":
                    break
                request_json = {
                    "IP": {"Type": "Request", "Data": user_input},
                    "State": self.state
                }
                user_id = self.logger.log_request("User", user_input, None)
                start = time.time()
                response_json, score = self.controller.process_request(request_json)
                end = time.time()
                self.logger.log_reply(
                    user_id,
                    str(response_json["OP"].get("Reply", "")),
                    str(response_json["OP"].get("Function", {})),
                    end - start,
                    score
                )
                self._output_response(response_json["OP"].get("Reply", ""))
                func = response_json.get("OP", {}).get("Function")
                if isinstance(func, list):
                    func = func[0] if func else {}
                func_name = func.get("Name") if isinstance(func, dict) else None
                if func_name == "EndSession":
                    logger.info("EndSession function triggered")
                    self._output_response("Ending session. Goodbye!")
                    break
                elif func_name not in ["0", 0]:
                    self._execute_function(response_json)
                self.state = response_json.get("State", self.state)
        finally:
            self._cleanup()
    def _get_input(self):
        if self.use_voice and self.voice:
            return self.voice.speech_to_text()
        elif self.use_keyboard:
            return input("You: ").strip()
        elif self.use_test_file:
            return self._get_test_input()
        else:
            return input("You: ").strip()
    def _get_test_input(self):
        if not hasattr(self, 'test_file'):
            self.test_file = open("test_requests.txt", "r")
        line = self.test_file.readline().strip()
        return line if line else None
    def _output_response(self, response):
        if self.use_voice and self.voice:
            self.voice.text_to_speech(response)
        else:
            print(f"Robot: {response}")
    def _execute_function(self, response_json):
        if not self.robot:
            return
        func = response_json["OP"]["Function"]
        result = self.robot.execute_function(func)
        self.logger.log_reply(
            self.logger.log_request("Function", func.get("Name"), None),
            result.get("update", ""),
            func.get("Name"),
            0.0,
            10.0 if result.get("status") == "success" else 0.0
        )
    def _cleanup(self):
        if self.robot:
            self.robot.close()
        print("Session ended.")

def main():
    session = CogniVeraSession()
    session.run()

if __name__ == "__main__":
    main()

# ✅ Example .env file:
"""
# =============================
# CogniVera Configuration
# =============================
# 🔑 API
OPENAI_API_KEY=your_openai_key_here

# 🎤 Input Modes
USE_VOICE=true
USE_KEYBOARD=true
USE_TEST_FILE=false

# 🤖 Robot
ROBOT_ON=true

# ✅ Validation
ENABLE_VALIDATION=true

# ⚙️ Optional Debug/Extensions
DEV_MODE=false
EXPERIMENT_MODE=false

# 🧠 Speech Settings
TTS_ENGINE=openai      # or coqui
STT_ENGINE=whisper     # or vosk

# 🌐 Robot Connection
ROBOT_HOST=192.168.125.1
ROBOT_PORT=5000
"""