import logging
from typing import Dict, Any
from tools.base_tool import BaseTool
from mic.google_search_api import google_web_search # Import the actual search function
import asyncio # Import asyncio for running async function

logger = logging.getLogger(__name__)

class WebSearchTool(BaseTool):
    """
    A tool for performing web searches using the Google Web Search tool.
    """
    def __init__(self, tool_name: str = "web_search_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Performs a web search using the Google Web Search tool and returns the results."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to find information on the web."},
                "num_results": {"type": "integer", "description": "The number of search results to return (max 10).", "default": 5}
            },
            "required": ["query"]
        }

    def execute(self, query: str, num_results: int = 5, **kwargs: Any) -> Dict:
        """
        Performs a web search using the Google Web Search tool.
        """
        if not query:
            error_msg = "'query' cannot be empty."
            logger.error(error_msg)
            return {"error": error_msg}

        try:
            # Call the actual asynchronous google_web_search function
            # Since execute is synchronous, we need to run the async function
            search_result = asyncio.run(google_web_search(query=query, num_results=num_results))
            
            if "error" in search_result:
                # The google_web_search function already logs its errors
                return {"error": f"Web search failed: {search_result['error']}"}
            
            return {"search_results": search_result}
        except Exception as e:
            error_msg = f"An unexpected error occurred during web search execution: {e}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
