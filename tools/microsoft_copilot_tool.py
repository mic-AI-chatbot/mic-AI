import logging
import json
import re
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MicrosoftCopilotSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Microsoft Copilot, providing
    structured JSON responses based on the user's prompt.
    """

    def __init__(self, tool_name: str = "MicrosoftCopilotSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Microsoft 365 actions like drafting emails, creating presentations, or generating images."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt describing the action to perform."
                }
            },
            "required": ["prompt"]
        }

    def _simulate_draft_email(self, prompt: str) -> Dict:
        recipient_match = re.search(r'to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', prompt)
        subject_match = re.search(r'about\s+([\'"]?)(.*?)\1(?:$|\s+with)', prompt)
        
        return {
            "action": "draft_email",
            "recipient": recipient_match.group(1) if recipient_match else "unknown",
            "subject": subject_match.group(2).title() if subject_match else "Update",
            "body": f"This is a simulated email draft based on your request: '{prompt}'."
        }

    def _simulate_create_presentation(self, prompt: str) -> Dict:
        title_match = re.search(r'about\s+([\'"]?)(.*?)\1(?:$)', prompt)
        title = title_match.group(2).title() if title_match else "New Presentation"
        
        return {
            "action": "create_presentation",
            "title": title,
            "slides": [
                {"title": "Introduction", "content": f"Overview of {title}."},
                {"title": "Key Point 1", "content": "Detailed discussion on the first major topic."},
                {"title": "Conclusion", "content": "Summary and next steps."}
            ]
        }

    def _simulate_generate_image(self, prompt: str) -> Dict:
        image_prompt_match = re.search(r'of\s+([\'"]?)(.*?)\1(?:$)', prompt)
        image_prompt = image_prompt_match.group(2) if image_prompt_match else "a random subject"
        
        return {
            "action": "generate_image",
            "image_generation_prompt": image_prompt,
            "simulated_image_path": f"/path/to/generated_images/{image_prompt.replace(' ', '_')}.png"
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Microsoft Copilot would be made ---
        # response = copilot_api.generate(prompt)
        # For now, we simulate the response based on keywords.
        
        response_data = {}
        if "draft email" in prompt_lower or "send email" in prompt_lower:
            response_data = self._simulate_draft_email(prompt)
        elif "create presentation" in prompt_lower or "make a powerpoint" in prompt_lower:
            response_data = self._simulate_create_presentation(prompt)
        elif "generate image" in prompt_lower or "create a picture" in prompt_lower:
            response_data = self._simulate_generate_image(prompt)
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Copilot for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Microsoft Copilot."
        return response_data

if __name__ == '__main__':
    print("Demonstrating MicrosoftCopilotSimulatorTool functionality...")
    
    copilot_sim = MicrosoftCopilotSimulatorTool()
    
    try:
        # --- Scenario 1: Draft an email ---
        print("\n--- Simulating: Draft an email ---")
        prompt1 = "draft email to alice@example.com about 'Project Phoenix Update'"
        result1 = copilot_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # --- Scenario 2: Create a presentation ---
        print("\n--- Simulating: Create a presentation ---")
        prompt2 = "Can you make a powerpoint about the Q3 financial results"
        result2 = copilot_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # --- Scenario 3: Generate an image ---
        print("\n--- Simulating: Generate an image ---")
        prompt3 = "generate image of a futuristic city skyline at sunset"
        result3 = copilot_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # --- Scenario 4: Generic query ---
        print("\n--- Simulating: Generic query ---")
        prompt4 = "What is the capital of France?"
        result4 = copilot_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")