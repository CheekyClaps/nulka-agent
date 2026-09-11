# Universal Oracle & /teach Feedback Loop

## Objective
Enhance the OmniHub architecture to allow manual user corrections via a `/teach` command, decouple the Oracle fallback from being strictly Gemini-dependent (making it a Universal Oracle), and package it beautifully as a system-wide Python utility (`setup.py`) with a built-in first-boot setup wizard inside the Python CLI (eliminating clunky scripts).

## Key Files & Context
- `cli.py`: Will store the `LAST_PROMPT` and `LAST_ROUTE`. Will implement the `/teach` command workflow. Will implement the interactive setup wizard on boot if `.env` is missing.
- `setup.py`: A packaging script to allow `pip install -e .` and expose a global `omnihub` command.
- `tools/oracle_cli_tool.py`: Renamed and refactored from `gemini_cli_tool.py` to use a dynamic `ORACLE_CMD` environment variable.
- `tools/consult_oracle_tool.py`: Renamed from `consult_gemini_oracle_tool.py` to be model-agnostic.
- `config/agents/external_oracle.md`: Renamed from `gemini_fallback.md`.
- `.env`: A configuration file dynamically managed by the internal setup wizard.

## Implementation Steps

### 1. Python Packaging (`setup.py`)
Create a `setup.py` in the root of the project that:
1. Declares packages and dependencies.
2. Registers an `entry_points` console script: `omnihub = cli:run_interactive_cli`.
3. Allows installing globally or in user-space via `pip install .` or `pip install -e .`.

### 2. Onboarding Setup Wizard (First-Boot inside Python)
Inside `cli.py` or `utils.py`:
1. Check if `.env` (or config file) exists.
2. If missing, pause the normal CLI startup and boot a gorgeous, stylized **Setup Wizard** using `rich` and `prompt_toolkit`.
3. Scan the user's local `PATH` for standard AI CLIs (`gemini`, `chatgpt`, `claude`).
4. Ask the user (with interactive options) to select their preferred Oracle CLI tool or input a custom execution command.
5. Save the configuration to `.env` dynamically.
6. Reload environment variables and continue the boot process seamlessly!

### 3. Universal Oracle Refactoring
1. **Tool Refactor:** Rename `gemini_cli_tool.py` to `oracle_cli_tool.py`. Modify it to read `os.getenv("ORACLE_CMD")` instead of hardcoding `gemini`. It will execute `ORACLE_CMD + " " + prompt`.
2. **Consult Tool Refactor:** Rename `consult_gemini_oracle_tool.py` to `consult_oracle_tool.py`.
3. **Agent Refactor:** Rename the `gemini_fallback` agent in `config/agents.yaml` and `cli.py` to `external_oracle`. Update `config/agents/teacher.md` and `config/agents/external_oracle.md` to remove specific "Gemini" branding, making it a generic "Elite External Oracle".

### 4. The `/teach` Feedback Loop
1. **State Tracking:** In `cli.py`, introduce global `LAST_USER_PROMPT` and `LAST_ROUTE` variables. Update these during every normal execution.
2. **Command Handling:** When the user types `/teach` or `/feedback`:
   - If `LAST_USER_PROMPT` is empty, warn the user.
   - Otherwise, bypass standard routing.
   - Instantiate a micro-crew consisting ONLY of the `Teacher` and `External Oracle`.
   - The Task for the Teacher: "The user reported that the previous response to '{LAST_USER_PROMPT}' was incomplete or incorrect. 1. Consult the Oracle with this prompt. 2. Use the 'interactive_teacher_tool' on the '{LAST_ROUTE}' agent to propose a correction. The user will augment this proposal with their explicit feedback."
3. **Execution:** This allows the user to immediately say `/teach`, see the interactive prompt, and type "Explain that local runs Qwen and Oracle runs Gemini", permanently fixing the agent!

## Verification
1. Remove `.env` and verify running `python cli.py` triggers the beautiful onboarding wizard.
2. Confirm `.env` is created.
3. Install package via `pip install -e .` and verify the `omnihub` command runs globally on the terminal.
4. Verify `/teach` operates perfectly on an incomplete answer.
