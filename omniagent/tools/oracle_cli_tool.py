import os
import subprocess
from langchain.tools import BaseTool

class OracleCLITool(BaseTool):
    name: str = "oracle_cli_tool"
    description: str = (
        "Executes a localized command using the configured system AI CLI tool (e.g. gemini, chatgpt, claude) "
        "to leverage external LLM intelligence. Use this tool to consult the Oracle for high-level guidance, "
        "framework insights, complex bug-fixing strategies, or automated system audits."
    )

    def _run(self, prompt: str) -> str:
        """Executes the configured AI CLI command and captures the output.
        
        Args:
            prompt: The text prompt/query to send to the Oracle CLI tool.
        """
        # Inject Universal Ground Rules if they exist
        rules_path = os.path.expanduser("~/.omniagent_rules.md")
        if os.path.exists(rules_path):
            try:
                with open(rules_path, "r") as f:
                    content = f.read().strip()
                    if content:
                        prompt = f"### 🌍 Universal Ground Rules:\n{content}\n\n### User Query:\n{prompt}"
            except Exception:
                pass

        # Fetch configured oracle command from environment (with default fallback)
        oracle_cmd_str = os.getenv("ORACLE_CMD", "gemini --prompt")
        
        # Split command to safety parameters
        cmd_parts = oracle_cmd_str.split()
        cmd = cmd_parts + [prompt]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[Errors/Warnings]:\n{result.stderr}"
                
            if result.returncode != 0:
                return f"Oracle CLI execution returned error code {result.returncode}.\nOutput:\n{output}"
                
            return output.strip() if output.strip() else "Oracle CLI executed successfully but returned empty output."
            
        except FileNotFoundError:
            base_bin = cmd_parts[0] if cmd_parts else "oracle"
            return (
                f"Error: The configured Oracle CLI command '{base_bin}' was not found.\n"
                f"Please run the onboarding wizard or verify that '{base_bin}' is installed and on your PATH."
            )
        except subprocess.TimeoutExpired:
            return "Error: Oracle CLI query timed out after 60 seconds."
        except Exception as e:
            return f"An unexpected error occurred during Oracle CLI tool execution: {e}"
