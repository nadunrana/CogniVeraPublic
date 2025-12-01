# CogniVera Publication Ready - Complete Guide

## 🎯 Overview

Your **CogniVera** framework has been completely refactored and is **ready for GitHub publication**. All code follows professional Python standards and best practices.

**Reference Paper**: [Large Language Models in Human-Robot Collaboration with Cognitive Validation Against Context-induced Hallucinations](https://doi.org/10.1109/ACCESS.2025.3565918) - IEEE Access, 2025

---

## 📦 What You Have

### Core Modules (7 files)
1. **assistant.py** - OpenAI LLM integration
2. **controller.py** - Dual-agent orchestration (Main + Validation)
3. **functionCaller.py** - Robot action execution
4. **logger.py** - CSV experiment logging
5. **main.py** - Main entry point and session management
6. **socketR.py** - TCP hardware communication
7. **voice.py** - Speech recognition & synthesis

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
python --version  # 3.8+
pip --version
```

### 2. Setup
```bash
# Clone repository
git clone https://github.com/yourusername/cognivera.git
cd cognivera

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure
```bash
# Create .env from template
cp .env.example .env

# Edit .env with your OpenAI API key
nano .env  # or: code .env (VS Code)
```

### 4. Run
```bash
# Default: voice interface
python main.py

# Or with options
python main.py --no-voice --keyboard      # Keyboard input
python main.py --no-robot                 # Simulation mode
python main.py --help                     # All options
```

---

## 📋 File Structure

```
cognivera/
├── src/                              # Source code (optional subdirectory)
│   ├── assistant.py                  # ✨ LLM Agent
│   ├── controller.py                 # ✨ Dual-agent system
│   ├── functionCaller.py             # ✨ Robot control
│   ├── logger.py                     # ✨ Logging
│   ├── main.py                       # ✨ Entry point
│   ├── socketR.py                    # ✨ Hardware comm
│   └── voice.py                      # ✨ Voice I/O
│
├── logs/                             # Auto-generated logs
│   └── experiment_log.csv            # CSV output
│
├── tests/                            # Test files (ready for pytest)
├── config/                           # Config files (optional)
│
├── .env.example                      # 📄 Environment template
├── .gitignore                        # 📄 Git exclusions
├── README.md                         # 📄 Project overview
├── ARCHITECTURE.md                   # 📄 Technical details
├── CLEANUP_SUMMARY.md                # 📄 What was improved
├── requirements.txt                  # 📄 Dependencies
├── LICENSE                           # 📄 MIT License
└── GETTING_STARTED.md               # 📄 This file
```

---

## 🔧 Module Quick Reference

### assistant.py
```python
from assistant import GPTAgent

agent = GPTAgent()
response = agent.chat("Hello!")
agent.define_prompt("You are a helpful robot...")
```

**Key Methods**:
- `chat(query)` - Send query, get response
- `define_prompt(prompt)` - Set system prompt
- `clear_history()` - Reset conversation

---

### controller.py
```python
from controller import AgentController

controller = AgentController(use_validation=True)
response_json, score = controller.process_request(request_json)
```

**Key Methods**:
- `process_request(request_json)` - Main processing
- Returns: `(response_dict, validation_score)`

---

### functionCaller.py
```python
from functionCaller import RobotFunctionCaller

robot = RobotFunctionCaller(robot_on=True)
result = robot.execute_function({"Name": "Move", "Params": {...}})
```

**Supported Functions**:
- Move (incremental)
- MoveTo (absolute)
- Grip (open/close)
- Rotate (orientation)
- Assembly (steps)
- Identify (vision)

---

### logger.py
```python
from logger import ExperimentLogger

logger = ExperimentLogger()
req_id = logger.log_request("User", "request text", None)
logger.log_reply(req_id, "reply", "function", 2.5, 10.0)
# Outputs: logs/experiment_log.csv
```

**CSV Columns**:
- Request_ID, Timestamp, Request_Type
- Request, Reply, Score
- Function_Call, Time_Taken_Seconds

---

### voice.py
```python
from voice import VoiceHandler

voice = VoiceHandler()
text = voice.speech_to_text()              # Listen & transcribe
voice.text_to_speech("Hello world!")       # Speak
```

**Key Methods**:
- `speech_to_text()` - Whisper transcription
- `text_to_speech(text, voice)` - TTS synthesis

---

### socketR.py
```python
from socketR import TCPClient

client = TCPClient(host="192.168.125.1", port=5000)
response = client.send_message("command string")
client.close()

# Or use as context manager:
with TCPClient() as client:
    response = client.send_message("command")
```

---

### main.py
```bash
python main.py                    # Voice input
python main.py --keyboard         # Keyboard
python main.py --no-robot         # Simulation
python main.py --no-validation    # Skip validation agent
```

---

## 🔐 Security & Environment

### API Key Management
**❌ WRONG:**
```python
api_key = "sk-..."  # Hardcoded!
```

**✅ CORRECT:**
```python
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### Setup .env
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# Load in your code (optional - handled automatically)
from dotenv import load_dotenv
load_dotenv()
```

### Never commit secrets!
`.gitignore` already excludes:
- `.env` (local only)
- `code.txt` (old key file)
- `logs/` (experiment logs)

---

## 📊 Data Flow

```
┌─────────────────────────────────────────┐
│         User Input                      │
│  (Voice/Keyboard/Test File)             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      Main Loop (CogniVeraSession)       │
│         main.py                         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     AgentController                     │
│  controller.py                          │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Main Agent (GPTAgent)            │  │
│  │ - Process request                │  │
│  │ - Generate response              │  │
│  │ - Call functions                 │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Validation Agent (optional)      │  │
│  │ - Quality check                  │  │
│  │ - Provide feedback               │  │
│  │ - Error correction loop          │  │
│  └──────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴─────┐
        │             │
        ▼             ▼
   No Function    Execute Function
        │             │
        ▼             ▼
   Output Reply  RobotFunctionCaller
   (Voice/Print)     │
                     ▼
                  TCPClient
                  (Hardware)
                     │
                     ▼
                  ExperimentLogger
                  (CSV)
```

---

## 🧪 Testing

### Manual Testing
```python
# Test individual modules
python -c "from assistant import GPTAgent; print('Assistant OK')"
python -c "from voice import VoiceHandler; print('Voice OK')"
python -c "from logger import ExperimentLogger; print('Logger OK')"
```

### Integration Testing
```bash
# Run with test file
echo "move left arm by 10 units" > test_requests.txt
python main.py --test-file --no-voice --no-robot
```

### Unit Tests (Future)
```bash
pytest tests/
pytest tests/ -v                    # Verbose
pytest tests/ --cov=src/           # Coverage
```

---

## 📈 Performance Tips

| Task | Typical Time |
|------|--------------|
| LLM Response | 2-5s |
| Speech Recognition | 1-3s |
| TTS Synthesis | 1-2s |
| Hardware Command | 50-200ms |
| Validation Loop | +1-3s |
| **Total Cycle** | **~5-15s** |

---

## 🐛 Troubleshooting

### Issue: "OPENAI_API_KEY not set"
```bash
# Solution: Set environment variable
export OPENAI_API_KEY=sk-...

# Or use .env file
cp .env.example .env
# Edit .env with your key
```

### Issue: "Cannot connect to robot"
```python
# Use simulation mode
python main.py --no-robot
```

### Issue: "Microphone not found"
```bash
# Check audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"

# Use keyboard input instead
python main.py --no-voice --keyboard
```

### Issue: "ImportError: No module named..."
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📚 Documentation Map

| Document | Purpose |
|----------|---------|
| **README.md** | Project overview, setup, features |
| **ARCHITECTURE.md** | Module details, data flow, config |
| **CLEANUP_SUMMARY.md** | What was improved, changes made |
| **GETTING_STARTED.md** | This file - quick reference |
| **requirements.txt** | Python dependencies |

---

## 🌟 Key Improvements Made

### Code Quality ✅
- ✓ PEP 8 compliant
- ✓ Type hints throughout
- ✓ Comprehensive docstrings
- ✓ Logging instead of print()
- ✓ Error handling

### Architecture ✅
- ✓ Modular design
- ✓ Separation of concerns
- ✓ Clear data flow
- ✓ Extensible framework

### Security ✅
- ✓ No hardcoded secrets
- ✓ Environment variable based
- ✓ .gitignore configured

### Documentation ✅
- ✓ README.md
- ✓ ARCHITECTURE.md
- ✓ Module docstrings
- ✓ Usage examples

---

## 🚀 Next Steps for Publication

### GitHub Setup
```bash
# Create GitHub repo
# Initialize local repo
git init
git add .
git commit -m "Initial commit: CogniVera framework"
git remote add origin https://github.com/yourusername/cognivera.git
git push -u origin main
```

### README Badges
```markdown
# CogniVera

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Paper](https://img.shields.io/badge/Paper-IEEE%20Access-blue)](https://doi.org/10.1109/ACCESS.2025.3565918)
```

### Additional Recommended Files
- `CONTRIBUTING.md` - How to contribute
- `CHANGELOG.md` - Version history
- `setup.py` - For PyPI distribution
- `.github/workflows/` - CI/CD pipeline

---

## 📞 Support & Citation

### Reference Your Paper
```bibtex
@article{cognivera2025,
  title={Large Language Models in Human-Robot Collaboration with Cognitive Validation Against Context-induced Hallucinations},
  author={Banerjee, P.},
  journal={IEEE Access},
  year={2025},
  doi={10.1109/ACCESS.2025.3565918}
}
```

### In README.md
```markdown
## Citation

If you use CogniVera in your research, please cite:

```bibtex
@article{cognivera2025,
  ...
}
```

### License
MIT License - See LICENSE file

---

## ✨ Summary

Your CogniVera framework is now:

✅ **Production-Ready** - Professional code quality
✅ **Well-Documented** - Comprehensive documentation
✅ **GitHub-Ready** - Complete project structure
✅ **Secure** - Proper secret management
✅ **Extensible** - Modular, reusable design
✅ **Publication-Ready** - Ready for academic/industry use

**Happy coding! 🎉**
