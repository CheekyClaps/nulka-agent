import os
from prompt_toolkit.formatted_text import HTML

from omniagent.core.state import state
from omniagent.utils import get_active_model_name
from omniagent.hrf_manager import hrf_manager

class StatusBar:
    @staticmethod
    def get_toolbar():
        """Returns the formatted bottom toolbar for PromptToolkit."""
        if not state.show_metrics:
            return None

        # Retrieve active models and thresholds
        active_local = get_active_model_name()
        hrf = hrf_manager.get_threshold(active_local)
        
        # Determine Oracle cmd (Fallback)
        oracle_cmd = os.getenv("ORACLE_CMD", "gemini")
        # Just extract the base binary name for cleaner display
        oracle_model = oracle_cmd.split()[0] if oracle_cmd else "None"
        
        # Execution metrics
        route_info = f"Route: {state.last_route}" if state.last_route else "Route: N/A"
        time_info = f"{state.last_execution_time:.2f}s" if state.last_execution_time else "N/A"
        
        # Working Directory Formatting
        cwd = os.getcwd()
        home = os.path.expanduser("~")
        display_cwd = cwd.replace(home, "~", 1) if cwd.startswith(home) else cwd
        
        # Build the HTML formatted string for the toolbar
        return HTML(
            f' <b>Status</b> | '
            f'Time: <ansiyellow>{time_info}</ansiyellow> | '
            f'{route_info} | '
            f'Local: <ansicyan>{active_local}</ansicyan> | '
            f'Oracle: <ansimagenta>{oracle_model}</ansimagenta> | '
            f'HRF: <ansired>{hrf:.1f}</ansired> | '
            f'Dir: <ansigreen>{display_cwd}</ansigreen> '
        )
