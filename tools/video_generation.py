import logging
import os
from typing import Dict, Any
from tools.base_tool import BaseTool
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

logger = logging.getLogger(__name__)

class TextToVideoTool(BaseTool):
    """
    A tool to generate a simple video from a text prompt.
    """
    def __init__(self, tool_name: str = "text_to_video_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Generates a simple video clip with the provided text overlaid on a colored background."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text_prompt": {"type": "string", "description": "The text to display in the video."},
                "output_path": {"type": "string", "description": "The local file path to save the output video (e.g., 'output.mp4')."},
                "duration_seconds": {"type": "integer", "description": "The duration of the video in seconds.", "default": 5},
                "font_size": {"type": "integer", "description": "The font size of the text.", "default": 70},
                "background_color": {"type": "string", "description": "The background color of the video.", "default": "black"}
            },
            "required": ["text_prompt", "output_path"]
        }

    def execute(self, text_prompt: str, output_path: str, duration_seconds: int = 5, font_size: int = 70, background_color: str = "black", **kwargs: Any) -> Dict:
        """
        Generates a video from a text prompt.
        """
        try:
            if not text_prompt:
                raise ValueError("'text_prompt' cannot be empty.")
            
            if not output_path.lower().endswith('.mp4'):
                raise ValueError("Output path must have a .mp4 extension.")

            logger.info(f"Generating video for prompt: '{text_prompt}'")

            # Create a TextClip
            txt_clip = TextClip(text_prompt, fontsize=font_size, color='white', size=(1280, 720))
            txt_clip = txt_clip.set_pos('center').set_duration(duration_seconds)

            # Create a background color clip
            color_clip = ColorClip(size=txt_clip.size, color=background_color, duration=duration_seconds)

            # Composite the text on the background
            final_clip = CompositeVideoClip([color_clip, txt_clip])
            
            # Write the final video file
            final_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')

            return {
                "message": f"Video generated successfully and saved to '{output_path}'.",
                "video_duration_seconds": duration_seconds,
                "text_prompt": text_prompt
            }

        except Exception as e:
            logger.error(f"An error occurred in TextToVideoTool: {e}")
            return {"error": str(e)}