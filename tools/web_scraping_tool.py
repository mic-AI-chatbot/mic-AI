import json
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import logging
from typing import Union, List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class WebScrapingTool(BaseTool):
    """
    A tool for scraping content from web pages, supporting both static and dynamic sites.
    """

    def __init__(self, tool_name: str = "web_scraping_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Scrapes content from web pages using CSS selectors, supporting static and dynamic sites."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the web page to scrape."},
                "selector": {"type": "string", "description": "The CSS selector to target specific elements."},
                "attribute": {
                    "type": "string", 
                    "description": "Optional. The attribute to extract from the selected elements (e.g., 'href', 'src')."
                },
                "dynamic": {
                    "type": "boolean", 
                    "description": "If True, use Playwright for dynamic content. Otherwise, use requests/BeautifulSoup.",
                    "default": False
                }
            },
            "required": ["url", "selector"]
        }

    def execute(self, url: str, selector: str, attribute: Optional[str] = None, dynamic: bool = False, **kwargs) -> Dict:
        """
        Executes the web scraping action.
        """
        if not url or not selector:
            raise ValueError("'url' and 'selector' are required.")

        try:
            if dynamic:
                extracted_data = self._scrape_dynamic(url, selector, attribute)
            else:
                extracted_data = self._scrape_static(url, selector, attribute)
            
            if not extracted_data:
                return {"message": f"No content found for selector '{selector}'.", "url": url, "selector": selector}

            return {"extracted_content": extracted_data, "url": url, "selector": selector}

        except Exception as e:
            logger.error(f"An error occurred during web scraping: {e}")
            return {"error": str(e)}

    def _scrape_static(self, url: str, selector: str, attribute: Optional[str] = None) -> List[str]:
        """
        Scrapes content from a static URL using requests and BeautifulSoup.
        """
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml') # Use lxml parser
        elements = soup.select(selector)
        
        extracted_data = []
        for element in elements:
            if attribute:
                extracted_data.append(element.get(attribute))
            else:
                extracted_data.append(element.get_text(strip=True))
        
        return extracted_data

    def _scrape_dynamic(self, url: str, selector: str, attribute: Optional[str] = None) -> List[str]:
        """
        Scrapes content from a dynamic URL using Playwright.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector(selector) # Wait for the selector to be present
            
            content = page.content()
            soup = BeautifulSoup(content, 'lxml') # Use lxml parser
            elements = soup.select(selector)
            
            extracted_data = []
            for element in elements:
                if attribute:
                    extracted_data.append(element.get(attribute))
                else:
                    extracted_data.append(element.get_text(strip=True))
            
            browser.close()
            return extracted_data
