# CogniVera: Human-Robot Collaboration Framework

CogniVera is an open-source Python framework for conversational human-robot collaboration based on dual Large Language Models (LLM) agents (see the official publication: [IEEE Access, DOI:10.1109/ACCESS.2025.3565918](https://doi.org/10.1109/ACCESS.2025.3565918)).

**Key Features**
- Vocal interaction and speech recognition via OpenAI and local voice agents
- Dual LLM agent design: Main Agent (task execution), Validation Agent (feedback and correction)
- Modular controller for supporting robot operations (assembly, movement, gripping, etc.)
- Logging and experiment tracking
- Hardware integration with socket-based communication

## Repository Structure

```
.
├── assistant.py         # LLM Agent logic (OpenAI)
├── controller.py        # Dual-agent system orchestrator
├── functionCaller.py    # Robot function handler, integrates vision/audio
├── logger.py            # Experiment logger
├── main.py              # Main conversational loop and entry point
├── voice.py             # Voice audio/speech handler
├── socketR.py           # TCP socket client for hardware
├── requirements.txt     # Python dependencies
├── README.md            # This documentation
```

## Getting Started

1. Clone this repository:
    ```bash
    git clone https://github.com/yourusername/cognivera.git
    cd cognivera
    ```

2. Install dependencies (see requirements.txt below!):
    ```bash
    pip install -r requirements.txt
    ```

3. Set your OpenAI API key (see project file for usage):
    - Recommended: Create a `.env` file and add:  
      `OPENAI_API_KEY=<your_openai_key>`  
    - Or add to your shell environment.

4. Run the main app:
    ```bash
    python main.py
    ```

---

## Module Overview

### assistant.py
Implements the `GPTAgent` class for OpenAI LLM interactions, including prompts and chat methods.

### controller.py
Core logic for the dual-agent approach, request/response orchestration, and experiment configuration.

### functionCaller.py
Handles robot action execution, including vision and movement, via OpenAI and socketR. Supports assembly, move, grip, rotate, identify functions.

### logger.py
Tracks requests and responses, logs scores and function calls for research experiments.

### main.py
Entry point for the framework; manages conversation state and user/robot dialogue loop.

### voice.py
Handles speech recognition (using speechrecognition, sounddevice, OpenAI whisper) and vocal output.

### socketR.py
Basic TCP client for hardware robot communication.

---

## Publication Reference

If using CogniVera in your work, please cite:
> Banerjee, P., "Large Language Models in Human-Robot Collaboration with Cognitive Validation Against Context-induced Hallucinations", IEEE Access, 2025. DOI:10.1109/ACCESS.2025.3565918

---

## License
Distributed under the MIT License. See `LICENSE` for more information.
