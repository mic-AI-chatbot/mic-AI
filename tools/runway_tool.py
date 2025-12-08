import logging
import json
import re
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RunwayMLSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with RunwayML, providing structured
    JSON responses for generative video and video editing tasks like
    Text-to-Video, Image-to-Video, and Inpainting.
    """

    def __init__(self, tool_name: str = "RunwayMLSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates RunwayML: Text-to-Video, Image-to-Video, and video editing features like Inpainting and Frame Interpolation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for RunwayML (e.g., 'text to video: a futuristic city')."
                }
            },
            "required": ["prompt"]
        }

    def _simulate_text_to_video(self, input_text: str) -> Dict:
        video_id = f"runway_vid_{random.randint(10000, 99999)}"  # nosec B311
        duration = random.randint(3, 10) # 3-10 seconds  # nosec B311
        
        return {
            "action": "text_to_video",
            "input_text": input_text,
            "simulated_video_url": f"https://runway.sim/videos/{video_id}.mp4",
            "duration_seconds": duration,
            "style": random.choice(["cinematic", "anime", "abstract"]),  # nosec B311
            "status": "generated"
        }

    def _simulate_image_to_video(self, input_image_url: str) -> Dict:
        video_id = f"runway_vid_{random.randint(10000, 99999)}"  # nosec B311
        duration = random.randint(2, 7) # 2-7 seconds  # nosec B311
        motion_type = random.choice(["subtle_pan", "zoom_in", "rotate_3d"])  # nosec B311
        
        return {
            "action": "image_to_video",
            "input_image_url": input_image_url,
            "simulated_video_url": f"https://runway.sim/videos/{video_id}.mp4",
            "duration_seconds": duration,
            "motion_type": motion_type,
            "status": "generated"
        }

    def _simulate_inpainting(self, input_video_url: str, object_to_remove: str) -> Dict:
        output_video_id = f"runway_vid_inpainting_{random.randint(10000, 99999)}"  # nosec B311
        
        return {
            "action": "inpainting",
            "input_video_url": input_video_url,
            "object_to_remove": object_to_remove,
            "simulated_output_url": f"https://runway.sim/videos/{output_video_id}.mp4",
            "status": "processed",
            "message": f"Simulated: Object '{object_to_remove}' removed from video."
        }

    def _simulate_frame_interpolation(self, input_video_url: str, target_fps: int) -> Dict:
        output_video_id = f"runway_vid_interp_{random.randint(10000, 99999)}"  # nosec B311
        
        return {
            "action": "frame_interpolation",
            "input_video_url": input_video_url,
            "original_fps": random.randint(15, 30),  # nosec B311
            "target_fps": target_fps,
            "simulated_output_url": f"https://runway.sim/videos/{output_video_id}.mp4",
            "status": "processed",
            "message": f"Simulated: Video frames interpolated to {target_fps} FPS."
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate RunwayML simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to RunwayML would be made ---
        # For now, we simulate the response.
        
        response_data = {}

        if "text to video" in prompt_lower:
            text_match = re.search(r'text to video:\s*(.*)', prompt_lower)
            input_text = text_match.group(1).strip() if text_match else "a generic scene"
            response_data = self._simulate_text_to_video(input_text)
        elif "image to video" in prompt_lower:
            image_url_match = re.search(r'image to video:\s*(.*)', prompt_lower)
            input_image_url = image_url_match.group(1).strip() if image_url_match else "https://runway.sim/images/default.jpg"
            response_data = self._simulate_image_to_video(input_image_url)
        elif "inpainting" in prompt_lower or "remove object" in prompt_lower:
            video_url_match = re.search(r'from video:\s*(.*)', prompt_lower)
            video_url = video_url_match.group(1).strip() if video_url_match else "https://runway.sim/videos/input.mp4"
            object_match = re.search(r'remove\s+(.*?)\s+from', prompt_lower)
            object_to_remove = object_match.group(1).strip() if object_match else "a person"
            response_data = self._simulate_inpainting(video_url, object_to_remove)
        elif "frame interpolation" in prompt_lower or "smooth video" in prompt_lower:
            video_url_match = re.search(r'video:\s*(.*)', prompt_lower)
            video_url = video_url_match.group(1).strip() if video_url_match else "https://runway.sim/videos/input.mp4"
            fps_match = re.search(r'to\s+(\d+)\s+fps', prompt_lower)
            target_fps = int(fps_match.group(1)) if fps_match else 60
            response_data = self._simulate_frame_interpolation(video_url, target_fps)
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from RunwayML for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with RunwayML."
        return response_data

if __name__ == '__main__':
    print("Demonstrating RunwayMLSimulatorTool functionality...")
    
    runway_sim = RunwayMLSimulatorTool()
    
    try:
        # 1. Text-to-Video
        print("\n--- Simulating: Text-to-Video 'a futuristic city' ---")
        prompt1 = "text to video: a futuristic city with flying cars"
        result1 = runway_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Image-to-Video
        print("\n--- Simulating: Image-to-Video 'make this image move' ---")
        prompt2 = "image to video: make this image move from https://runway.sim/images/static_scene.jpg"
        result2 = runway_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # 3. Inpainting
        print("\n--- Simulating: Inpainting 'remove a person from video: https://runway.sim/videos/crowd.mp4' ---")
        prompt3 = "inpainting: remove a person from video: https://runway.sim/videos/crowd.mp4"
        result3 = runway_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # 4. Frame Interpolation
        print("\n--- Simulating: Frame Interpolation 'smooth video: https://runway.sim/videos/low_fps.mp4 to 60 fps' ---")
        prompt4 = "frame interpolation: smooth video: https://runway.sim/videos/low_fps.mp4 to 60 fps"
        result4 = runway_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

        # 5. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt5 = "What is the capital of France?"
        result5 = runway_sim.execute(prompt=prompt5)
        print(json.dumps(result5, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")