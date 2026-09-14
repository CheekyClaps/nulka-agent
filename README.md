<div align="center">
  <h1>NulkaAgent</h1>
  <p><b>Enterprise Multi-Agent Simulated Workspace with Local LLMs and Interactive Self-Learning</b></p>
</div>

<br>

NulkaAgent is an advanced, enterprise-grade multi-agent Command Line Interface (CLI) designed to orchestrate specialized autonomous AI agents directly within your terminal. Operating as an embedded technical consulting firm, NulkaAgent leverages local models (via Ollama) to maintain absolute data privacy, while natively supporting a configurable "Universal Oracle" (such as Gemini, ChatGPT, or Claude) for seamless fallback when local models encounter complex constraints.

## Core Capabilities

- **Dynamic Nulka-Agent Roster:** Deploys a pre-configured corporate structure featuring highly specialized roles: Router, Planner, Architect, Developer, Tester, Pentester, Security Officer, and Network Engineer.
- **Semantic Routing:** Features an intelligent intent classification engine that evaluates user prompts and dynamically assembles the optimal Crew of agents for the specific task.
- **Zero-Trust Hallucination Risk Factor (HRF):** Evaluates prompts against spatial, temporal, and web-based constraints. High-risk prompts automatically bypass local execution and route directly to the Universal Oracle.
- **Interactive Self-Learning Loop:** When an agent produces an incorrect or hallucinatory response, the user can invoke the feedback loop to query the Universal Oracle for the absolute truth. This truth is then permanently embedded into the local agent's behavior rules.
- **Workspace Initialization:** Supports state persistence. Users can initialize directories as managed workspaces to preserve interaction history and agent memory across sessions.
- **Terminal UI:** Built on top of robust terminal libraries to provide real-time execution breadcrumbs, status panels, native paging, and interactive command handling.

---

## Installation

NulkaAgent is packaged as a standard Python module and requires Python 3.10 or higher. 

### Prerequisites

1. **Python 3.10+**: Ensure Python and `pip` are installed on your system.
2. **Ollama**: NulkaAgent relies on Ollama for local LLM inference.
   - Install Ollama from [ollama.com](https://ollama.com).
   - Ensure the Ollama background daemon is running before booting the CLI.
3. **External CLI Tools (Optional but Recommended)**: For the Universal Oracle to function, you must have an external AI CLI tool installed globally on your system (e.g., `gemini-cli`, a ChatGPT CLI, or a Claude CLI).

### Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/cheekyclaps/nulka_agent.git
   cd nulka_agent
   ```

2. **Install the Package**
   It is highly recommended to install the package in editable mode if you plan on modifying agent behavior.
   ```bash
   pip install -e .
   ```

3. **Initialize the Environment**
   Launch the application for the first time. If no global configuration is found, NulkaAgent will launch an interactive onboarding wizard to configure your Universal Oracle command.
   ```bash
   nulka_agent
   ```

---

## Usage Guide

NulkaAgent operates as an interactive shell. From any directory in your terminal, type `nulka_agent` to boot the application.

### Basic Interaction

Once inside the prompt, simply type your requirement or question in natural language:

```text
> Please audit the current directory for hardcoded secrets and generate a compliance report.
```
The internal Semantic Router will automatically classify this as a Security task, bypass the general assistant, and dispatch the Security Officer to execute the audit.

### Slash Commands

NulkaAgent supports interactive system commands to manage state, models, and execution parameters.

- `/init`: Initializes the current directory as an NulkaAgent workspace. This creates a `.nulka_agent` folder to permanently save session interaction history and contextual memory.
- `/models`: Queries the local Ollama daemon and displays a table of all cached and actively loaded local models.
- `/pull <model_name>`: Pulls a new model directly from the Ollama library.
- `/teach`: Triggers the Interactive Feedback Loop on the last executed query. This fetches the correct answer from the Oracle and embeds it into the failing agent's behavior rules.
- `/expand`: Opens the raw, un-truncated output of the last command in a native full-screen terminal pager.
- `/clear`: Clears the screen and resets the current context buffer.
- `/cd <path>`: Changes the active working directory of the application.
- `/ls <path>`: Lists the contents of a specified directory.
- `/vim`: Toggles Vim keybindings for the interactive input prompt.
- `/quit`: Terminates the NulkaAgent session.

## Architecture

NulkaAgent is built on top of the CrewAI framework but heavily modified for dynamic, interactive terminal use.

- **Tools Integration**: Agents are equipped with a native Python toolset allowing them to read files, write files, perform recursive glob searches, execute safe grep operations, and run bash shell commands. Read and write permissions are strictly segregated based on the agent's organizational role.
- **State Management**: The application utilizes a singleton state manager that records prompt histories, routing paths, and execution times, ensuring seamless transitions into feedback loops or paginated reviews.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
