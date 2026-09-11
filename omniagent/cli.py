import os
import sys
import glob
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import warnings
import logging

# Suppress Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Suppress OpenTelemetry TracerProvider overriding warnings caused by sequential crew kickoffs
logging.getLogger("opentelemetry.trace").setLevel(logging.ERROR)
logging.getLogger("opentelemetry.sdk.trace").setLevel(logging.ERROR)

CONFIG_PATH = os.path.expanduser("~/.omniagent_env")
# Load environment variables on startup
load_dotenv(CONFIG_PATH)

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from crewai import Crew, Task, Process
from langchain.tools import tool
from omniagent.utils import (
    instantiate_agents, 
    get_system_context, 
    ollama_llm,
    is_ollama_running,
    start_ollama_server,
    get_local_models,
    get_loaded_models
)

# Initialize Rich Console
console = Console()

# Define Workspace Tools (using exact compatibility from old cli.py)
@tool("read_file")
def read_file_tool(file_path: str) -> str:
    """Reads the contents of a file."""
    try:
        if not os.path.exists(file_path):
            return f"File does not exist: {file_path}"
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@tool("write_file")
def write_file_tool(file_path: str, content: str) -> str:
    """Writes content to a file, creating it if it doesn't exist."""
    try:
        # Automatically create directory structure if missing
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(file_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"

@tool("search_workspace")
def search_workspace_tool(pattern: str = "**/*.md") -> str:
    """Searches the workspace for files matching a glob pattern (e.g. **/*.md or **/*.py). 
    WARNING: Do NOT use broad patterns like '**/*' as it will return thousands of files and crash your context window. Always be highly specific."""
    try:
        files = glob.glob(pattern, recursive=True)
        if not files:
            return "No files found matching that pattern."
        # Truncate output natively inside the tool to prevent terminal flooding during verbose runs
        return format_condensed_output("\n".join(files), max_lines=100)
    except Exception as e:
        return f"Error searching workspace: {e}"

@tool("run_shell_command")
def run_shell_command_tool(command: str) -> str:
    """Executes a bash shell command and returns its output. 
    CRITICAL: You are running in a non-interactive environment. You MUST use non-interactive flags (e.g., `-y`, `--assumeyes`, `--quiet`, `--no-pager`, `--noninteractive`). 
    If a command presents an unavoidable interactive menu (like flatpak asking 'Which do you want to use [0-4]:'), you MUST pipe input into it using echo (e.g., `echo 0 | flatpak uninstall ...`). Failure to do so will cause the command to abort."""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=300)
        output = result.stdout
        if result.stderr:
            output += f"\nError output:\n{result.stderr}"
        raw_output = output.strip() if output.strip() else "Command executed successfully with no output."
        # Truncate natively
        return format_condensed_output(raw_output, max_lines=100)
    except Exception as e:
        return f"Failed to execute command: {e}"

# Bundle workspace tools
workspace_tools = [read_file_tool, write_file_tool, search_workspace_tool, run_shell_command_tool]

# Initialize Agents
agents = instantiate_agents(custom_tools=workspace_tools)

# Global Debug Mode to control agent thought verbosity
DEBUG_MODE = False

# Global state to support the /teach feedback loop and /expand condenser
LAST_USER_PROMPT = None
LAST_ROUTE = None
LAST_FULL_OUTPUT = None

def format_condensed_output(text: str, max_lines: int = 40) -> str:
    """Smartly truncates massive string outputs for the terminal UI."""
    if not text:
        return text
    lines = text.split("\n")
    if len(lines) <= max_lines:
        return text
        
    first_part = "\n".join(lines[:15])
    last_part = "\n".join(lines[-15:])
    hidden = len(lines) - 30
    
    divider = f"\n\n[dim cyan]... [ {hidden} Lines Condensed. Type /expand to view full output ] ...[/dim cyan]\n\n"
    return first_part + divider + last_part

