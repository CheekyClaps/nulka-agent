<div align="center">
  <h1>🤖 OmniAgentCore</h1>
  <p><b>Enterprise Multi-Agent Simulated Workspace with local LLMs and an Interactive Self-Learning Feedback Loop</b></p>

  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![CrewAI](https://img.shields.io/badge/CrewAI-0.11.2-orange.svg)](https://crewai.com)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Local AI](https://img.shields.io/badge/Ollama-Native-purple.svg)](https://ollama.ai)
  
</div>

<br>

**OmniAgentCore** is an advanced, enterprise-grade multi-agent CLI designed to orchestrate highly specialized autonomous AI agents right on your terminal. It acts as an elite technical consulting firm right inside your project directory, leveraging local models (like `Qwen` via Ollama) to maintain ultimate privacy while featuring a configurable "Universal Oracle" (like `Gemini`, `ChatGPT`, or `Claude`) for when local models get stuck.

## ✨ Key Features

- **🌐 Dynamic Omni-Agent Roster:** Includes specialized roles out of the box: *Router, Planner, Architect, Developer, Tester, Pentester, Security Officer, and Network Engineer*.
- **🧠 Semantic Router:** Fast, intelligent intent classification using LLM-backed lexical-semantic routing to dynamically assemble the perfect Crew for your query.
- **🎓 Interactive Self-Learning Loop (`/teach`):** When a local agent hallucinates or makes a mistake, type `/teach`. The system will fetch the absolute truth from the External Oracle and *interactively rewrite* the failing agent's backstory, allowing the workspace to permanently learn from its mistakes!
- **🔮 Universal Oracle Fallback:** Agnostic CLI integrations. If a local model fails, OmniAgentCore falls back to your configured External Oracle CLI (Gemini, ChatGPT, Claude) to guarantee success.
- **🎨 Beautiful Terminal UI:** Built with `rich` and `prompt_toolkit`. Features real-time execution breadcrumbs, beautiful panels, silent workflows, and interactive slash commands (`/help`, `/models`, `/pull`).

## 🚀 Installation (Zero Script Required)

OmniAgentCore is a production-ready Python package. You can install it globally and launch the interactive setup wizard natively:

```bash
# Clone the repository
git clone https://github.com/cheekyclaps/omniagentcore.git
cd omniagentcore

# Install globally or in a virtual environment
pip install -e .

# Launch the interactive onboarding wizard
omniagentcore
```

On your very first boot, OmniAgentCore will scan your system for available AI CLI tools, ask you which one to use as your **Universal Oracle**, and save the configuration to `~/.omniagentcore_env`.

## 🎮 Usage

Simply type `omniagentcore` from anywhere in your terminal to boot into the workspace.

```text
✦ ❯ what model are you?
✨ Answer Completed!
Router ➔ General Assistant ➔ Teacher

╭────────────────────────────────────────────── Answer ──────────────────────────────────────────────╮
│ I am based on the Qwen model.                                                                      │
╰────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Slash Commands
- `/models`: View a stunning table of all locally cached and actively loaded Ollama models.
- `/pull <model>`: Pulls models directly from Ollama using native streaming progress bars.
- `/teach`: Triggers the **Interactive Feedback Loop** to manually fix the agent's last answer.
- `/debug`: Toggles verbose tracing, showing exactly what each AI Agent is thinking during execution.
- `/quit`: Power down the hub.

## 🏗 Architecture & Wiki

For deep technical insights into how the agent configuration works, how to customize backstories, or how the `/teach` feedback loop edits markdown dynamically, please check out the [Official Wiki](docs/Home.md).

## 🛡️ License

This project is licensed under the MIT License - see the LICENSE file for details.
