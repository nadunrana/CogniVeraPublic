# CogniVera: Human-Robot Collaboration Framework

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Paper: IEEE Access](https://img.shields.io/badge/Paper-IEEE%20Access-blue.svg)

**A dual-agent LLM framework for conversational human-robot collaboration with cognitive validation against context-induced hallucinations.**

> **Publication**: [Large Language Models in Human-Robot Collaboration with Cognitive Validation Against Context-induced Hallucinations](https://doi.org/10.1109/ACCESS.2025.3565918)  
> IEEE Access, 2025 | DOI: 10.1109/ACCESS.2025.3565918

---

## 🎯 Overview

CogniVera is an open-source Python framework enabling natural conversational interaction between humans and robots using Large Language Models (LLMs). The framework implements a **dual-agent architecture** where:

- **Main Agent**: Processes user requests and generates responses with function calls
- **Validation Agent**: Ensures accuracy, provides feedback, and corrects hallucinations

Features include:
- 🎤 Voice input/output via OpenAI Whisper & TTS
- 🤖 Dual-LLM validation system for hallucination prevention
- 🔧 Modular robot control (movement, gripper, vision, assembly)
- 📊 CSV-based experiment logging and tracking
- 🔌 TCP socket hardware integration
- 🛡️ Secure API key management via environment variables

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- (Optional) Robot hardware with TCP socket interface

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nadunrana/CogniVera.git
   cd CogniVera
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate          # Linux/Mac
   # or
   venv\Scripts\activate             # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   nano .env  # or use your favorite editor
   ```

5. **Run the system**
   ```bash
   python main.py
   ```

---

## 📖 Usage

### Voice Interface (Default)
```bash
python main.py
```
Listen for the greeting, then speak your request naturally.

### Keyboard Input
```bash
python main.py --no-voice --keyboard
```

### Simulation Mode (No Robot Hardware)
```bash
python main.py --no-robot
```

### Skip Validation Agent
```bash
python main.py --no-validation
```

### All Options
```bash
python main.py --help
```

---

## 🏗️ Architecture

### Module Structure

```
cognivera/
├── assistant.py          # LLM Agent (OpenAI GPT-4)
├── controller.py         # Dual-agent orchestration
├── functionCaller.py     # Robot action execution
├── logger.py             # Experiment tracking (CSV)
├── main.py               # Entry point & session manager
├── socketR.py            # TCP hardware communication
└── voice.py              # Speech recognition & synthesis
```

### Data Flow

```
User Input (Voice/Keyboard)
    ↓
Main Agent (GPTAgent)
    ├─ Process request
    ├─ Generate response
    └─ Call functions
    ↓
Validation Agent (optional)
    ├─ Quality check
    ├─ Provide feedback
    └─ Error correction
    ↓
Function Execution (if needed)
    ├─ RobotFunctionCaller
    ├─ TCPClient → Hardware
    └─ ExperimentLogger (CSV)
    ↓
Output (Voice/Text)
```

---

## 📚 Module Reference

### **assistant.py** - LLM Agent
Interfaces with OpenAI's GPT models for conversation and task generation.

```python
from assistant import GPTAgent

agent = GPTAgent()
response = agent.chat("Move the left arm forward")
agent.define_prompt("You are a helpful robot...")
```

**Key Methods**:
- `chat(query)` - Send query and receive response
- `define_prompt(prompt)` - Set system prompt
- `clear_history()` - Reset conversation

---

### **controller.py** - Dual-Agent Orchestrator
Manages Main Agent and Validation Agent with feedback loops.

```python
from controller import AgentController

controller = AgentController(use_validation=True)
response_json, score = controller.process_request(request_json)
```

**Key Methods**:
- `process_request(request_json)` - Main processing pipeline
- Returns: `(response_dict, validation_score)`

---

### **functionCaller.py** - Robot Control
Executes robot functions: movement, gripping, rotation, assembly, vision.

```python
from functionCaller import RobotFunctionCaller

robot = RobotFunctionCaller(robot_on=True)
result = robot.execute_function({
    "Name": "Move",
    "Params": {"Arm": "Left", "Axis": "X", "Units": 50}
})
```

**Supported Functions**:
- **Move** - Incremental movement (X/Y/Z axes)
- **MoveTo** - Absolute position or named preset
- **Grip** - Open/close gripper
- **Rotate** - Change end-effector orientation
- **Assembly** - Multi-step assembly sequences
- **Identify** - Vision-based object identification

---

### **logger.py** - Experiment Tracking
CSV-based logging for requests, responses, and validation scores.

```python
from logger import ExperimentLogger

logger = ExperimentLogger()
req_id = logger.log_request("User", "move forward", None)
logger.log_reply(req_id, "moving forward", "Move", 1.5, 10.0)
# Output: logs/experiment_log.csv
```

**CSV Columns**:
- Request_ID, Timestamp, Request_Type
- Request, Reply, Score
- Function_Call, Time_Taken_Seconds

---

### **voice.py** - Voice I/O
Speech recognition (Whisper) and text-to-speech synthesis.

```python
from voice import VoiceHandler

voice = VoiceHandler()
text = voice.speech_to_text()        # Listen & transcribe
voice.text_to_speech("Hello world!")  # Speak
```

**Key Methods**:
- `speech_to_text()` - Capture microphone and transcribe
- `text_to_speech(text, voice)` - Synthesize and play audio

---

### **socketR.py** - Hardware Communication
TCP socket client for robot controller communication.

```python
from socketR import TCPClient

client = TCPClient(host="192.168.125.1", port=5000)
response = client.send_message("command_string")
client.close()

# Or use as context manager:
with TCPClient() as client:
    response = client.send_message("command")
```

---

## 🔐 Security

### API Key Management

**✅ Recommended**: Use environment variables
```bash
export OPENAI_API_KEY="sk-..."
```

**✅ Recommended**: Use `.env` file
```bash
cp .env.example .env
# Edit .env with your API key
```

**❌ Never**: Hardcode secrets in source code

### Secrets Excluded from Git
- `.env` (local configuration)
- `code.txt` (old key file)
- `logs/` (experiment data)

---

## 🧪 Testing

### Manual Module Testing
```bash
python -c "from assistant import GPTAgent; print('✓ Assistant OK')"
python -c "from voice import VoiceHandler; print('✓ Voice OK')"
python -c "from logger import ExperimentLogger; print('✓ Logger OK')"
```

### Integration Test
```bash
echo "move left arm by 10 units" > test_requests.txt
python main.py --test-file --no-voice --no-robot
```

### Unit Tests (with pytest)
```bash
pytest tests/
pytest tests/ -v --cov=src/
```

---

## 🐛 Troubleshooting

### Issue: "OPENAI_API_KEY not set"
```bash
# Set environment variable
export OPENAI_API_KEY=sk-...

# Or use .env file
cp .env.example .env
# Edit .env with your key
```

### Issue: "Cannot connect to robot"
```bash
# Use simulation mode
python main.py --no-robot

# Check robot IP/port settings
# Default: 192.168.125.1:5000
```

### Issue: "Microphone not found"
```bash
# List audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"

# Use keyboard input instead
python main.py --no-voice --keyboard
```

### Issue: "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

---

## 📁 Project Structure

```
cognivera/
├── assistant.py                  # GPT Agent interface
├── controller.py                 # Dual-agent orchestration
├── functionCaller.py             # Robot function execution
├── logger.py                     # Experiment logging
├── main.py                       # Entry point
├── socketR.py                    # Hardware TCP client
├── voice.py                      # Voice I/O
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git exclusions
└── LICENSE                       # MIT License
```

---

## 🚀 Advanced Usage

### Programmatic API
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

### Custom Robot Configuration
```python
from functionCaller import RobotFunctionCaller

robot = RobotFunctionCaller(
    robot_on=True,
    host="192.168.125.1",
    port=5000,
    api_key="sk-..."
)
```

### Custom Prompts
```python
from controller import AgentController

controller = AgentController()
controller.main_agent.define_prompt("Your custom system prompt...")
controller.validation_agent.define_prompt("Your validation prompt...")
```

---

## 📄 Citation

If you use CogniVera in your research, please cite our paper:

```bibtex
@article{ranasinghe_large_2025,
	title = {Large {Language} {Models} in {Human}-{Robot} {Collaboration} {With} {Cognitive} {Validation} {Against} {Context}-{Induced} {Hallucinations}},
	url = {https://ieeexplore.ieee.org/abstract/document/10980279},
	doi = {10.1109/ACCESS.2025.3565918},
	journal = {IEEE Access},
	author = {Ranasinghe, Nadun and Mohammed, Wael M. and Stefanidis, Kostas and Martinez Lastra, Jose L.},
	year = {2025},
}
```

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run linting
flake8 . --count --select=E9,F63,F7,F82

# Run tests
pytest tests/

# Type checking
mypy .
```

---

## 📞 Support

For issues, questions, or suggestions:
- Open an [Issue](https://github.com/nadunrana/CogniVera/issues)
- Check [Troubleshooting](./README.md#-troubleshooting) section
- Review [GIT_FIXES.md](GIT_FIXES.md) for common errors

---

## 🙏 Acknowledgments

- **OpenAI** - GPT-4 and Whisper API
- **IEEE Access** - Publication venue
- **FAST-LAB** & **Thammasat University** - Research institution

---

## 📌 Key Features

✅ **Dual-Agent Architecture** - Main Agent + Validation Agent for hallucination prevention  
✅ **Voice Interface** - Natural language interaction via Whisper & TTS  
✅ **Modular Design** - Easy to extend with custom functions  
✅ **Hardware Integration** - TCP socket communication with robot controllers  
✅ **Experiment Logging** - Automatic CSV tracking of interactions  
✅ **Production-Ready** - Professional code quality, comprehensive documentation  
✅ **Academic Research** - Published framework for human-robot collaboration  

---

**Built with ❤️ for human-robot collaboration** 🤖👥

Last Updated: December 2025  
Repository: [github.com/nadunrana/CogniVera](https://github.com/nadunrana/CogniVera)