def lexical_routing(prompt: str) -> str:
    """Performs fast lexical keyword matching (LiteLLM principle)."""
    p = prompt.lower()
    
    # Offensive Security
    if any(k in p for k in ["pentest", "exploit", "penetration", "hack", "vulnerability", "vulnerable", "attacker"]):
        return "PENTEST"
    # Defensive Security
    if any(k in p for k in ["security", "audit", "compliance", "encryption", "cipher", "secret", "owasp"]):
        return "SECURITY"
    # Networking
    if any(k in p for k in ["network", "dns", "firewall", "iptables", "port", "ip address", "nginx", "proxy", "subnet"]):
        return "NETWORK"
    # Systems Architecture
    if any(k in p for k in ["architect", "design", "structural", "uml", "diagram", "pattern", "clean architecture"]):
        return "ARCHITECT"
    # Testing & QA
    if any(k in p for k in ["test", "pytest", "unit test", "validation", "qa", "verify"]):
        return "TEST"
    # Planning
    if any(k in p for k in ["plan", "roadmap", "epic", "sprint", "milestone", "scrum", "agile"]):
        return "PLAN"
    # Coding
    if any(k in p for k in ["code", "write python", "implement", "fix", "refactor", "bug", "develop"]):
        return "CODE"
        
    return None

def semantic_routing(prompt: str) -> str:
    """Uses LLM-based Intent Classification (LiteLLM fallback Classifier)."""
    system_prompt = (
        "You are the Company Dispatcher & Semantic Router.\n"
        "Your task is to classify the user's intent into ONE of the following categories:\n"
        "- 'PLAN': Wants requirements analysis, roadmaps, task breakdowns, or sprint setups.\n"
        "- 'ARCHITECT': Wants system architecture, framework evaluations, clean code design patterns, or diagrams.\n"
        "- 'CODE': Explicit requests to WRITE, MODIFY, or REFACTOR code files. DO NOT use this for simply locating or finding files.\n"
        "- 'TEST': Wants unit tests, functional verification suites, linter runs, or test execution.\n"
        "- 'PENTEST': Wants offensive audits, vulnerability scans, exploit PoCs, or security penetration.\n"
        "- 'SECURITY': Wants secure coding standards, cryptography reviews, regulatory audits, or secret detection.\n"
        "- 'NETWORK': Wants port mapping, firewall rule changes, proxy configs, or domain configuration.\n"
        "- 'GENERAL': General tech explanations, chatting, finding/locating files on disk, answering 'what', 'where', or 'how' questions without modifying code.\n\n"
        "CRITICAL RULE: If the prompt is asking to find a file, read a file, or is a conversational inquiry, ALWAYS classify as GENERAL.\n\n"
        "Reply with ONLY the matching category name in capital letters (PLAN, ARCHITECT, CODE, TEST, PENTEST, SECURITY, NETWORK, or GENERAL).\n\n"
        f"Prompt: {prompt}"
    )
    try:
        response = ollama_llm.invoke(system_prompt).strip().upper()
        # Find exact matches in response
        for cat in ["PLAN", "ARCHITECT", "CODE", "TEST", "PENTEST", "SECURITY", "NETWORK", "GENERAL"]:
            if cat in response:
                return cat
    except Exception as e:
        console.print(f"[bold red]Router Error during semantic classification: {e}[/]")
    return "GENERAL"

def calculate_hallucination_risk(prompt: str) -> int:
    """Evaluates the prompt against common local LLM hallucination pitfalls."""
    import re
    p = prompt.lower()
    score = 0
    
    # 1. External URLs (Models heavily hallucinate reading/browsing live web)
    if re.search(r'(http[s]?://|www\.)', p):
        score += 8
        
    # 2. Spatial/Location Data (Lack of physical grounding)
    if re.search(r'\b(near me|closest|nearest|directions to|where is the)\b', p):
        score += 8
        
    # 3. Temporal/Live Data (Models don't know current dates, live news, or stock prices)
    if re.search(r'\b(latest|today|current version|release|weather|stock|news|live)\b', p):
        score += 6
        
    # 4. Obscure Facts / Dynamic Entities
    if re.search(r'\b(who won|population of|president of|ceo of)\b', p):
        score += 5
        
    # 5. Arithmetic / Strict Logic 
    if re.search(r'\b(calculate|multiply|divide|square root)\b', p):
        score += 4
        
    return min(score, 10)

from omniagent.hrf_manager import HRFManager

# Initialize the global HRF Manager
hrf_manager = HRFManager()

def get_active_model_name() -> str:
    """Helper to fetch the primary loaded model."""
    loaded = get_loaded_models()
    if loaded:
        return loaded[0]
    return "qwen2.5-coder:latest"

