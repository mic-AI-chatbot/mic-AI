import logging
import os
from typing import Dict, Any
from tools.base_tool import BaseTool
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

class VideoToGifTool(BaseTool):
    """
    A tool to create an animated GIF from a segment of a video file.
    """
    def __init__(self, tool_name: str = "video_to_gif_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Creates an animated GIF from a specified segment of a video."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "The local file path to the source video."},
                "output_path": {"type": "string", "description": "The local file path to save the output GIF (e.g., 'animation.gif')."},
                "start_time": {"type": "string", "description": "Start time of the clip to convert (in seconds or HH:MM:SS format)."},
                "end_time": {"type": "string", "description": "End time of the clip to convert (in seconds or HH:MM:SS format)."},
                "fps": {
                    "type": "integer", 
                    "description": "Frames per second for the output GIF. A lower value reduces file size.",
                    "default": 10
                }
            },
            "required": ["input_path", "output_path", "start_time", "end_time"]
        }

    def execute(self, input_path: str, output_path: str, start_time: str, end_time: str, fps: int = 10, **kwargs: Any) -> Dict:
        """
        Creates a GIF from a video clip.
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input video file not found at '{input_path}'.")
            
            if not output_path.lower().endswith('.gif'):
                raise ValueError("Output path must have a .gif extension.")

            logger.info(f"Creating GIF from '{input_path}' between {start_time} and {end_time}.")

            with VideoFileClip(input_path) as clip:
                # Create a subclip from the specified times
                gif_clip = clip.subclip(start_time, end_time)
                
                # Write the GIF file
                gif_clip.write_gif(output_path, fps=fps)

            return {
                "message": f"GIF created successfully and saved to '{output_path}'.",
                "gif_duration_seconds": gif_clip.duration,
                "fps": fps
            }

        except Exception as e:
            logger.error(f"An error occurred in VideoToGifTool: {e}")
            return {"error": str(e)}