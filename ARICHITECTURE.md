# File Structure & Architecture

## Module Overview

### assistant.py
- **Class**: `GPTAgent`
- **Purpose**: Interface with OpenAI LLM API
- **Key Methods**:
  - `chat(query)` - Send query and receive response
  - `define_prompt(prompt)` - Set system prompt
  - `clear_history()` - Reset conversation
- **Dependencies**: openai

### controller.py
- **Class**: `AgentController`
- **Purpose**: Orchestrate dual-agent system
- **Key Methods**:
  - `process_request(request_json)` - Main entry for requests
  - `_validate_response()` - Quality assurance check
  - `_provide_feedback_correction()` - Error correction loop
- **Dependencies**: assistant, logger

### functionCaller.py
- **Class**: `RobotFunctionCaller`
- **Purpose**: Execute robot functions and hardware control
- **Key Methods**:
  - `execute_function(function_data)` - Execute any robot function
  - `_execute_move()` - Incremental movement
  - `_execute_grip()` - Gripper control
  - `_execute_assembly()` - Multi-step assembly
  - `_execute_identify()` - Vision-based identification
- **Dependencies**: socketR, cv2, requests

### logger.py
- **Class**: `ExperimentLogger`
- **Purpose**: CSV-based experiment tracking
- **Key Methods**:
  - `log_request(type, request, score)` - Start new log entry
  - `log_reply(id, reply, function, time, score)` - Complete log entry
- **Output**: `logs/experiment_log.csv`

### socketR.py
- **Class**: `TCPClient`
- **Purpose**: Low-level hardware communication
- **Key Methods**:
  - `send_message(message)` - Send command and receive response
  - `is_connected()` - Check connection status
- **Dependencies**: socket, logging

### voice.py
- **Class**: `VoiceHandler`
- **Purpose**: Speech recognition and synthesis
- **Key Methods**:
  - `speech_to_text()` - Capture and transcribe audio
  - `text_to_speech(text)` - Synthesize and play audio
- **Dependencies**: openai, speech_recognition, soundfile, sounddevice

### main.py
- **Class**: `CogniVeraSession`
- **Purpose**: Main interaction loop
- **Key Methods**:
  - `run()` - Main event loop
  - `_get_input()` - Capture user input
  - `_execute_function()` - Execute robot actions
  - `_output_response()` - Return responses to user
- **Dependencies**: All modules
- **Entry Point**: `if __name__ == "__main__": main()`

## Data Flow

```
User Input (Voice/Keyboard)
        ↓
VoiceHandler or input()
        ↓
Main Loop (CogniVeraSession.run)
        ↓
Request JSON → AgentController
        ↓
Main Agent (GPTAgent) → Response JSON
        ↓
Validation Agent (optional) ← Feedback Loop
        ↓
ExperimentLogger (CSV)
        ↓
Function Name != "0"?
    ├─ Yes → RobotFunctionCaller
    │         ↓
    │     TCPClient → Hardware
    │         ↓
    │     Response → Logger
    │
    └─ No → Output Reply
        ↓
    VoiceHandler.text_to_speech or print()
```

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=sk-...  # Required: OpenAI API key
```

### Robot Hardware (socketR.py)
```python
DEFAULT_HOST = "192.168.125.1"  # Robot IP
DEFAULT_PORT = 5000             # Robot port
```

### Voice Settings (voice.py)
```python
dev_mode = False           # Skip greeting
greeting_active = True     # Show greeting
pause_threshold = 1.0      # Silence timeout (seconds)
```

### Logging (logger.py)
```python
file_name = "logs/experiment_log.csv"  # Log file path
```

## Usage Examples

### Basic Usage (Voice Interface)
```bash
python main.py
```

### Keyboard Only
```bash
python main.py --no-voice --keyboard
```

### Simulation (No Robot Hardware)
```bash
python main.py --no-robot
```

### With Test File
```bash
python main.py --test-file
```

### Programmatic Usage
```python
from main import CogniVeraSession

session = CogniVeraSession(
    use_voice=True,
    use_keyboard=False,
    robot_on=True,
    enable_validation=True
)
session.run()
```

## Error Handling

All modules include comprehensive logging:

```python
import logging
logger = logging.getLogger(__name__)

# Errors logged automatically
logger.error("Error message")
logger.warning("Warning message")
logger.info("Info message")
logger.debug("Debug message")
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `OPENAI_API_KEY not set` | Set environment variable or pass to init |
| `Cannot connect to robot` | Check IP/port, robot power, network |
| `Microphone not found` | Check audio device, permissions |
| `Vision identification fails` | Ensure frame.jpg exists, check API key |

## Testing

### Unit Tests
```bash
pytest tests/
```

### Manual Testing
```python
# Test LLM Agent
from assistant import GPTAgent
agent = GPTAgent()
response = agent.chat("Hello!")

# Test Voice
from voice import VoiceHandler
voice = VoiceHandler()
text = voice.speech_to_text()
voice.text_to_speech("Testing TTS")

# Test Logger
from logger import ExperimentLogger
log = ExperimentLogger()
req_id = log.log_request("User", "test request", None)
log.log_reply(req_id, "test reply", None, 1.5, 10.0)
```

## Performance Metrics

- **LLM Response Time**: ~2-5 seconds (GPT-4)
- **Speech Recognition**: ~1-3 seconds
- **TTS Synthesis**: ~1-2 seconds
- **Hardware Communication**: ~50-200ms
- **Validation Loop**: +1-3 seconds if enabled

## Paper Reference

For the original research and methodology, see:
**Large Language Models in Human-Robot Collaboration with Cognitive Validation Against Context-induced Hallucinations**
- DOI: 10.1109/ACCESS.2025.3565918
- IEEE Access, 2025

## License

MIT License - See LICENSE file for details
