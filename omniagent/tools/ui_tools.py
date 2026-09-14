from langchain.tools import BaseTool
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

class AskUserTool(BaseTool):
    name: str = "ask_user"
    description: str = (
        "Ask the user a question in the terminal to gather preferences, clarify requirements, "
        "or make decisions. Execution will pause until the user provides an answer."
    )

    def _run(self, question: str) -> str:
        console.print(f"\n[bold yellow]🤖 Agent Needs Input:[/bold yellow]")
        console.print(f"[white]{question}[/white]")
        
        try:
            answer = Prompt.ask("[bold cyan]Your Answer[/bold cyan]")
            return f"User replied: {answer}"
        except Exception as e:
            return f"Failed to get user input: {e}"

class UpdateTopicTool(BaseTool):
    name: str = "update_topic"
    description: str = (
        "Manages your narrative flow. Call this to output a stylized status panel to the terminal "
        "when starting a new logical phase, shifting strategic intent, or providing a summary of work."
    )

    def _run(self, title: str, summary: str, strategic_intent: str) -> str:
        try:
            content = f"[bold white]{summary}[/bold white]\n\n[italic cyan]Intent: {strategic_intent}[/italic cyan]"
            panel = Panel(
                content,
                title=f"[bold magenta]✨ {title}[/bold magenta]",
                expand=False,
                border_style="magenta"
            )
            console.print(panel)
            return "Successfully updated the user on the current topic."
        except Exception as e:
            return f"Failed to update topic: {e}"
