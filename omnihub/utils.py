import os
import time
import yaml
import platform
from datetime import datetime
from crewai import Agent
from langchain_community.llms import Ollama
from omnihub.tools.oracle_cli_tool import OracleCLITool
from omnihub.tools.interactive_teacher_tool import InteractiveTeacherTool
from omnihub.tools.consult_oracle_tool import ConsultOracleTool

# Setup standard local LLM
ollama_llm = Ollama(model="qwen2.5-coder:latest", base_url="http://localhost:11434")

def get_system_context():
    """Gathers real-time environmental context metrics for the Router agent."""
    # 1. System Time
    now = datetime.now()
    current_time = now.strftime("%A, %B %d, %Y - %I:%M:%S %p")
    
    # 2. Operating System Details
    system_os = platform.system()
    system_platform = platform.platform()
    
    # 3. Geolocation via System Timezone Info
    timezone = "UTC"
    try:
        if os.path.exists("/etc/timezone"):
            with open("/etc/timezone", "r") as f:
                timezone = f.read().strip()
        elif hasattr(time, "tzname"):
            timezone = "/".join(time.tzname)
    except Exception:
        pass
        
    return {
        "current_time": current_time,
        "system_os": system_os,
        "system_platform": system_platform,
        "geolocation": timezone
    }

def load_agent_configs(agents_yaml_path="config/agents.yaml"):
    """Loads agents.yaml and pre-injects backstories from linked .md files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agents_yaml_path = os.path.join(base_dir, agents_yaml_path)

    if not os.path.exists(agents_yaml_path):
        raise FileNotFoundError(f"Configuration file not found: {agents_yaml_path}")
        
    with open(agents_yaml_path, "r") as f:
        agents_data = yaml.safe_load(f)
        
    context = get_system_context()
    
    for agent_key, agent_config in agents_data.items():
        backstory_file = agent_config.get("backstory_file")
        if backstory_file:
            # Resolve relative path safely
            backstory_file = os.path.join(base_dir, backstory_file.strip())
            if os.path.exists(backstory_file):
                with open(backstory_file, "r") as bf:
                    raw_backstory = bf.read()
                # Dynamically inject system variables into the backstory
                try:
                    formatted_backstory = raw_backstory.format(
                        system_os=context["system_os"],
                        system_platform=context["system_platform"],
                        current_time=context["current_time"],
                        geolocation=context["geolocation"]
                    )
                except KeyError as ke:
                    # Fallback in case the markdown contains other curly brace patterns
                    # We only replace known variables
                    formatted_backstory = raw_backstory
                    for var in ["system_os", "system_platform", "current_time", "geolocation"]:
                        formatted_backstory = formatted_backstory.replace(f"{{{var}}}", str(context.get(var, "")))
                
                agent_config["backstory"] = formatted_backstory
            else:
                agent_config["backstory"] = "Backstory markdown file not found."
                
    return agents_data

def instantiate_agents(custom_tools=None):
    """Instantiates and returns the dictionary of initialized CrewAI Agent objects."""
    if custom_tools is None:
        custom_tools = []
        
    # Standardize our local Oracle CLI Tool
    oracle_cli_tool = OracleCLITool()
    interactive_teacher_tool = InteractiveTeacherTool()
    consult_oracle_tool = ConsultOracleTool()
    
    configs = load_agent_configs()
    agents = {}
    
    # Distribute tools to relevant agents
    for agent_key, config in configs.items():
        # Setup tools for each agent based on their requirements
        agent_tools = []
        
        if agent_key in ["developer", "systems_engineer", "pentester", "network_engineer", "external_oracle"]:
            # These specialized profiles get the Oracle CLI Tool
            agent_tools.append(oracle_cli_tool)
            
        if agent_key == "teacher":
            # The educational director gets the interactive teaching tool and Oracle Consultant tool
            agent_tools.extend([interactive_teacher_tool, consult_oracle_tool])
            
        # Give workspace access tools if passed, BUT explicitly deny them to the external_oracle
        if custom_tools and agent_key != "external_oracle":
            agent_tools.extend(custom_tools)
            
        # The teacher and router agents are allowed to delegate tasks to others
        allow_delegation = True if agent_key in ["router", "teacher"] else False
            
        agents[agent_key] = Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=True,
            allow_delegation=allow_delegation,
            tools=agent_tools,
            llm=ollama_llm
        )
        
    return agents

def is_ollama_running(url="http://localhost:11434"):
    """Checks if the local Ollama server is running and responding."""
    import requests
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def start_ollama_server():
    """Starts the local Ollama server in the background."""
    import subprocess
    import requests
    if is_ollama_running():
        return True, "Ollama is already running."
        
    try:
        # Start 'ollama serve' in background
        # We redirect stdout/stderr to devnull to prevent blocking or terminal spam
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        
        # Poll the server until it responds (max 15 seconds)
        for _ in range(15):
            time.sleep(1)
            if is_ollama_running():
                return True, "Ollama server started successfully."
        return False, "Failed to start Ollama server (timeout expired)."
    except Exception as e:
        return False, f"Error starting Ollama server: {e}"

def get_local_models():
    """Queries the local Ollama API to list all installed/downloaded models."""
    import requests
    if not is_ollama_running():
        return []
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []

def get_loaded_models():
    """Queries the local Ollama API to list currently active/loaded models in memory."""
    import requests
    if not is_ollama_running():
        return []
    try:
        response = requests.get("http://localhost:11434/api/ps", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        pass
    return []

