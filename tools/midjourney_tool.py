import logging
import json
import re
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MidjourneySimulatorTool(BaseTool):
    """
    A tool that simulates interacting with the Midjourney image generation service,
    including parsing Midjourney-specific prompt parameters.
    """

    def __init__(self, tool_name: str = "MidjourneySimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates generating images with Midjourney, including parsing prompt parameters like --ar."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The text prompt, including any Midjourney parameters (e.g., 'a blue dog --ar 16:9')."
                }
            },
            "required": ["prompt"]
        }

    def _parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parses a Midjourney-style prompt into a base prompt and parameters."""
        params = {}
        base_prompt = prompt
        
        # Regex to find --key value pairs
        pattern = r'--(\w+)\s+([^\s--]+)'
        matches = re.findall(pattern, prompt)
        
        for key, value in matches:
            params[key] = value
            # Remove the parsed parameter from the base prompt string
            base_prompt = re.sub(rf'--{key}\s+{value}', '', base_prompt)
            
        return {
            "base_prompt": base_prompt.strip(),
            "parameters": params
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the Midjourney prompt and returns a simulated job result.
        """
        if not prompt:
            raise ValueError("The prompt cannot be empty.")

        parsed_prompt = self._parse_prompt(prompt)
        job_id = f"mj-sim-{random.randint(10000, 99999)}"  # nosec B311
        
        # --- This is where a real API call to Midjourney would be made ---
        # For now, we simulate the response.
        
        simulated_urls = [f"/path/to/simulated_images/{job_id}_{i+1}.png" for i in range(4)]
        
        response_data = {
            "job_id": job_id,
            "status": "completed",
            "prompt_data": parsed_prompt,
            "simulated_image_urls": simulated_urls,
            "upscale_and_variation_options": [f"U{i+1}" for i in range(4)] + [f"V{i+1}" for i in range(4)],
            "disclaimer": "This is a simulated response. No real images were generated."
        }
        
        return response_data

if __name__ == '__main__':
    print("Demonstrating MidjourneySimulatorTool functionality...")
    
    midjourney_sim = MidjourneySimulatorTool()
    
    try:
        # --- Scenario 1: A complex prompt with parameters ---
        print("\n--- Simulating a complex prompt ---")
        prompt1 = "a highly detailed portrait of a cybernetic owl, intricate mechanics, glowing eyes --ar 16:9 --style raw --chaos 20"
        result1 = midjourney_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # --- Scenario 2: A simple prompt ---
        print("\n--- Simulating a simple prompt ---")
        prompt2 = "a cute cat"
        result2 = midjourney_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")