def scrutinize_prompt(prompt: str) -> str:
    """Uses LLM to evaluate if a prompt has enough context to be executed."""
    system_prompt = (
        "You are the OmniAgent Requirements Scrutinizer. Analyze the user's prompt.\n"
        "Does it lack critical context required to execute the request? (e.g., missing specific file names to read, missing physical location for spatial queries like finding a place, highly ambiguous goals).\n\n"
        "RULES:\n"
        "1. If it is perfectly actionable, or if it is a general conversational question, reply with ONLY the word: PROCEED\n"
        "2. If it is missing critical context, reply ONLY with a short, direct question asking the user for the missing information. Do NOT say 'PROCEED'.\n\n"
        f"User Prompt: {prompt}"
    )
    try:
        response = ollama_llm.invoke(system_prompt).strip()
        # Clean up possible conversational prefixes from LLM
        if "PROCEED" in response.upper() and len(response) < 15:
            return "PROCEED"
        return response
    except Exception as e:
        console.print(f"[bold red]Router Error during scrutiny: {e}[/]")
        return "PROCEED"

def route_request(prompt: str) -> str:
    """Integrates LiteLLM Lexical-Semantic routing logic and dynamic HRF evaluation."""
    
    # 0. Evaluate Hallucination Risk Factor (HRF)
    hrf_score = calculate_hallucination_risk(prompt)
    active_model = get_active_model_name()
    dynamic_threshold = hrf_manager.get_threshold(active_model)
    
    if hrf_score >= dynamic_threshold:
        console.print(f"[bold yellow]⚠️ High Hallucination Risk Factor Detected ({hrf_score} >= threshold {dynamic_threshold:.1f}). Defaulting to Universal Oracle...[/]")
        return "ORACLE"
        
    # 1. Lexical fast-path
    lexical_route = lexical_routing(prompt)
    if lexical_route:
        console.print(f"[bold cyan]🔍 [Lexical Router] Match found: {lexical_route}[/]")
        return lexical_route
        
    # 2. Semantic LLM-path fallback
    with console.status("[bold yellow]🧠 [Semantic Router] Classifying intent via local LLM...[/]"):
        semantic_route = semantic_routing(prompt)
    console.print(f"[bold cyan]🔍 [Semantic Router] Classified as: {semantic_route}[/]")
    return semantic_route

