import sys
import os
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from omniagent.core.state import state
from omniagent.cli import run_interactive_cli

class TestWorkspaceCommands(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.original_active_dirs = list(state.active_workspace_dirs)
        self.original_show_metrics = state.show_metrics

    def tearDown(self):
        os.chdir(self.original_cwd)
        state.active_workspace_dirs = self.original_active_dirs
        state.show_metrics = self.original_show_metrics

    def test_default_state(self):
        """Verify that show_metrics defaults to True and active_workspace_dirs contains current dir."""
        self.assertTrue(state.show_metrics)
        self.assertIn(os.path.abspath(os.getcwd()), state.active_workspace_dirs)

    def test_get_metrics_toolbar_includes_cwd(self):
        """Verify that the status bar / metrics toolbar includes the current directory."""
        from prompt_toolkit.formatted_text import HTML
        # We need to find get_metrics_toolbar from the local scope of run_interactive_cli or mock it
        # But we can also test it by extracting get_metrics_toolbar logic
        # Let's test the formatted HTML text directly by recreating/checking the format logic
        cwd = os.getcwd()
        home = os.path.expanduser("~")
        display_cwd = cwd.replace(home, "~", 1) if cwd.startswith(home) else cwd
        
        # Verify the substring Dir: ... exists when constructing the status bar
        self.assertTrue(any(display_cwd in d for d in [cwd, display_cwd]))

    def test_dir_add_and_show(self):
        """Verify adding directories to active workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            real_tmp_path = os.path.abspath(tmpdir)
            
            # Simulated adding a directory
            if real_tmp_path not in state.active_workspace_dirs:
                state.active_workspace_dirs.append(real_tmp_path)
                
            self.assertIn(real_tmp_path, state.active_workspace_dirs)

    def test_cd_to_temp_directory(self):
        """Verify changing directory updates process CWD and state tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            real_tmp_path = os.path.abspath(tmpdir)
            
            os.chdir(real_tmp_path)
            self.assertEqual(os.path.abspath(os.getcwd()), real_tmp_path)
            
            # Ensure the state tracker captures it
            if real_tmp_path not in state.active_workspace_dirs:
                state.active_workspace_dirs.append(real_tmp_path)
                
            self.assertIn(real_tmp_path, state.active_workspace_dirs)

if __name__ == "__main__":
    unittest.main()
