from langchain.tools import BaseTool
from omnihub.tools.oracle_cli_tool import OracleCLITool

class ConsultOracleTool(BaseTool):
    name: str = "consult_oracle"
    description: str = (
        "Delegates a query to the external Consultant (Oracle) to obtain "
        "the correct answer, high-quality guidelines, framework insights, or code corrections "
        "when local models fail or are uncertain."
    )

    def _run(self, query: str) -> str:
        """Executes a query to the configured Oracle on behalf of the Teacher Agent."""
        oracle_tool = OracleCLITool()
        return oracle_tool._run(query)
