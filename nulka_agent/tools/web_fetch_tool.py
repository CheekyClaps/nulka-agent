import requests
from bs4 import BeautifulSoup
from langchain.tools import BaseTool

class WebFetchTool(BaseTool):
    name: str = "web_fetch"
    description: str = (
        "Fetches and extracts the textual information from a specific URL. "
        "Use this after a web search to read the full content of a page, documentation, or repository. "
        "Provides the raw text extracted from the HTML."
    )

    def _run(self, url: str) -> str:
        """Fetches and parses the text content of a given URL.
        
        Args:
            url: The HTTP/HTTPS URL to fetch.
        """
        if not url.startswith("http"):
            return "Error: Please provide a valid HTTP or HTTPS URL."

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
                script_or_style.extract()
                
            text = soup.get_text(separator='\n')
            
            # Collapse multiple newlines/spaces
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Truncate to avoid context window blowouts (~8000 characters is a safe limit for local models)
            max_chars = 8000
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n... [Content truncated to {max_chars} characters to fit context window]"
                
            return text
        except requests.exceptions.RequestException as e:
            return f"Failed to fetch URL: {e}"
        except Exception as e:
            return f"An error occurred while parsing the page: {e}"