def execute_crew_workflow(route: str, prompt: str):
    """Dynamically assembles and kicks off the perfect Crew of agents based on the route."""
    context = get_system_context()
    inputs = {
        "user_prompt": prompt,
        "current_time": context["current_time"],
        "system_os": context["system_os"],
        "system_platform": context["system_platform"],
        "geolocation": context["geolocation"]
    }

    # Map routes to Agent combinations & Tasks
    if route == "ORACLE":
        tasks = [
            Task(
                description=(
                    f"The user asked a high-risk query: '{prompt}'.\n"
                    f"1. You MUST use the 'oracle_cli_tool' exactly once to execute this exact query: '{prompt}'.\n"
                    f"2. You MUST NOT modify or summarize the response.\n"
                    f"3. Return the EXACT string returned by the oracle_cli_tool as your final answer."
                ),
                expected_output="The exact, unmodified string returned by the oracle tool.",
                agent=agents["external_oracle"]
            )
        ]
        crew_agents = [agents["external_oracle"]]
        status_msg = "Consulting Elite External Oracle..."
        
    elif route == "PLAN":
        tasks = [
            Task(
                description=f"Analyze the requirement: '{prompt}'. Design a high-level roadmap and checklist. Store rules or steps.",
                expected_output="A clean, comprehensive Markdown-formatted product plan with checklists.",
                agent=agents["planner"]
            )
        ]
        crew_agents = [agents["planner"]]
        status_msg = "Planning department is drawing up blueprints..."

    elif route == "ARCHITECT":
        tasks = [
            Task(
                description=f"Analyze structural constraints for: '{prompt}'. Produce systems architecture designs, UML schemas, or file trees.",
                expected_output="An architectural specification document outlining modular boundaries and design patterns.",
                agent=agents["systems_engineer"]
            )
        ]
        crew_agents = [agents["systems_engineer"]]
        status_msg = "Systems Architecture is engineering the structural boundaries..."

    elif route == "CODE":
        # Multi-agent software dev squad: Dev -> QA -> Security Audit
        coding_task = Task(
            description=f"Implement functional code for requirement: '{prompt}'. Write cleanly commented code into workspace files.",
            expected_output="Functional code files created in the workspace.",
            agent=agents["developer"]
        )
        qa_task = Task(
            description="Examine the code implemented. Write and execute complete unit tests to verify correctness.",
            expected_output="Comprehensive unit tests validating code correctness.",
            agent=agents["tester"]
        )
        sec_task = Task(
            description="Conduct a defensive security review on the code. Ensure zero secrets are committed and secure coding rules are met.",
            expected_output="Defensive security pass certificate or vulnerability fix warnings.",
            agent=agents["security_officer"]
        )
        tasks = [coding_task, qa_task, sec_task]
        crew_agents = [agents["developer"], agents["tester"], agents["security_officer"]]
        status_msg = "Full Dev-QA-Security squad is implementing, verifying, and hardening your code..."

    elif route == "TEST":
        tasks = [
            Task(
                description=f"Analyze the workspace and write or execute test suites verifying target files for: '{prompt}'. Ensure test-driven standards.",
                expected_output="An operational test suite and a test execution summary report.",
                agent=agents["tester"]
            )
        ]
        crew_agents = [agents["tester"]]
        status_msg = "QA & Testing is executing validation routines..."

    elif route == "PENTEST":
        tasks = [
            Task(
                description=f"Perform offensive security scanning or binary analysis matching user scope: '{prompt}'. Attempt safe exploits.",
                expected_output="A vulnerability report with severity ratings, threat models, and proof of concept runs.",
                agent=agents["pentester"]
            )
        ]
        crew_agents = [agents["pentester"]]
        status_msg = "Ethical Penetration squad is launching offensive scans..."

    elif route == "SECURITY":
        tasks = [
            Task(
                description=f"Examine codebases or environments matching: '{prompt}' for security posture, compliance, encryption, and secure storage.",
                expected_output="A comprehensive CISO audit report highlighting defensive strengths, secret detections, and compliance metrics.",
                agent=agents["security_officer"]
            )
        ]
        crew_agents = [agents["security_officer"]]
        status_msg = "Security Office is performing defensive posture reviews..."

    elif route == "NETWORK":
        tasks = [
            Task(
                description=f"Analyze and design topologies, proxies, firewalls, or docker networking configurations matching: '{prompt}'.",
                expected_output="A validated networking design configuration, docker composition, or firewall script blueprint.",
                agent=agents["network_engineer"]
            )
        ]
        crew_agents = [agents["network_engineer"]]
        status_msg = "Infrastructure Team is mapping subnet routing and firewalls..."

    else: # GENERAL
        # General Assistant route
        tasks = [
            Task(
                description=f"Respond helpfully, clearly, and contextualized to: '{prompt}'. Feel free to consult workspace files to make your answer highly precise.",
                expected_output="A helpful, professional response addressing the query fully.",
                agent=agents["assistant"]
            )
        ]
        crew_agents = [agents["assistant"]]
        status_msg = "General Assistant is gathering information..."

    # Update global tracking state for the /teach feedback loop
    global LAST_USER_PROMPT, LAST_ROUTE
    LAST_USER_PROMPT = prompt
    LAST_ROUTE = route

    # Append Educational Teacher task for continuous self-learning fallback
    teacher_task = Task(
        description=(
            f"Review the entire context and actions taken to address: '{prompt}'.\n"
            f"- If the previous agents answered the question successfully and factually, return their exact final answer.\n"
            f"- If the previous agents failed, hallucinated, or were unable to answer, YOU MUST call the 'consult_oracle' tool with the query '{prompt}' to get the absolute truth. Then, return the EXACT string returned by the Oracle.\n"
            f"CRITICAL: Do not format your response as JSON. Do not add conversational filler. Return only the raw text of the final answer."
        ),
        expected_output="The exact, raw string containing the final answer to the user's prompt.",
        agent=agents["teacher"]
    )
    tasks.append(teacher_task)

    # Ensure learning loop agents are in the crew
    if agents["teacher"] not in crew_agents:
        crew_agents.append(agents["teacher"])
    if agents["external_oracle"] not in crew_agents:
        crew_agents.append(agents["external_oracle"])

    # Apply debug/verbosity settings dynamically to all agents in the current crew
    for agent in crew_agents:
        agent.verbose = DEBUG_MODE

    # Execute dynamic Crew
    with console.status(f"[bold green]🚀 {status_msg}[/]") as status:
        crew = Crew(
            agents=crew_agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=DEBUG_MODE
        )
        crew_output = crew.kickoff()
        result_text = str(crew_output)
        
    # Determine header message and Panel title dynamically
    if route == "GENERAL":
        completion_msg = "✨ Answer Completed!"
        title_str = "Answer"
    else:
        completion_msg = "✅ Task Execution Completed!"
        title_str = "Response & Deliverables"

    # Construct the Breadcrumb Path of executed steps
    steps = ["Router"]
    if route == "ORACLE":
        steps.extend(["Universal Oracle (HRF Bypass)"])
    elif route == "PLAN":
        steps.extend(["Product Planner", "Teacher"])
    elif route == "ARCHITECT":
        steps.extend(["Systems Architect", "Teacher"])
    elif route == "CODE":
        steps.extend(["Developer", "QA Tester", "Security Officer", "Teacher"])
    elif route == "TEST":
        steps.extend(["QA Tester", "Teacher"])
    elif route == "PENTEST":
        steps.extend(["Pentester", "Teacher"])
    elif route == "SECURITY":
        steps.extend(["Security Officer", "Teacher"])
    elif route == "NETWORK":
        steps.extend(["Network Engineer", "Teacher"])
    else: # GENERAL
        steps.extend(["General Assistant", "Teacher"])

    # Dynamically append Oracle and Backstory Update if fallback occurred
    if route != "ORACLE" and ("Oracle" in result_text or "retrieved from the Oracle" in result_text):
        steps.append("External Oracle")
        
        # Check if any agent backstory .md file was updated in the last 30 seconds
        import time
        recently_modified = False
        base_dir = os.path.dirname(os.path.abspath(__file__))
        agents_dir = os.path.join(base_dir, "config", "agents")
        for md_file in glob.glob(os.path.join(agents_dir, "*.md")):
            try:
                if time.time() - os.path.getmtime(md_file) < 30:
                    recently_modified = True
                    break
            except Exception:
                pass
        if recently_modified:
            steps.append("Backstory Updated")

    # Render breadcrumb trail cleanly
    breadcrumb_trail = " ➔ ".join([f"[bold cyan]{step}[/]" for step in steps])

    console.print(f"\n[bold green]{completion_msg}[/]")
    console.print(f"{breadcrumb_trail}\n")
    
    # Save absolute raw output to global state for the /expand command
    global LAST_FULL_OUTPUT
    LAST_FULL_OUTPUT = result_text
    
    # Condense string for UI display
    condensed_result = format_condensed_output(result_text)
    console.print(Panel(condensed_result, title=f"[bold white]{title_str}[/]", border_style="green"))
    
    # Stabilize HRF baseline for the active model after a successful completion
    active_model = get_active_model_name()
    new_thresh = hrf_manager.stabilize(active_model)
    # console.print(f"[dim]HRF stabilized to {new_thresh:.2f}[/dim]") # Hidden debug

