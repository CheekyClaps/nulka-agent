import sys
import os
import unittest
from unittest.mock import patch

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestLearningLoop(unittest.TestCase):
    def test_teacher_tool_execution(self):
        """Verifies that the InteractiveTeacherTool can execute and append rules correctly."""
        from omniagent.tools.interactive_teacher_tool import InteractiveTeacherTool
        
        tool = InteractiveTeacherTool()
        
        # Read the original content of assistant.md using an absolute path to match tool logic
        assistant_path = os.path.abspath("omniagent/config/agents/assistant.md")
        with open(assistant_path, "r") as f:
            original_content = f.read()
            
        try:
            # We mock 'ask_user_safe' to simulate user accepting the rules,
            # and patch subprocess.run to prevent actual git commits during testing.
            with patch('omniagent.core.state.ask_user_safe', return_value="a"), \
                 patch('subprocess.run') as mock_run:
                 
                # Run the tool on assistant backstory
                result = tool._run(agent_name="assistant", proposed_rules="Always state that you are a highly helpful and friendly assistant.")
                
                self.assertIn("permanently updated", result)
                self.assertTrue(os.path.exists(assistant_path))
                
                # Read assistant.md to verify it appended the rules
                with open(assistant_path, "r") as f:
                    content = f.read()
                self.assertIn("Always state that you are a highly helpful and friendly assistant.", content)
                
                # Verify git commands were invoked
                mock_run.assert_any_call(["git", "add", assistant_path], check=True, capture_output=True)
                
        finally:
            # Restore the original file content
            with open(assistant_path, "w") as f:
                f.write(original_content)

    def test_consult_oracle_tool(self):
        """Verifies that the ConsultOracleTool executes correctly."""
        from omniagent.tools.consult_oracle_tool import ConsultOracleTool
        
        tool = ConsultOracleTool()
        
        # Mock OracleCLITool._run to return a predictable response
        with patch('omniagent.tools.oracle_cli_tool.OracleCLITool._run', return_value="Oracle Answer"):
            result = tool._run("What is 2+2?")
            self.assertEqual(result, "Oracle Answer")

    def test_execute_teach_feedback_oracle_fail(self):
        """Verifies that execute_teach_feedback handles Oracle failures by prompting for manual rules."""
        from omniagent.cli import execute_teach_feedback
        from omniagent.core.state import state
        
        # Save original state
        orig_prompt = state.last_user_prompt
        orig_route = state.last_route
        
        try:
            state.last_user_prompt = "some query"
            state.last_route = "GENERAL"
            
            # Patch OracleCLITool._run to return an error/timeout string
            # Patch ask_user_safe to return our custom rule
            # Patch doubt to return a float (5.0) so format formatting :.2f doesn't fail on MagicMock
            with patch('omniagent.tools.oracle_cli_tool.OracleCLITool._run', return_value="Error: Oracle CLI query timed out after 60 seconds."), \
                 patch('omniagent.core.state.ask_user_safe', return_value="My custom manual rule") as mock_ask, \
                 patch('omniagent.tools.interactive_teacher_tool.InteractiveTeacherTool._run', return_value="Success") as mock_teacher_run, \
                 patch('omniagent.cli.hrf_manager.doubt', return_value=5.0) as mock_doubt:
                 
                execute_teach_feedback()
                
                # Check that fallback input was called
                mock_ask.assert_called_once()
                # Check that InteractiveTeacherTool._run was called with the custom rule we entered!
                mock_teacher_run.assert_called_once_with(
                    agent_name="assistant",
                    proposed_rules="When asked 'some query', the correct guideline/action is:\nMy custom manual rule\nAlways ensure this context is applied."
                )
                # Check that doubt was called
                mock_doubt.assert_called_once()
                
        finally:
            state.last_user_prompt = orig_prompt
            state.last_route = orig_route

    def test_execute_teach_feedback_oracle_success(self):
        """Verifies that execute_teach_feedback uses Oracle answer directly when successful."""
        from omniagent.cli import execute_teach_feedback
        from omniagent.core.state import state
        
        orig_prompt = state.last_user_prompt
        orig_route = state.last_route
        
        try:
            state.last_user_prompt = "another query"
            state.last_route = "CODE"
            
            # Patch hrf_manager.doubt to return 5.0 to support :.2f float formatting
            with patch('omniagent.tools.oracle_cli_tool.OracleCLITool._run', return_value="Oracle solution here"), \
                 patch('omniagent.tools.interactive_teacher_tool.InteractiveTeacherTool._run', return_value="Success") as mock_teacher_run, \
                 patch('omniagent.cli.hrf_manager.doubt', return_value=5.0) as mock_doubt:
                 
                execute_teach_feedback()
                
                mock_teacher_run.assert_called_once_with(
                    agent_name="developer",
                    proposed_rules="When asked 'another query', the correct information is:\nOracle solution here\nAlways ensure this context is applied."
                )
                mock_doubt.assert_called_once()
                
        finally:
            state.last_user_prompt = orig_prompt
            state.last_route = orig_route

if __name__ == "__main__":
    unittest.main()
