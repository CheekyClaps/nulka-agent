import os
from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

console = Console()

def get_bottom_toolbar():
    return HTML(' <b>[A]</b> Accept   <b>[R]</b> Reject   <b>[Type Text]</b> Augment / Edit   <b>[Ctrl+C]</b> Cancel ')

class TeacherToolInput(BaseModel):
    agent_name: str = Field(description="The name of the agent whose instructions need to be updated (e.g., 'developer', 'tester', 'assistant').")
    proposed_rules: str = Field(description="The new instructions, rules, or lessons learned to persistently append to the agent's backstory markdown file.")

class InteractiveTeacherTool(BaseTool):
    name: str = "interactive_teacher_tool"
    description: str = (
        "Updates an agent's backstory markdown file with new instructions, lessons, or rules learned. "
        "This tool prompts the user interactively in the CLI to approve, reject, or edit the proposed changes before they are saved."
    )
    args_schema: Type[BaseModel] = TeacherToolInput

    def _run(self, agent_name: str, proposed_rules: str) -> str:
        """Executes the tool to interactively update agent backstory."""
        # Normalize agent name to find file
        agent_name_clean = agent_name.lower().replace(".md", "").strip()
        valid_agents = ['planner', 'systems_engineer', 'developer', 'tester', 'pentester', 'security_officer', 'network_engineer', 'assistant']

        if agent_name_clean not in valid_agents:
            console.print(f"\n[bold red]⚠️  Teacher Agent proposed an invalid agent name: '{agent_name}'.[/bold red]")
            console.print(f"Available agents to update: {', '.join(valid_agents)}")
            
            from omniagent.core.state import ask_user_safe
            agent_name_clean = ask_user_safe(
                "Please enter the correct agent name to update (or leave blank to skip) > ",
                style_dict={'prompt': 'ansiyellow bold'}
            ).lower().replace(".md", "")
            
            if not agent_name_clean:
                return "User interrupted the interactive update process. No changes were made."

        if not agent_name_clean or agent_name_clean not in valid_agents:
            return f"Skipped backstory update due to invalid agent selection: '{agent_name_clean}'."

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "config", "agents", f"{agent_name_clean}.md")

        if not os.path.exists(file_path):
            return f"Error: Agent backstory file not found at {file_path}."

        console.print("\n")
        panel_content = (
            f"[bold cyan]Agent to Update:[/bold cyan] {agent_name_clean}.md\n\n"
            f"[bold green]Proposed Rules / Lessons learned:[/bold green]\n"
            f"{proposed_rules}\n"
        )
        console.print(Panel(
            panel_content, 
            title="[bold yellow]🎓 Learning Loop: Teacher Agent Proposal[/bold yellow]", 
            border_style="yellow"
        ))

        from omniagent.core.state import ask_user_safe
        user_decision = ask_user_safe(
            "Feedback Action ([A]ccept / [R]eject / Type custom rules) ❯ ",
            style_dict={'prompt': 'ansicyan bold'}
        )

        if not user_decision:
            return "No decision received or process interrupted. Skipping update."

        decision_lower = user_decision.lower()

        if decision_lower in ['r', 'reject', 'no']:
            return "User rejected the proposed backstory update. No changes were made."

        rules_to_append = proposed_rules
        status_message = "Successfully accepted proposed backstory update."

        if decision_lower not in ['a', 'accept', 'yes', 'y']:
            # The user typed their own custom augmented rules
            rules_to_append = user_decision
            status_message = "Successfully updated backstory with user-augmented custom rules."

        # Append rules to file
        try:
            with open(file_path, "a") as f:
                # Ensure spacing
                f.write(f"\n\n### 🎓 Learned Rules & Guidelines (Updated {os.getenv('USER', 'Self-Learning Loop')}):\n")
                f.write(f"{rules_to_append.strip()}\n")
            
            # Version Control: Automatically commit the change to git
            import subprocess
            try:
                subprocess.run(["git", "add", file_path], check=True, capture_output=True)
                commit_msg = f"OmniAgent Learning Loop: Update {agent_name_clean}.md"
                subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
                status_message += f"\n[bold green]📦 Version control active: Changes safely committed to git repository.[/bold green]"
            except Exception as git_e:
                status_message += f"\n[bold yellow]⚠️ Could not commit to git (is git initialized?): {git_e}[/bold yellow]"

            return f"{status_message}\nFile {file_path} has been permanently updated."
        except Exception as e:
            return f"Failed to write to file {file_path}: {e}"