def execute_teach_feedback():
    """Triggers the learning loop on the last executed query robustly by manually invoking tools."""
    global LAST_USER_PROMPT, LAST_ROUTE
    if not LAST_USER_PROMPT or not LAST_ROUTE:
        console.print("[bold red]❌ No previous query found to teach from. Please submit a query first.[/]")
        return

    console.print(f"\n[bold yellow]🎓 [Onboarding Feedback Loop] Activating Teacher...[/bold yellow]")
    console.print(f"Teaching from query: [bold cyan]'{LAST_USER_PROMPT}'[/bold cyan] (Route: [bold magenta]{LAST_ROUTE}[/bold magenta])")

    # Map the LAST_ROUTE to the correct agent filename/key to update
    route_to_agent_map = {
        "PLAN": "planner",
        "ARCHITECT": "systems_engineer",
        "CODE": "developer",
        "TEST": "tester",
        "PENTEST": "pentester",
        "SECURITY": "security_officer",
        "NETWORK": "network_engineer",
        "GENERAL": "assistant",
        "ORACLE": "assistant"
    }
    target_agent_key = route_to_agent_map.get(LAST_ROUTE, "assistant")

    console.print("[bold yellow]🚀 Consulting the External Oracle...[/]")
    from omniagent.tools.oracle_cli_tool import OracleCLITool
    from omniagent.tools.interactive_teacher_tool import InteractiveTeacherTool
    
    # 1. Fetch Oracle Truth manually
    oracle_tool = OracleCLITool()
    oracle_answer = oracle_tool._run(LAST_USER_PROMPT)
    
    console.print(f"\n[bold green]✨ Oracle Answer Retrieved:[/]\n{oracle_answer}\n")
    
    # 2. Invoke Interactive Tool manually
    proposed_rules = f"When asked '{LAST_USER_PROMPT}', the correct information is:\n{oracle_answer}\nAlways ensure this context is applied."
    
    teacher_tool = InteractiveTeacherTool()
    result = teacher_tool._run(agent_name=target_agent_key, proposed_rules=proposed_rules)

    # Automatically lower trust (doubt) because the local model failed
    active_model = get_active_model_name()
    new_thresh = hrf_manager.doubt(active_model)

    console.print("\n[bold green]✨ Feedback Learning Session Completed![/]")
    console.print(f"[dim]Note: Local model trust decreased. HRF threshold is now {new_thresh:.2f}[/dim]")
    console.print(Panel(result, title="[bold white]Feedback Output[/]", border_style="yellow"))

