# OpenCode CrewAI Enterprise Hub

This repository contains an advanced, enterprise-grade multi-agent simulated workspace built using the **CrewAI** framework and local **Ollama** LLMs. The workspace mimics a software/security company with specialized functional departments, equipped with a dynamic environmental context engine and a streamlined interactive command-line interface resembling OpenCode/OpenHands.

---

## 📂 Project Directory Structure
```text
crewai-setup/
├── cli.py                  # Beautiful interactive console UI (rich & prompt_toolkit)
├── main.py                 # Startup script / Entry point
├── utils.py                # Environment context engine & dynamic yaml/markdown loader
├── run_main.sh             # Activates virtual env and boots the application
├── config/
│   ├── agents.yaml         # High-level agent meta configurations (role, goal)
│   └── agents/             # Markdown files containing advanced 2026 backstories
│       ├── router.md       # Classifies and delegates requests (Lexical-Semantic routing)
│       ├── planner.md      # Scrum Product Management (PM)
│       ├── systems_engineer.md # Structural systems specs
│       ├── developer.md    # Code implementation & docstrings
│       ├── tester.md       # TDD test harness & validation suites
│       ├── pentester.md    # Offensive vulnerability exploits (ethical hacking)
│       ├── security_officer.md # Defensive code review & secure coding standards
│       └── network_engineer.md # Docker, DNS, ports, firewalls, and proxy topologies
├── tools/
│   └── gemini_cli_tool.py  # Custom BaseTool wrapping local gemini-cli commands
└── docs/                   # Planning and Research documentation
    ├── architecture-plan.md  # Detailed implementation steps
    └── frameworks-research.md # Comparative analysis of Multi-Agent Frameworks
```

---

## 🚀 How to Run the App

1. Ensure Ollama is installed on your system.
2. Launch the application:
   ```bash
   ./run_main.sh
   ```
   *The program will automatically check if the Ollama server is running and start the background daemon natively if it is offline.*

---

## 🎛️ Special Slash Commands

While inside the interactive shell, you can type special commands:
* **`/models`**: Queries Ollama's local cache and memory, showing a beautiful table of installed models and highlighting which ones are currently loaded in RAM (`ACTIVE`).
* **`/pull <model_name>`**: Pulls a new model from the official Ollama library, displaying the native streaming progress bars directly in your terminal.
* **`/help`**: Renders a styled help menu showing all available controls.
* **`/quit`**: Shuts down the console.

---

## 🧩 Architectural Conventions

### YAML + Markdown Split
To keep prompt-engineering decoupled from logic:
1. Agent **Role** and **Goal** properties are declared inside `config/agents.yaml`.
2. Agent **Backstories** and **Rules of Engagement** are stored inside their respective Markdown files in `config/agents/*.md`.
3. The loader (`utils.py`) dynamically reads both, performing environmental context interpolation at runtime.

### Dynamic Context Interpolation
During startup, the system gathers real-time host metrics:
* `{system_os}`: Operating system (e.g., Linux).
* `{system_platform}`: Release/version parameters.
* `{current_time}`: Precise local datetime.
* `{geolocation}`: Local timezone mapping (e.g., Europe/Berlin).

These parameters are dynamically injected into placeholders within the backstory `.md` files, giving the agents real-time situational awareness (such as timezone deadlines and operating-system-specific commands).
