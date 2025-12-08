import logging
import json
import re
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RytrSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Rytr, an AI writing assistant,
    generating various types of content like blog outlines, ad copy, and emails.
    """

    def __init__(self, tool_name: str = "RytrSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Rytr: content generation using various templates (e.g., blog outlines, ad copy, emails)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for Rytr (e.g., 'generate blog outline for \"AI in Healthcare\"')."
                }
            },
            "required": ["prompt"]
        }

    def _simulate_generate_blog_outline(self, topic: str) -> Dict:
        outline = [
            f"Introduction: What is {topic}?",
            f"Key Benefits of {topic}",
            f"Challenges and Solutions in {topic}",
            f"Future Trends in {topic}",
            "Conclusion: Summary and Call to Action"
        ]
        return {
            "action": "generate_blog_outline",
            "topic": topic,
            "generated_outline": outline
        }

    def _simulate_generate_ad_copy(self, product: str) -> Dict:
        ad_copy_options = [
            f"Unlock the power of {product}! Experience unparalleled performance and innovation. Buy now!",
            f"Transform your life with {product}. Simple, effective, and designed for you. Learn more!",
            f"Don't miss out on {product}! Limited time offer. Get yours today!"
        ]
        return {
            "action": "generate_ad_copy",
            "product": product,
            "generated_copy": random.choice(ad_copy_options)  # nosec B311
        }

    def _simulate_draft_email(self, purpose: str) -> Dict:
        email_body = f"Dear Customer,\n\nThis is a simulated email draft regarding your request for '{purpose}'. We are working to provide you with the best possible solution.\n\nSincerely,\nRytr AI (Simulated)"
        return {
            "action": "draft_email",
            "purpose": purpose,
            "generated_email_body": email_body
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate Rytr simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Rytr would be made ---
        # For now, we simulate the response.
        
        response_data = {}

        if "generate blog outline" in prompt_lower:
            topic_match = re.search(r'for\s+([\'\"]?)(.*?)\1(?:$)', prompt_lower)
            topic = topic_match.group(2).title() if topic_match else "General Topic"
            response_data = self._simulate_generate_blog_outline(topic)
        elif "write ad copy" in prompt_lower or "generate ad copy" in prompt_lower:
            product_match = re.search(r'for\s+([\'\"]?)(.*?)\1(?:$)', prompt_lower)
            product = product_match.group(2).title() if product_match else "New Product"
            response_data = self._simulate_generate_ad_copy(product)
        elif "draft email" in prompt_lower:
            purpose_match = re.search(r'for\s+([\'\"]?)(.*?)\1(?:$)', prompt_lower)
            purpose = purpose_match.group(2).title() if purpose_match else "General Purpose"
            response_data = self._simulate_draft_email(purpose)
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Rytr for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Rytr."
        return response_data

if __name__ == '__main__':
    print("Demonstrating RytrSimulatorTool functionality...")
    
    rytr_sim = RytrSimulatorTool()
    
    try:
        # 1. Generate a blog outline
        print("\n--- Simulating: Generate blog outline for 'Future of Quantum Computing' ---")
        prompt1 = "generate blog outline for 'Future of Quantum Computing'"
        result1 = rytr_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Generate ad copy
        print("\n--- Simulating: Write ad copy for 'New AI-Powered Vacuum Cleaner' ---")
        prompt2 = "write ad copy for 'New AI-Powered Vacuum Cleaner'"
        result2 = rytr_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # 3. Draft an email
        print("\n--- Simulating: Draft email for 'customer support inquiry' ---")
        prompt3 = "draft email for 'customer support inquiry'"
        result3 = rytr_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # 4. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt4 = "Tell me a joke."
        result4 = rytr_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")