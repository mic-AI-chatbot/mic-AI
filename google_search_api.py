import os
import httpx
import logging
from mic.config import GOOGLE_API_KEY, GOOGLE_CSE_ID

logger = logging.getLogger(__name__)

async def google_web_search(query: str, num_results: int = 5) -> dict:
    """
    Performs a web search using the Google Custom Search API.

    Args:
        query (str): The search query.
        num_results (int): The number of search results to return (max 10).

    Returns:
        dict: A dictionary containing search results or an error message.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        error_msg = "Google API Key or Custom Search Engine ID is not configured."
        logger.error(error_msg)
        return {"error": error_msg}

    if not query:
        return {"error": "Search query cannot be empty."}

    if not (1 <= num_results <= 10):
        return {"error": "Number of results must be between 1 and 10."}

    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, params=params, timeout=10)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            data = response.json()

            if "error" in data:
                error_msg = f"Google Search API error: {data['error'].get('message', 'Unknown error')}"
                logger.error(error_msg, extra={"api_error": data['error']})
                return {"error": error_msg}

            search_results = []
            if "items" in data:
                for item in data["items"]:
                    search_results.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet")
                    })
            
            return {"query": query, "results": search_results}

    except httpx.RequestError as e:
        error_msg = f"Network or HTTP error during Google Search: {e}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}
    except httpx.HTTPStatusError as e:
        error_msg = f"Google Search API returned an error status {e.response.status_code}: {e.response.text}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred during Google Search: {e}"
        logger.error(error_msg, exc_info=True)
        return {"error": error_msg}
