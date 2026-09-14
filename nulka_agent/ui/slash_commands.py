import os
import sys

from nulka_agent.core.state import state
from nulka_agent.utils import get_system_context
from nulka_agent.hrf_manager import hrf_manager

# Inline implementation to avoid circular dependencies
def get_active_model_name() -> str:
    from nulka_agent.utils import get_best_available_model
    return get_best_available_model()

# Note: console, execute_teach_feedback, execute_expand_pager are imported/passed where needed
# to avoid massive circular imports, we will keep the heavy lifting in cli.py or pass callables.

def handle_slash_command(cmd: str, parts: list[str], console, session, cli_module) -> bool:
    """
    Handles slash commands for the interactive CLI.
    Returns True if the command was handled (meaning the loop should `continue`).
    Returns False if it was not a handled slash command (or unknown).
    """
    
    # 1. Core Session & Environment
    if cmd in ["/help", "/?", "/commands"]:
        print_help(console)
        return True
    elif cmd == "/about":
        console.print("[bold green]NulkaAgent[/bold green] - A robust, production-ready omni-agent CLI.")
        console.print("[dim]Inspired by the Gemini CLI. Powered by CrewAI & Ollama.[/dim]")
        return True
    elif cmd == "/clear":
        os.system('clear' if os.name == 'posix' else 'cls')
        if hasattr(session.history, 'clear'):
            # Some prompt_toolkit histories don't support direct clear, but we do our best
            try: session.history.clear()
            except: pass
        state.last_user_prompt = None
        state.last_full_output = None
        console.print("[bold green]✨ Screen and session context cleared.[/bold green]")
        return True
    elif cmd == "/vim":
        state.vim_mode = not state.vim_mode
        status = "[bold green]ON[/bold green]" if state.vim_mode else "[bold red]OFF[/bold red]"
        console.print(f"⌨️  [bold]Vim Mode:[/bold] {status}")
        return True
    elif cmd in ["/quit", "/exit"]:
        if "--delete" in parts:
            history_file = os.path.join(os.path.expanduser("~"), ".nulka_agent_history")
            if os.path.exists(history_file):
                os.remove(history_file)
            console.print("[bold red]🗑️ History purged.[/bold red]")
        console.print("[bold yellow]Goodbye human[/bold yellow]")
        sys.exit(0)

    # 2. Tools & Agents Inspection
    elif cmd == "/tools":
        console.print("[bold cyan]🛠️ Available NulkaAgent Tools:[/bold cyan]")
        console.print("  - [bold]read_file[/bold]: Read file contents.")
        console.print("  - [bold]write_file[/bold]: Write to files.")
        console.print("  - [bold]search_workspace[/bold]: Glob search files.")
        console.print("  - [bold]run_shell_command[/bold]: Execute bash shell commands.")
        console.print("  - [bold]consult_oracle[/bold]: Fallback to universal truth (gemini/claude).")
        return True
    elif cmd == "/agents":
        console.print("[bold magenta]🤖 Available NulkaAgent Departments:[/bold magenta]")
        console.print("  - Router, Planner, Architect, Developer, Tester, Pentester, Security Officer, Network Engineer, Teacher")
        return True
    
    # 3. Output Management
    elif cmd == "/copy":
        if not state.last_full_output:
            console.print("[bold red]❌ No recent output to copy.[/bold red]")
            return True
        try:
            # Fallback copy mechanism (very basic cross-platform support via pyperclip if installed)
            import pyperclip
            pyperclip.copy(state.last_full_output)
            console.print("[bold green]✅ Copied last output to clipboard![/bold green]")
        except ImportError:
            console.print("[bold yellow]⚠️ 'pyperclip' not installed. Unable to copy to clipboard.[/bold yellow]")
            console.print("[dim]Run 'pip install pyperclip' to enable this command.[/dim]")
        return True
    elif cmd == "/expand":
        cli_module.execute_expand_pager()
        return True
        
    # 4. Workspace & Directory
    elif cmd == "/init":
        workspace_dir = os.path.join(os.path.abspath(os.getcwd()), ".nulka_agent")
        if os.path.exists(workspace_dir):
            console.print(f"[bold yellow]⚠️ Workspace already initialized at {workspace_dir}[/bold yellow]")
        else:
            try:
                os.makedirs(workspace_dir)
                with open(os.path.join(workspace_dir, "session.json"), "w", encoding="utf-8") as f:
                    f.write('{"history": []}')
                console.print(f"[bold green]✅ Successfully initialized NulkaAgent workspace at {workspace_dir}[/bold green]")
                console.print("[dim]Session progress and workspace memory will now be persistently saved here.[/dim]")
            except Exception as e:
                console.print(f"[bold red]❌ Failed to initialize workspace: {e}[/bold red]")
        return True
    elif cmd == "/cd":
        target_dir = os.path.expanduser(" ".join(parts[1:]) if len(parts) > 1 else "~")
        target_dir = os.path.abspath(target_dir)
        if not os.path.exists(target_dir):
            console.print(f"[bold red]❌ Directory does not exist: {target_dir}[/bold red]")
        elif not os.path.isdir(target_dir):
            console.print(f"[bold red]❌ Path is not a directory: {target_dir}[/bold red]")
        else:
            try:
                os.chdir(target_dir)
                if target_dir not in state.active_workspace_dirs:
                    state.active_workspace_dirs.append(target_dir)
                console.print(f"[bold green]✅ Changed working directory to:[/] [cyan]{target_dir}[/cyan]")
            except Exception as e:
                console.print(f"[bold red]❌ Failed to change directory: {e}[/bold red]")
        return True
    elif cmd == "/pwd":
        console.print(f"📂 [bold]Current Working Directory:[/bold] [cyan]{os.getcwd()}[/cyan]")
        return True
    elif cmd in ["/ls", "/list"]:
        target_dir = os.path.expanduser(" ".join(parts[1:]) if len(parts) > 1 else ".")
        target_dir = os.path.abspath(target_dir)
        if not os.path.exists(target_dir):
            console.print(f"[bold red]❌ Path does not exist: {target_dir}[/bold red]")
            return True
        if not os.path.isdir(target_dir):
            console.print(f"[bold red]❌ Path is not a directory: {target_dir}[/bold red]")
            return True
        try:
            items = sorted(os.listdir(target_dir))
            if not items:
                console.print("[dim]Directory is empty.[/dim]")
                return True
            
            # Format nicely: Directories first, then files
            dirs = []
            files = []
            for item in items:
                # Ignore hidden files by default unless asked, or just show them
                full_path = os.path.join(target_dir, item)
                if os.path.isdir(full_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            console.print(f"📂 [bold]Listing directory:[/bold] [cyan]{target_dir}[/cyan]")
            for d in dirs:
                console.print(f"  [bold blue]📁 {d}/[/bold blue]")
            for f in files:
                console.print(f"  📄 {f}")
        except Exception as e:
            console.print(f"[bold red]❌ Failed to list directory: {e}[/bold red]")
        return True
    elif cmd in ["/dir", "/directory", "/workspace"]:
        subcmd = parts[1].lower() if len(parts) > 1 else "show"
        if subcmd == "show":
            console.print("[bold yellow]📂 Active Workspace Directories:[/bold yellow]")
            for d in state.active_workspace_dirs:
                active_marker = " [bold green](Current)[/bold green]" if d == os.getcwd() else ""
                console.print(f"  ➔ [cyan]{d}[/cyan]{active_marker}")
        elif subcmd == "add" and len(parts) >= 3:
            for p in " ".join(parts[2:]).split(","):
                p_exp = os.path.abspath(os.path.expanduser(p.strip()))
                if os.path.isdir(p_exp) and p_exp not in state.active_workspace_dirs:
                    state.active_workspace_dirs.append(p_exp)
                    console.print(f"[bold green]✅ Added to workspace:[/bold green] [cyan]{p_exp}[/cyan]")
        elif subcmd in ["set", "cd"] and len(parts) >= 3:
            handle_slash_command("/cd", ["/cd"] + parts[2:], console, session, cli_module)
        else:
            console.print("[bold red]❌ Usage: /workspace [show|add <paths>|set <path>][/bold red]")
        return True

    # 5. Core Display & Debug
    elif cmd == "/metrics":
        state.show_metrics = not state.show_metrics
        status = "[bold green]ON[/bold green]" if state.show_metrics else "[bold red]OFF[/bold red]"
        console.print(f"📊 [bold]Metrics Toolbar:[/bold] {status}")
        return True
    elif cmd == "/debug":
        cli_module.DEBUG_MODE = not cli_module.DEBUG_MODE
        status = "[bold green]ON[/bold green]" if cli_module.DEBUG_MODE else "[bold red]OFF[/bold red]"
        console.print(f"⚙️  [bold]Debug Mode (Verbose Agent Thoughts):[/bold] {status}")
        return True

    # 6. Model Management
    elif cmd == "/models":
        cli_module.show_ollama_models()
        return True
    elif cmd == "/pull":
        if len(parts) < 2:
            console.print("[bold red]❌ Usage: /pull <model_name>[/]")
        else:
            cli_module.pull_ollama_model(parts[1])
        return True
        
    # 7. HRF & Trust Commands
    elif cmd == "/oracle":
        if len(parts) < 2:
            console.print("[bold red]❌ Usage: /oracle <your query>[/]")
            return True
        query = " ".join(parts[1:])
        # Direct bypass to Oracle
        cli_module.execute_crew_workflow("ORACLE", query)
        return True
    elif cmd in ["/teach", "/feedback"]:
        cli_module.execute_teach_feedback()
        return True
    elif cmd == "/hrf":
        active_model = get_active_model_name()
        thresh = hrf_manager.get_threshold(active_model)
        base = hrf_manager.get_baseline(active_model)
        from rich.panel import Panel
        console.print(Panel(
            f"Active Model: [bold cyan]{active_model}[/bold cyan]\n"
            f"Current Threshold: [bold magenta]{thresh:.2f}[/bold magenta]\n"
            f"Baseline: [dim]{base:.2f}[/dim]\n\n"
            f"If a prompt's risk score exceeds this threshold, the query defaults to the Oracle.\n"
            f"Use [bold cyan]/trust[/] to raise the threshold, [bold yellow]/doubt[/] to lower it, and [bold red]/bs[/] to penalize it heavily.",
            title="Hallucination Risk Factor (HRF) Status", border_style="blue"
        ))
        return True
    elif cmd == "/trust":
        active_model = get_active_model_name()
        new_thresh = hrf_manager.trust(active_model)
        console.print(f"[bold green]✅ Trust Increased for {active_model}. HRF threshold is now {new_thresh:.2f}[/]")
        return True
    elif cmd == "/doubt":
        active_model = get_active_model_name()
        new_thresh = hrf_manager.doubt(active_model)
        console.print(f"[bold yellow]⚠️ Trust Decreased for {active_model}. HRF threshold is now {new_thresh:.2f}[/]")
        return True
    elif cmd == "/bs":
        weight = 3.0
        if len(parts) > 1:
            try: weight = float(parts[1])
            except ValueError: pass
        active_model = get_active_model_name()
        new_thresh = hrf_manager.bs(active_model, weight)
        console.print(f"[bold red]🚨 Bullshit Penalty Applied (-{weight}) to {active_model}![/bold red]")
        console.print(f"HRF threshold plummeted to {new_thresh:.2f}")
        if new_thresh <= 1.0:
            console.print("\n[bold red]⚠️ ZERO TRUST MODE INITIATED ⚠️[/bold red]")
            console.print("The local model has lost all trust. All future queries will be locked down and routed to the External Oracle.")
            console.print("Type [bold cyan]/forgive[/bold cyan] to reset trust back to baseline.")
        return True
    elif cmd in ["/forgive", "/reset"]:
        active_model = get_active_model_name()
        new_thresh = hrf_manager.reset(active_model)
        console.print(f"[bold green]🕊️ Trust Forgiven. The local model {active_model} has been granted a clean slate.[/bold green]")
        return True

    # 8. Unimplemented/Mocked External Extensions
    elif cmd in ["/mcp", "/extensions", "/skills", "/plan", "/policies", "/hooks", "/shells", "/bashes", "/setup-github", "/resume", "/chat", "/rewind", "/restore", "/settings", "/theme", "/terminal-setup", "/permissions", "/compress", "/memory", "/stats", "/bug", "/upgrade", "/privacy"]:
        console.print(f"[yellow]⚠️  Command '{cmd}' is a recognized Gemini command, but is currently stubbed/unsupported in NulkaAgent.[/yellow]")
        console.print("[dim]NulkaAgent focuses on autonomous CrewAI agentic behaviors over direct manual REPL scaffolding.[/dim]")
        return True

    else:
        console.print(f"[bold red]❌ Unknown command: {cmd}. Type /help to list commands.[/]")
        return False


def print_help(console):
    from rich.panel import Panel
    console.print(Panel(
        "[bold yellow]Core System[/bold yellow]\n"
        "  [bold cyan]/about[/]              Show NulkaAgent version and diagnostic info\n"
        "  [bold cyan]/clear[/]              Clear the screen and reset session context\n"
        "  [bold cyan]/vim[/]                Toggle Vim-mode keybindings for the prompt\n"
        "  [bold cyan]/quit[/]               Exit session (use --delete to purge history)\n\n"
        "[bold yellow]Tools, Output, & Agents[/bold yellow]\n"
        "  [bold cyan]/expand[/]             View the last truncated output in a full-screen pager\n"
        "  [bold cyan]/copy[/]               Copy the last raw output to your clipboard\n"
        "  [bold cyan]/tools[/]              List available capabilities\n"
        "  [bold cyan]/agents[/]             List available specialized AI departments\n"
        "  [bold cyan]/oracle <query>[/]     Directly query the External Universal Oracle\n"
        "  [bold cyan]/metrics[/]            Toggle the live bottom toolbar for performance metrics\n"
        "  [bold cyan]/debug[/]              Toggle verbose agent thoughts & details\n\n"
        "[bold yellow]Workspace & Directory Management[/bold yellow]\n"
        "  [bold cyan]/cd [path][/]          Change current working directory\n"
        "  [bold cyan]/pwd[/]                Show current working directory path\n"
        "  [bold cyan]/ls [path][/]           List contents of a directory (defaults to current)\n"
        "  [bold cyan]/workspace [cmd][/]    Manage active directories (subcmds: show, add, set)\n\n"
        "[bold yellow]Learning & Trust (HRF)[/bold yellow]\n"
        "  [bold cyan]/teach[/]              Flag the last response as incomplete & teach the agent\n"
        "  [bold cyan]/hrf[/]                Show current Hallucination Risk Factor settings\n"
        "  [bold cyan]/trust[/]              Trust model more (raises Oracle threshold)\n"
        "  [bold cyan]/doubt[/]              Trust model less (lowers Oracle threshold)\n"
        "  [bold cyan]/bs [weight][/]        Apply hallucination penalty to drop trust\n"
        "  [bold cyan]/forgive[/]            Reset trust back to clean-slate baseline\n\n"
        "[bold yellow]Model Management[/bold yellow]\n"
        "  [bold cyan]/models[/]             Show downloaded & loaded Ollama models\n"
        "  [bold cyan]/pull <name>[/]        Download a new model from the Ollama library",
        title="NulkaAgent Command Reference", border_style="blue"
    ))
