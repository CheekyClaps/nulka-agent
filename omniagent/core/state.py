import sys
import os

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
