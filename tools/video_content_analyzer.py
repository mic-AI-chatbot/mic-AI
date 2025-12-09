import logging
import os
from typing import Dict, Any
from tools.base_tool import BaseTool
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

class VideoProcessingTool(BaseTool):
    """
    A tool for performing basic video processing tasks like trimming,
    audio extraction, and format conversion.
    """
    def __init__(self, tool_name: str = "video_processing_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Performs video processing tasks: trimming, audio extraction, and format conversion."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'trim', 'extract_audio', 'convert'."
                },
                "input_path": {"type": "string", "description": "The local file path to the source video."},
                "output_path": {"type": "string", "description": "The local file path to save the output."},
                "start_time": {"type": "string", "description": "Start time for trimming (in seconds or HH:MM:SS format)."},
                "end_time": {"type": "string", "description": "End time for trimming (in seconds or HH:MM:SS format)."}
            },
            "required": ["action", "input_path", "output_path"]
        }

    def execute(self, action: str, input_path: str, output_path: str, **kwargs: Any) -> Dict:
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input video file not found at '{input_path}'.")

            action = action.lower()
            
            with VideoFileClip(input_path) as clip:
                if action == 'trim':
                    start_time = kwargs.get("start_time")
                    end_time = kwargs.get("end_time")
                    if start_time is None or end_time is None:
                        raise ValueError("'start_time' and 'end_time' are required for trimming.")
                    
                    trimmed_clip = clip.subclip(start_time, end_time)
                    trimmed_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
                    
                    return {"message": f"Video trimmed successfully and saved to '{output_path}'.", "duration": trimmed_clip.duration}

                elif action == 'extract_audio':
                    if not output_path.lower().endswith(('.mp3', '.wav', '.aac')):
                        raise ValueError("Output path for audio must have a valid audio extension (e.g., .mp3, .wav).")
                    
                    audio = clip.audio
                    audio.write_audiofile(output_path)
                    audio.close()
                    
                    return {"message": f"Audio extracted successfully and saved to '{output_path}'."}

                elif action == 'convert':
                    # The format is inferred from the output_path extension
                    logger.info(f"Converting video to format implied by '{output_path}'")
                    clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
                    return {"message": f"Video converted successfully and saved to '{output_path}'."}

                else:
                    raise ValueError(f"Invalid action. Supported: 'trim', 'extract_audio', 'convert'.")

        except Exception as e:
            logger.error(f"An error occurred in VideoProcessingTool: {e}")
            return {"error": str(e)}