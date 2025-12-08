import logging
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PatentSearchSimulatorTool(BaseTool):
    """
    A tool that simulates searching a patent database for keywords and
    returns a list of simulated patent results.
    """

    def __init__(self, tool_name: str = "PatentSearchSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates searching a patent database for keywords and returns simulated patent results."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "The keyword(s) to search for in the patent database."},
                "num_results": {"type": "integer", "minimum": 1, "maximum": 10, "default": 3, "description": "The number of simulated patent results to return."}
            },
            "required": ["keyword"]
        }

    def execute(self, keyword: str, num_results: int = 3, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Simulates searching a patent database for keywords and returns a list of
        simulated patent results.
        """
        if not keyword: raise ValueError("Keyword cannot be empty.")
        if num_results < 1 or num_results > 10: raise ValueError("Number of results must be between 1 and 10.")

        simulated_results = []
        for i in range(num_results):
            patent_id = f"US{random.randint(1000000, 9999999)}B2"  # nosec B311
            inventor = random.choice(["John Doe", "Jane Smith", "Alice Johnson", "Bob Williams"])  # nosec B311
            filing_date = (datetime.now() - timedelta(days=random.randint(365, 365 * 10))).strftime("%Y-%m-%d")  # nosec B311
            
            # Generate a title that incorporates the keyword
            title_templates = [
                f"Method and Apparatus for {keyword.title()} Enhancement",
                f"System for Advanced {keyword.title()} Applications",
                f"Novel Device for {keyword.title()} Integration",
                f"Improved Process for {keyword.title()} Management"
            ]
            title = random.choice(title_templates)  # nosec B311
            
            # Relevance score based on keyword presence
            relevance_score = round(random.uniform(0.6, 0.99), 2) if keyword.lower() in title.lower() else round(random.uniform(0.3, 0.6), 2)  # nosec B311

            simulated_results.append({
                "title": title,
                "patent_id": patent_id,
                "inventor": inventor,
                "filing_date": filing_date,
                "relevance_score": relevance_score,
                "abstract_snippet": f"A patent describing a novel approach to {keyword.lower()} using advanced computational techniques to achieve superior performance and efficiency."
            })
        
        # Sort by relevance score
        simulated_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return simulated_results

if __name__ == '__main__':
    print("Demonstrating PatentSearchSimulatorTool functionality...")
    
    patent_search_tool = PatentSearchSimulatorTool()
    
    try:
        # 1. Search for "AI in healthcare"
        print("\n--- Searching for 'AI in healthcare' (3 results) ---")
        results1 = patent_search_tool.execute(keyword="AI in healthcare", num_results=3)
        print(json.dumps(results1, indent=2))

        # 2. Search for "quantum computing" (5 results)
        print("\n--- Searching for 'quantum computing' (5 results) ---")
        results2 = patent_search_tool.execute(keyword="quantum computing", num_results=5)
        print(json.dumps(results2, indent=2))
        
        # 3. Search for a less common keyword
        print("\n--- Searching for 'bioluminescent algae' (2 results) ---")
        results3 = patent_search_tool.execute(keyword="bioluminescent algae", num_results=2)
        print(json.dumps(results3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")