def execute_expand_pager():
    """Opens the LAST_FULL_OUTPUT in a native full-screen terminal pager."""
    global LAST_FULL_OUTPUT
    if not LAST_FULL_OUTPUT:
        console.print("[bold red]❌ No previous output to expand. Please run a query first.[/]")
        return
        
    with console.pager():
        console.print(LAST_FULL_OUTPUT)

def show_ollama_models():
    """Renders a beautiful table of installed and loaded models."""
    if not is_ollama_running():
        console.print("[bold red]❌ Ollama is not running.[/]")
        return
        
    with console.status("[bold yellow]📥 Fetching model statuses from Ollama daemon...[/]"):
        local = get_local_models()
        loaded = get_loaded_models()
        
    table = Table(title="🦙 Ollama Local Model Hub", header_style="bold magenta", border_style="cyan")
    table.add_column("Model Name", style="bold white")
    table.add_column("Status", justify="center")
    
    if not local:
        table.add_row("[italic yellow]No models found[/]", "")
    else:
        for model in local:
            # Match model name cleanly (e.g. qwen2.5-coder:latest vs qwen2.5-coder)
            is_active = any(model in l or l in model for l in loaded)
            status_text = "[bold green]ACTIVE (Loaded)[/]" if is_active else "[dim]IDLE (Cached)[/]"
            table.add_row(model, status_text)
            
    console.print(table)

def pull_ollama_model(model_name: str):
    """Pulls a new model via Ollama native progress indicator."""
    if not is_ollama_running():
        console.print("[bold red]❌ Ollama is not running. Please start the server first.[/]")
        return
        
    console.print(f"[bold yellow]📥 Pulling model '{model_name}' natively from Ollama Library...[/]")
    try:
        # Run natively so the user can see Ollama's dynamic progress bars
        subprocess.run(["ollama", "pull", model_name], check=True)
        console.print(f"\n[bold green]✅ Model '{model_name}' pulled successfully![/]")
    except subprocess.CalledProcessError:
        console.print(f"\n[bold red]❌ Failed to pull model '{model_name}'. Please verify the name is correct.[/]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/]")

