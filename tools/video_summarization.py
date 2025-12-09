import logging
import random
import os
from typing import Dict, Any
from tools.base_tool import BaseTool
from moviepy.editor import VideoFileClip, concatenate_videoclips

logger = logging.getLogger(__name__)

class VideoSummarizationTool(BaseTool):
    """
    A tool to create a summary video by concatenating short, simulated "key" clips
    from a source video.
    """
    def __init__(self, tool_name: str = "video_summarization_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Creates a short summary video from a longer video by selecting and concatenating key clips."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_path": {"type": "string", "description": "The local file path to the source video."},
                "output_path": {"type": "string", "description": "The local file path to save the summary video."},
                "summary_duration_seconds": {
                    "type": "integer",
                    "description": "The desired approximate duration of the summary video.",
                    "default": 10
                }
            },
            "required": ["input_path", "output_path"]
        }

    def execute(self, input_path: str, output_path: str, summary_duration_seconds: int = 10, **kwargs: Any) -> Dict:
        """
        Creates a summary of a video.
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input video file not found at '{input_path}'.")
            
            if not output_path.lower().endswith('.mp4'):
                raise ValueError("Output path must have a .mp4 extension.")

            logger.info(f"Creating a {summary_duration_seconds}s summary for '{input_path}'.")

            with VideoFileClip(input_path) as clip:
                duration = clip.duration
                if summary_duration_seconds >= duration:
                    raise ValueError("Summary duration must be less than the original video's duration.")

                # Simulate finding "key" moments. We'll create 3-5 short clips.
                num_clips = random.randint(3, 5)  # nosec B311
                clip_duration = summary_duration_seconds / num_clips
                
                summary_clips = []
                for i in range(num_clips):
                    # Pick a random start time for each clip, ensuring it's within bounds
                    max_start_time = duration - clip_duration
                    start_time = random.uniform(i * (duration / num_clips), max_start_time)  # nosec B311
                    
                    subclip = clip.subclip(start_time, start_time + clip_duration)
                    summary_clips.append(subclip)
                
                # Combine the clips into a final summary video
                final_clip = concatenate_videoclips(summary_clips)
                
                # Write the final video file
                final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

            return {
                "message": f"Video summary created successfully and saved to '{output_path}'.",
                "original_duration": round(duration, 2),
                "summary_duration": round(final_clip.duration, 2),
                "num_clips_used": len(summary_clips)
            }

        except Exception as e:
            logger.error(f"An error occurred in VideoSummarizationTool: {e}")
            return {"error": str(e)}