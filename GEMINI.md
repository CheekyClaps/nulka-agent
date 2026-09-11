# OmniAgent Workspace Memory

## 🏗 Project Architecture & State (As of Sept 11, 2026)

This project has been transformed from a basic CrewAI boilerplate into **OmniAgent**, a highly robust, production-ready, globally executable Python package.

### Key Capabilities & Workflows:
1. **Dynamic Omni-Agent Corporate Crew:**
   * Contains 8 specialized departments: `Router, Planner, Architect, Developer, Tester, Pentester, Security Officer, Network Engineer`.
   * Also includes a `Teacher` (Educational Director) and an `External Oracle` (Fallback Consultant).
   * YAML & Markdown configuration split. Meta-properties reside in `omniagent/config/agents.yaml`, while long-form backstories and reasoning protocols are in individual files under `omniagent/config/agents/*.md`.

2. **The Prompt Scrutinizer (Pre-Execution):**
   * Before spinning up heavy LLM crews, a lightweight LLM scrutinizer evaluates the user prompt for missing context (e.g. missing filenames or physical location).
   * If context is missing, the router actively asks the user for clarification in the terminal, appending it to the prompt.

3. **Semantic Router & HRF Shield:**
   * Uses Lexical/Semantic routing (via `ollama_llm`).
   * Implements a **Hallucination Risk Factor (HRF)** heuristic. If a prompt triggers high risk (e.g. spatial queries, URLs, live data), it bypasses local agents and delegates immediately to the `Universal Oracle`.
   * HRF is completely dynamic per-model (tracked in `~/.oac_hrf.json`). It supports `/trust` (lower risk threshold), `/doubt` (higher risk threshold), and naturally stabilizes 10% back to a baseline after every run.

4. **Universal Oracle Fallback:**
   * Natively hooks into the user's globally installed AI CLI tool (`gemini`, `claude`, `chatgpt`).
   * Configured via `~/.oac_env` under `ORACLE_CMD`.

5. **Self-Learning Feedback Loop (`/teach`):**
   * If a local agent fails or hallucinates an answer, the user types `/teach`.
   * The system bypasses standard workflow, queries the absolute truth from the Universal Oracle, and triggers the `InteractiveTeacherTool`.
   * The terminal presents an interactive Zellij-style UI (using `prompt_toolkit` bottom toolbars). The user can Accept, Reject, or Augment the rule.
   * **Git-Versioned Persistence:** Approved rules are appended to the agent's backstory `.md` file, and instantly committed to the Git repository (e.g., `OmniAgent Learning Loop: Update assistant.md`).

6. **Smart Output Condenser (`/expand`):**
   * Any tool output (e.g. `search_workspace` grabbing 40,000 files) is instantly intercepted and truncated to 30 lines with a glowing `[ ... Lines Condensed ... ]` tag.
   * Prevents terminal flooding and LLM context window crashes.
   * Users can type `/expand` to open the full raw string in a native terminal pager (like `less`).

### 🚀 Commands to Run the App
The project is packaged via `setup.py`. It is symlinked globally to `~/.local/bin/omniagent`.
* To run the app, type: `omniagent`
* The interactive Onboarding Wizard automatically handles missing `.oac_env` configs.
* Ensure you configure `LOCAL_MODEL="qwen2.5:14b"` for the best agentic reasoning capability!