def run_onboarding_wizard():
    """Starts a beautiful Python-native onboarding setup wizard if no config is found."""
    from prompt_toolkit import prompt
    from prompt_toolkit.styles import Style
    import shutil
    
    console.print("\n")
    banner = (
        "[bold cyan]========================================================================[/bold cyan]\n"
        "                 [bold yellow]🌟 Welcome to OmniAgent Onboarding! 🌟[/bold yellow]\n"
        "          Let's configure your system-wide Oracle fallback tool.\n"
        "[bold cyan]========================================================================[/bold cyan]\n"
    )
    console.print(Panel(banner, border_style="cyan"))
    
    # Scan for common AI CLI tools
    console.print("[bold blue]🔍 Scanning system path for available AI CLIs...[/bold blue]")
    candidates = ["gemini", "chatgpt", "claude"]
    found_clis = []
    
    for cli in candidates:
        if shutil.which(cli):
            found_clis.append(cli)
            console.print(f"  [bold green]➔ Found:[/] {cli} at [dim]{shutil.which(cli)}[/dim]")
            
    # Interactive selection using prompt_toolkit
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })
    
    oracle_cmd = "gemini --prompt" # Default fallback
    
    if found_clis:
        console.print("\n[bold yellow]Choose an AI CLI to act as your external Oracle fallback:[/bold yellow]")
        for i, cli in enumerate(found_clis):
            console.print(f"  [[bold cyan]{i}[/]] {cli}")
        console.print("  [[bold cyan]c[/]] Enter a custom command string")
        
        try:
            choice = prompt("Select option [default: 0] > ", style=style).strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold red]Onboarding cancelled. Falling back to default 'gemini --prompt'.[/bold red]")
            choice = "0"
            
        choice = choice or "0"
        
        if choice == 'c':
            try:
                custom_cmd = prompt("Enter your custom CLI command string (e.g. chatgpt -p) > ", style=style).strip()
            except (KeyboardInterrupt, EOFError):
                custom_cmd = ""
            oracle_cmd = custom_cmd if custom_cmd else "gemini --prompt"
        else:
            try:
                idx = int(choice)
                if idx < len(found_clis):
                    selected = found_clis[idx]
                    oracle_cmd = "gemini --prompt" if selected == "gemini" else selected
                else:
                    oracle_cmd = "gemini --prompt"
            except ValueError:
                oracle_cmd = "gemini --prompt"
    else:
        console.print("\n[bold yellow]No standard AI CLIs were found on your PATH.[/bold yellow]")
        try:
            custom_cmd = prompt("Enter your Oracle CLI command string [default: gemini --prompt] > ", style=style).strip()
        except (KeyboardInterrupt, EOFError):
            custom_cmd = ""
        oracle_cmd = custom_cmd if custom_cmd else "gemini --prompt"
        
    console.print(f"\n[bold green]✅ Configured Oracle Command:[/] [bold magenta]{oracle_cmd}[/bold magenta]")
    
    # Save to global config file
    try:
        with open(CONFIG_PATH, "w") as f:
            f.write("# OmniAgent Environment Configuration\n")
            f.write(f'ORACLE_CMD="{oracle_cmd}"\n')
        console.print(f"[bold green]💾 Saved configuration to {CONFIG_PATH} successfully![/bold green]\n")
        
        # Load dotenv to reload environment variables on the fly
        load_dotenv(CONFIG_PATH, override=True)
    except Exception as e:
        console.print(f"[bold red]❌ Failed to save configuration: {e}[/bold red]\n")

