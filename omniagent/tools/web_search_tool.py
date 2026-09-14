import json
from langchain.tools import BaseTool
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Performs a web search to find information across the internet. "
        "Returns synthesized search results with URLs. "
        "Use this for broad research, finding up-to-date documentation, or troubleshooting."
    )

    def _run(self, query: str) -> str:
        """Executes the web search using DuckDuckGo.
        
        Args:
            query: The search query.
        """
        if DDGS is None:
            return "Error: duckduckgo-search package is not installed."
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            
            if not results:
                return "No search results found."
            
            formatted_results = []
            for i, res in enumerate(results, 1):
                title = res.get('title', 'No Title')
                href = res.get('href', 'No URL')
                body = res.get('body', 'No snippet')
                formatted_results.append(f"[{i}] {title}\nURL: {href}\nSnippet: {body}\n")
                
            return "\n".join(formatted_results)
        except Exception as e:
            return f"Web search failed: {e}"
