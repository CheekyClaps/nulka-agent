# CrewAI Company Architecture & Router Plan

## Objective
Transform the `crewai-setup` project into a comprehensive, company-like AI agent organization with a fluid, interactive CLI interface. This includes establishing diverse organizational roles, implementing a semantic router inspired by LiteLLM principles, introducing Markdown-backed agent context loading, and equipping agents with Gemini functionality via a custom CLI tool. The entire system will be wrapped in a persistent, styling-rich terminal shell, removing the need to manually edit and run Python scripts.

## Scope & Impact
- **Relocation:** Project successfully moved to `~/Projects/crewai-setup`.
- **Interactive Interface:** Building a persistent Interactive CLI Shell (using `rich` and `prompt_toolkit`) to serve as the user's primary chat/command interface with the Router.
- **Organizational Roles:** Transitioning to a structured crew: Planner, Systems Engineer, Developer, Tester, Pentester, Security Officer, Network Engineer, and Router.
- **Configuration Pattern:** Adopting a YAML + Markdown split. Core agent configurations (`role`, `goal`, etc.) will reside in YAML, while long-form `backstory` and context will be loaded dynamically from dedicated `.md` files.
- **Tooling:** Introducing a `GeminiCLITool` that allows agents to execute local `gemini-cli` commands.

## Implementation Steps

### 1. Interface Layer (Interactive CLI)
- Create `cli.py` as the main entry point.
- Implement a persistent chat loop using `prompt_toolkit` for history and auto-completion, and `rich` for beautifully formatted markdown, agent thoughts, and status spinners.
- The CLI will capture user input and pass it directly to the **Router Agent**, effectively acting as the user's window into the AI "Company".

### 2. Agent Roles & Context Setup
- Define the following agents in `config/agents.yaml`:
  - **Router:** Analyzes queries, extracts semantic keywords, and routes tasks.
  - **Planner (PM):** Product management, epic/task breakdown.
  - **Systems Engineer:** High-level architecture, constraints analysis.
  - **Developer:** Code generation and refactoring.
  - **Tester (QA):** Quality assurance and validation.
  - **Pentester:** Identifies vulnerabilities and attempts exploits.
  - **Security Officer:** Defines security policies and reviews code for compliance.
  - **Network Engineer:** Designs network topologies and manages routing/firewall rules.
- Create corresponding Markdown files in `config/agents/` (e.g., `planner.md`, `pentester.md`) to serve as rich, well-thought-out backstories. 
  - **2026 Prompt Architecture:** These `.md` files will not be written from scratch. They will be auto-populated using enterprise-grade prompt patterns derived from state-of-the-art 2026 frameworks (like Microsoft's Magentic-One and OpenHands). Each file will include:
    - **Operational Protocol:** Strict step-by-step reasoning rules.
    - **Contextual Boundaries:** Defining what the agent can and cannot do.
    - **Tooling Constraints:** How to safely use the Gemini CLI Tool.
    - **Tone & Persona:** Professional, deterministic, and output-focused.

### 3. Dynamic Environmental Context Injection
- The system must provide real-time situational awareness (Time, OS, Geolocation) to the Router and other agents.
- **Implementation Mechanism:** 
  - Use CrewAI's `inputs` parameter during the `crew.kickoff(inputs={...})` execution.
  - In `cli.py` or `main.py`, create a function to gather host metrics before execution:
    - `current_time` via `datetime.now()`.
    - `system_os` via `platform.system()` and `platform.release()`.
    - `geolocation` via system timezone mapping or a lightweight local IP check.
  - Use placeholders (e.g., `{current_time}`, `{system_os}`) inside the agent's Markdown backstory files. The framework will dynamically inject these variables into the system prompt right before the LLM call.

### 4. Markdown Backstory Loader
- Implement a loading mechanism in `crew.py` (or a dedicated `utils.py`).
- The YAML configuration will include a `backstory_file` pointer (e.g., `backstory_file: config/agents/developer.md`).
- During agent instantiation, the loader will read the specified `.md` file and inject its contents into the agent's `backstory` property.

### 5. Semantic Router Implementation
- Design the **Router Agent** as the entry point for the crew.
- Equip the Router with instructions (in `router.md`) to analyze incoming prompts using LiteLLM-like principles:
  - **Lexical/Keyword matching:** Looking for explicit cues (e.g., "plan", "test", "architect").
  - **Intent Classification:** Using the LLM to classify the core intent and delegate the task to the appropriate specialist agent (Planner, Systems Engineer, Developer, or Tester) or sub-crew.

### 6. Gemini CLI Integration Tool
- Create `tools/gemini_cli_tool.py`.
- Define `GeminiCLITool` inheriting from CrewAI's `BaseTool`.
- Implement the `_run` method using Python's `subprocess.run()` to execute `gemini-cli` commands on the local machine.
- Ensure proper error handling and capture of `stdout`/`stderr` to return actionable feedback to the agent.
- Assign this tool to relevant agents (e.g., Systems Engineer, Developer) so they can leverage Gemini for local codebase interactions.

## Verification & Testing
1. **Config Validation:** Instantiate the Crew and verify that backstories are correctly populated from the `.md` files.
2. **Tool Execution:** Test the `GeminiCLITool` with a safe command (e.g., `gemini-cli --help`) to ensure subprocess execution and output capture work flawlessly.
3. **Routing Logic:** Feed the Crew varying prompts (e.g., "Write a test for X" vs. "Plan a new authentication feature") and verify the Router correctly delegates to the Tester and Planner respectively.
