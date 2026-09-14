import os
import subprocess
from langchain.tools import BaseTool

class RunShellCommandTool(BaseTool):
    name: str = "run_shell_command"
    description: str = (
        "Executes a given shell command as a subprocess. "
        "Useful for running tests, installing dependencies, or building projects."
    )

    def _run(self, command: str, dir_path: str = ".") -> str:
        """Executes the shell command.
        
        Args:
            command: The exact bash command to execute.
            dir_path: The directory to run the command in.
        """
        try:
            result = subprocess.run(
                command,
                cwd=dir_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
                
            if result.returncode != 0:
                output += f"\nCommand failed with return code {result.returncode}"
                
            # Truncate to protect context window
            if len(output) > 6000:
                output = output[:6000] + "\n... [Output truncated to 6000 characters]"
                
            return output.strip() if output.strip() else "Command executed successfully with no output."
        except subprocess.TimeoutExpired:
            return "Command execution timed out after 120 seconds."
        except Exception as e:
            return f"Error executing command: {e}"
