import sys
import warnings

# Suppress Pydantic v1/v2 mixing warnings from older crewai/langchain versions
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from omnihub.cli import run_interactive_cli

if __name__ == "__main__":
    try:
        run_interactive_cli()
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
        sys.exit(0)
