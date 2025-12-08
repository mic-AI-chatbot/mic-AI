import logging
import json
import re
import random
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated Notion pages and database items
SIMULATED_NOTION_DATA = {
    "pages": {
        "Meeting Notes - Project Alpha": {
            "content": "Meeting on 2023-11-15. Discussed project timeline, resource allocation, and next steps. Decision: Prioritize Feature X. Action Item: Bob to research cloud providers. Deadline: 2023-11-20.",
            "properties": {"Status": "In Progress", "Owner": "Alice"}
        },
        "Research Paper on AI": {
            "content": "Artificial intelligence (AI) is a rapidly evolving field. Machine learning, a subset of AI, focuses on algorithms that learn from data. Deep learning is a further specialization using neural networks. AI has applications in natural language processing, computer vision, and robotics. Ethical considerations are paramount in AI development.",
            "properties": {"Tags": ["AI", "Research"], "Summary": ""}
        }
    },
    "databases": {
        "Tasks Database": {
            "items": {
                "Implement Feature Y": {"Status": "To Do", "Priority": "High", "Due Date": "2023-11-25"},
                "Refactor Auth Module": {"Status": "In Progress", "Priority": "Medium", "Due Date": "2023-11-30"}
            }
        }
    }
}

class NotionAISimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Notion AI, providing structured
    JSON responses for tasks like summarizing pages, auto-filling properties,
    and answering questions based on simulated Notion content.
    """

    def __init__(self, tool_name: str = "NotionAISimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Notion AI: drafting, summarizing, translating text, auto-filling properties, and Q&A on page content."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for Notion AI (e.g., 'summarize page \"Meeting Notes\"')."
                }
            },
            "required": ["prompt"]
        }

    def _find_page_or_item_title(self, prompt: str) -> Optional[str]:
        """Helper to extract page/item title from prompt."""
        for page_title in SIMULATED_NOTION_DATA["pages"].keys():
            if page_title.lower() in prompt.lower():
                return page_title
        for db_name, db_data in SIMULATED_NOTION_DATA["databases"].items():
            for item_title in db_data["items"].keys():
                if item_title.lower() in prompt.lower():
                    return item_title
        return None

    def _simulate_summarize_page(self, page_title: str) -> Dict:
        page_data = SIMULATED_NOTION_DATA["pages"].get(page_title)
        if not page_data:
            return {"status": "error", "message": f"Page '{page_title}' not found in simulated Notion."}
        
        # Simple summary: take first few sentences
        summary = " ".join(page_data["content"].split('.')[:2]) + "."
        
        return {
            "action": "summarize_page",
            "page_title": page_title,
            "summary": summary
        }

    def _simulate_auto_fill_property(self, page_title: str, property_name: str) -> Dict:
        page_data = SIMULATED_NOTION_DATA["pages"].get(page_title)
        if not page_data:
            return {"status": "error", "message": f"Page '{page_title}' not found in simulated Notion."}
        
        # Simulate filling a summary property
        if property_name.lower() == "summary":
            filled_value = self._simulate_summarize_page(page_title)["summary"]
        else:
            filled_value = f"Simulated value for '{property_name}' based on page content."
        
        # Update simulated data
        SIMULATED_NOTION_DATA["pages"][page_title]["properties"][property_name] = filled_value

        return {
            "action": "auto_fill_property",
            "page_title": page_title,
            "property_name": property_name,
            "filled_value": filled_value
        }

    def _simulate_answer_question(self, question: str, page_title: Optional[str] = None) -> Dict:
        answer = "I cannot find a direct answer to that question in the simulated content."
        source = "N/A"
        
        if page_title:
            page_data = SIMULATED_NOTION_DATA["pages"].get(page_title)
            if page_data:
                if "AI" in question and "AI" in page_data["content"]:
                    answer = "AI is a rapidly evolving field, with machine learning and deep learning as subsets. It has applications in NLP, computer vision, and robotics."
                    source = page_title
                elif "deadline" in question and "Deadline" in page_data["content"]:
                    answer = "The deadline for Bob to research cloud providers is 2023-11-20."
                    source = page_title
        
        return {
            "action": "answer_question",
            "question": question,
            "answer": answer,
            "source_page": source
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate Notion AI simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Notion AI would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        page_or_item_title = self._find_page_or_item_title(prompt)

        if "summarize page" in prompt_lower:
            if page_or_item_title:
                response_data = self._simulate_summarize_page(page_or_item_title)
            else:
                response_data = {"status": "error", "message": "Please specify a page to summarize."}
        elif "auto-fill" in prompt_lower or "autofill" in prompt_lower:
            property_match = re.search(r'\'(.*?)\'\s+property', prompt_lower)
            property_name = property_match.group(1) if property_match else "Summary"
            if page_or_item_title:
                response_data = self._simulate_auto_fill_property(page_or_item_title, property_name)
            else:
                response_data = {"status": "error", "message": "Please specify a page for auto-fill."}
        elif "answer" in prompt_lower and "about" in prompt_lower:
            question_match = re.search(r'answer\s+([\'"]?)(.*?)\1\s+about', prompt_lower)
            question = question_match.group(2) if question_match else "unknown question"
            response_data = self._simulate_answer_question(question, page_or_item_title)
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Notion AI for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Notion AI."
        return response_data

if __name__ == '__main__':
    print("Demonstrating NotionAISimulatorTool functionality...")
    
    notion_sim = NotionAISimulatorTool()
    
    try:
        # 1. Summarize a page
        print("\n--- Simulating: Summarize page 'Meeting Notes - Project Alpha' ---")
        prompt1 = "summarize page 'Meeting Notes - Project Alpha'"
        result1 = notion_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Auto-fill a property
        print("\n--- Simulating: Auto-fill 'Summary' property for 'Research Paper on AI' page ---")
        prompt2 = "auto-fill 'Summary' property for 'Research Paper on AI' page"
        result2 = notion_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))
        
        # 3. Answer a question
        print("\n--- Simulating: Answer 'What is the deadline?' about 'Meeting Notes - Project Alpha' page ---")
        prompt3 = "answer 'What is the deadline?' about 'Meeting Notes - Project Alpha' page"
        result3 = notion_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))

        # 4. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt4 = "Write a poem about a cat."
        result4 = notion_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")