import logging
import json
import re
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated long video content
SIMULATED_LONG_VIDEOS = {
    "My Podcast Episode 1": {
        "duration_seconds": 3600, # 1 hour
        "transcript": "Welcome to the podcast. Today we discuss AI ethics. A key point is the bias in algorithms. We also touched on the future of work and automation. Finally, we had a funny anecdote about a cat. This was a great discussion.",
        "highlights": [
            "AI ethics and algorithmic bias",
            "Future of work and automation",
            "Funny cat anecdote"
        ]
    },
    "Tech Talk: Microservices": {
        "duration_seconds": 2700, # 45 minutes
        "transcript": "This tech talk covers microservices architecture. We talked about scalability, resilience, and deployment strategies. A major challenge is managing dependencies. We concluded with best practices for microservice adoption.",
        "highlights": [
            "Microservices architecture benefits",
            "Challenges in dependency management",
            "Best practices for adoption"
        ]
    }
}

class OpusClipSimulatorTool(BaseTool):
    """
    A tool that simulates OpusClip's functionality, repurposing long videos
    into short, viral clips with dynamic cropping and captions based on
    simulated video content.
    """

    def __init__(self, tool_name: str = "OpusClipSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates OpusClip: repurposing long videos into short, viral clips with dynamic cropping and captions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for OpusClip (e.g., 'repurpose video \"My Podcast Episode 1\" into viral clips')."
                }
            },
            "required": ["prompt"]
        }

    def _find_video_title(self, prompt: str) -> Optional[str]:
        """Helper to extract video title from prompt."""
        for video_title in SIMULATED_LONG_VIDEOS.keys():
            if video_title.lower() in prompt.lower():
                return video_title
        return None

    def _simulate_repurpose_video(self, video_title: str) -> Dict:
        video_data = SIMULATED_LONG_VIDEOS.get(video_title)
        if not video_data:
            return {"status": "error", "message": f"Video '{video_title}' not found in simulated library."}
        
        generated_clips = []
        for i, highlight in enumerate(video_data["highlights"]):
            clip_duration = random.randint(30, 90) # 30-90 seconds  # nosec B311
            clip_start_time = random.randint(0, video_data["duration_seconds"] - clip_duration)  # nosec B311
            
            generated_clips.append({
                "clip_id": f"{video_title.replace(' ', '_')}_clip_{i+1}",
                "title": f"Viral Clip: {highlight}",
                "duration_seconds": clip_duration,
                "start_time_seconds": clip_start_time,
                "highlights_text": highlight,
                "simulated_url": f"https://opusclip.sim/clips/{video_title.replace(' ', '_')}_{i+1}.mp4",
                "features": {
                    "dynamic_cropping": True,
                    "auto_captions": True,
                    "background_music": random.choice([True, False])  # nosec B311
                }
            })
        
        return {
            "action": "repurpose_video",
            "video_title": video_title,
            "total_clips_generated": len(generated_clips),
            "generated_clips": generated_clips
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate OpusClip simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to OpusClip would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        video_title = self._find_video_title(prompt)

        if "repurpose video" in prompt_lower or "create clips" in prompt_lower:
            if video_title:
                response_data = self._simulate_repurpose_video(video_title)
            else:
                response_data = {"status": "error", "message": "Please specify a video to repurpose."}
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from OpusClip for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with OpusClip."
        return response_data

if __name__ == '__main__':
    print("Demonstrating OpusClipSimulatorTool functionality...")
    
    opusclip_sim = OpusClipSimulatorTool()
    
    try:
        # 1. Repurpose a podcast episode
        print("\n--- Simulating: Repurpose video 'My Podcast Episode 1' ---")
        prompt1 = "repurpose video 'My Podcast Episode 1' into viral clips for social media"
        result1 = opusclip_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Repurpose a tech talk
        print("\n--- Simulating: Repurpose video 'Tech Talk: Microservices' ---")
        prompt2 = "create short clips from 'Tech Talk: Microservices' with captions"
        result2 = opusclip_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))
        
        # 3. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt3 = "What is the capital of France?"
        result3 = opusclip_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")