def run_interactive_cli():
    import os
    # 0. Onboarding Check
    if not os.path.exists(CONFIG_PATH) and not os.getenv("ORACLE_CMD"):
        run_onboarding_wizard()

    # 1. Startup Ollama Daemon Check & Boot
    import platform
    if not is_ollama_running():
        console.print("[bold yellow]⚠️ [Ollama] Server is not running. Attempting to start...[/]")
        with console.status("[bold green]🚀 [Ollama] Starting background daemon and verifying connection...[/]"):
            success, msg = start_ollama_server()
        if success:
            console.print("[bold green]✅ [Ollama] Daemon started successfully and verified online![/]")
        else:
            console.print(f"[bold red]❌ [Ollama] Could not start server: {msg}[/]")
            console.print("[yellow]Please run 'ollama serve' in another terminal, then restart this CLI.[/]")
            sys.exit(1)

    # Welcome banner
    welcome_text = Text()
    welcome_text.append("\n🤖 Omni-Agent\n", style="bold green")
    welcome_text.append("Operating System: ", style="dim")
    welcome_text.append(f"{platform.system()} {platform.release()}\n", style="bold cyan")
    welcome_text.append("Local Time: ", style="dim")
    welcome_text.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", style="bold yellow")
    welcome_text.append("Available Agents: ", style="dim")
    welcome_text.append("Router, Planner, Architect, Developer, Tester, Pentester, Security, Network\n", style="bold magenta")
    welcome_text.append("Special Tooling: ", style="dim")
    welcome_text.append("Gemini CLI Tool Integrated\n", style="bold blue")
    welcome_text.append("Interactive Help: ", style="dim")
    welcome_text.append("Type /models to view models or /help to view command list\n", style="bold green")
    welcome_text.append("Type '/quit', 'exit', or 'quit' to terminate.\n", style="italic")
    
    console.print(Panel(welcome_text, title="[bold green]OmniAgent[/]", border_style="green"))
    
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style
    import os
    history_file = os.path.join(os.path.expanduser("~"), ".omniagent_history")
    session = PromptSession(history=FileHistory(history_file))
    
    while True:
        try:
            user_input = session.prompt("\n✦ ❯ ")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Exiting. Goodbye![/]")
            break
            
        user_input = user_input.strip()
        if not user_input:
            continue
            
        if user_input.lower() in ['/quit', 'exit', 'quit']:
            console.print("[bold yellow]Powering down OmniAgent. Goodbye human[/]")
            break
            
        # Handle slash commands
        if user_input.startswith("/"):
            parts = user_input.split()
            cmd = parts[0].lower()
            
            if cmd == "/models":
                show_ollama_models()
                continue
            elif cmd == "/pull":
                if len(parts) < 2:
                    console.print("[bold red]❌ Usage: /pull <model_name>[/]")
                else:
                    pull_ollama_model(parts[1])
                continue
            elif cmd == "/debug":
                global DEBUG_MODE
                DEBUG_MODE = not DEBUG_MODE
                status_str = "[bold green]ON[/bold green]" if DEBUG_MODE else "[bold red]OFF[/bold red]"
                console.print(f"⚙️  [bold]Debug Mode (Verbose Agent Thoughts):[/bold] {status_str}")
                continue
            elif cmd in ["/teach", "/feedback"]:
                execute_teach_feedback()
                continue
            elif cmd == "/trust":
                active_model = get_active_model_name()
                new_thresh = hrf_manager.trust(active_model)
                console.print(f"[bold green]✅ Trust Increased for {active_model}. HRF threshold is now {new_thresh:.2f}[/]")
                continue
            elif cmd == "/doubt":
                active_model = get_active_model_name()
                new_thresh = hrf_manager.doubt(active_model)
                console.print(f"[bold yellow]⚠️ Trust Decreased for {active_model}. HRF threshold is now {new_thresh:.2f}[/]")
                continue
            elif cmd == "/hrf":
                active_model = get_active_model_name()
                thresh = hrf_manager.get_threshold(active_model)
                base = hrf_manager.get_baseline(active_model)
                console.print(Panel(
                    f"Active Model: [bold cyan]{active_model}[/bold cyan]\n"
                    f"Current Threshold: [bold magenta]{thresh:.2f}[/bold magenta]\n"
                    f"Baseline: [dim]{base:.2f}[/dim]\n\n"
                    f"If a prompt's risk score exceeds this threshold, the query defaults to the Oracle.\n"
                    f"Use [bold cyan]/trust[/] to raise the threshold and [bold yellow]/doubt[/] to lower it.",
                    title="Hallucination Risk Factor (HRF) Status", border_style="blue"
                ))
                continue
            elif cmd == "/expand":
                execute_expand_pager()
                continue
            elif cmd in ["/help", "/commands"]:
                console.print(Panel(
                    "Available Slash Commands:\n"
                    "  [bold cyan]/models[/]        Show downloaded & loaded Ollama models\n"
                    "  [bold cyan]/pull <name>[/]   Download a new model from the Ollama library\n"
                    "  [bold cyan]/debug[/]         Toggle verbose agent thoughts & details\n"
                    "  [bold cyan]/expand[/]        View the last truncated output in a full-screen pager\n"
                    "  [bold cyan]/teach[/]         Flag the last response as incomplete/incorrect & teach the agent\n"
                    "  [bold cyan]/trust[/]         Trust the active model more (raises Oracle threshold)\n"
                    "  [bold cyan]/doubt[/]         Trust the active model less (lowers Oracle threshold)\n"
                    "  [bold cyan]/hrf[/]           Show current Hallucination Risk Factor settings\n"
                    "  [bold cyan]/quit[/]          Terminate the CLI session",
                    title="Help & Commands", border_style="blue"
                ))
                continue
            else:
                console.print(f"[bold red]❌ Unknown command: {cmd}. Type /help to list commands.[/]")
                continue

        # 1. Scrutinize prompt for missing context
        with console.status("[bold yellow]🤔 [Router] Scrutinizing prompt context...[/]"):
            scrutiny_result = scrutinize_prompt(user_input)
            
        if scrutiny_result != "PROCEED":
            console.print(f"[bold yellow]🤔 [Router Scrutiny]:[/] {scrutiny_result}")
            try:
                style = Style.from_dict({'prompt': 'ansicyan bold'})
                clarification = session.prompt("Provide clarification ❯ ", style=style).strip()
                if clarification:
                    user_input = f"{user_input}\n\nUser Clarification: {clarification}"
                else:
                    console.print("[dim]No clarification provided. Proceeding with original prompt...[/dim]")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold red]Cancelled prompt.[/bold red]")
                continue

        # 2. Route the request
        route = route_request(user_input)
        
        # 3. Execute workflow
        try:
            execute_crew_workflow(route, user_input)
        except Exception as e:
            console.print(f"[bold red]Execution Error: {e}[/]")

if __name__ == "__main__":
    run_interactive_cli()
