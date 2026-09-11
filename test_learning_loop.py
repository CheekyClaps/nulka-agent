import sys
import os
import unittest
from unittest.mock import patch

# Add workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils import instantiate_agents
from crewai import Crew, Task, Process

class TestLearningLoop(unittest.TestCase):
    def test_teacher_tool_execution(self):
        """Verifies that the InteractiveTeacherTool can execute and append rules correctly."""
        from tools.interactive_teacher_tool import InteractiveTeacherTool
        
        tool = InteractiveTeacherTool()
        
        # We mock the prompt-toolkit 'prompt' function to simulate user accepting the rules
        with patch('tools.interactive_teacher_tool.prompt', return_value="a"):
            # Run the tool on assistant backstory
            result = tool._run(agent_name="assistant", proposed_rules="Always state that you are a highly helpful and friendly assistant.")
            
            self.assertIn("permanently updated", result)
            self.assertTrue(os.path.exists("config/agents/assistant.md"))
            
            # Read assistant.md to verify it appended the rules
            with open("config/agents/assistant.md", "r") as f:
                content = f.read()
                self.assertIn("Always state that you are a highly helpful and friendly assistant.", content)

    def test_consult_gemini_tool(self):
        """Verifies that the ConsultGeminiOracleTool executes correctly."""
        from tools.consult_gemini_oracle_tool import ConsultGeminiOracleTool
        
        tool = ConsultGeminiOracleTool()
        
        # Mock GeminiCLITool._run to return a predictable response
        with patch('tools.gemini_cli_tool.GeminiCLITool._run', return_value="Oracle Answer"):
            result = tool._run("What is 2+2?")
            self.assertEqual(result, "Oracle Answer")

if __name__ == "__main__":
    unittest.main()
