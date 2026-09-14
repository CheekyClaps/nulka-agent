import sys
import os
import json

class SessionState:
    """Manages global application state cleanly without using Python globals."""
    def __init__(self):
        self.last_user_prompt: str | None = None
        self.last_route: str | None = None
        self.last_full_output: str | None = None
        self.last_execution_time: float = 0.0
        self.show_metrics: bool = True
        self.active_workspace_dirs: list[str] = [os.path.abspath(os.getcwd())]
        self.vim_mode: bool = False
        self.history: list[dict] = []
        
        # Attempt to load recoverable session if it exists in the current workspace
        self.load_session()

    def get_workspace_dir(self) -> str:
        """Returns the local workspace .omniagent directory if it exists, otherwise falls back to a global directory."""
        cwd = os.path.abspath(os.getcwd())
        local_dir = os.path.join(cwd, ".omniagent")
        if os.path.exists(local_dir):
            return local_dir
        
        # Fallback to global user directory for uninitialized workspaces
        global_dir = os.path.expanduser("~/.omniagent/global_workspace")
        os.makedirs(global_dir, exist_ok=True)
        return global_dir

    def load_session(self):
        """Loads session progress from the active workspace."""
        workspace_dir = self.get_workspace_dir()
        session_file = os.path.join(workspace_dir, "session.json")
        
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
                    # Optionally restore the last run state for /expand or /teach to work on boot
                    if self.history:
                        last_entry = self.history[-1]
                        self.last_user_prompt = last_entry.get("prompt")
                        self.last_route = last_entry.get("route")
                        self.last_full_output = last_entry.get("output")
            except Exception:
                pass # Fail silently if corrupted

    def save_session(self):
        """Saves current progress to the active workspace."""
        workspace_dir = self.get_workspace_dir()
        session_file = os.path.join(workspace_dir, "session.json")
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump({"history": self.history}, f, indent=4)
        except Exception:
            pass

    def save_output_cache(self, output: str):
        """Saves the raw output of the last turn to a cache file so agents can read it without re-executing."""
        workspace_dir = self.get_workspace_dir()
        cache_file = os.path.join(workspace_dir, "last_output_cache.txt")
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(output)
        except Exception:
            pass

    def append_interaction(self, prompt: str, route: str, output: str):
        """Logs an interaction to history and flushes to disk."""
        self.last_user_prompt = prompt
        self.last_route = route
        self.last_full_output = output
        
        self.history.append({
            "prompt": prompt,
            "route": route,
            "output": output
        })
        self.save_session()
        self.save_output_cache(output)

# Singleton instance to be shared across the application run
state = SessionState()

def ask_user_safe(prompt_text: str, default: str = "", style_dict: dict = None) -> str:
    """
    A bulletproof interactive prompt that automatically detects the terminal capabilities.
    Falls back to standard python input() if prompt_toolkit or CPR is unavailable.
    """
    use_fallback = not sys.stdout.isatty() or not sys.stdin.isatty()
    
    if use_fallback:
        try:
            return input(prompt_text).strip()
        except (KeyboardInterrupt, EOFError):
            return ""
            
    # Use advanced prompt toolkit
    from prompt_toolkit import prompt
    from prompt_toolkit.styles import Style
    
    try:
        if style_dict:
            prompt_style = Style.from_dict(style_dict)
            return prompt(prompt_text, style=prompt_style).strip()
        return prompt(prompt_text).strip()
    except Exception:
        # Final fail-safe if prompt toolkit throws internal terminal errors
        try:
            return input(prompt_text).strip()
        except (KeyboardInterrupt, EOFError):
            return ""
