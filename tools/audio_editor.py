import os
from pydub import AudioSegment
import logging
import json
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

def _load_audio(file_path: str) -> AudioSegment:
    """Helper function to load an audio file and provide detailed error messages."""
    if not os.path.isabs(file_path):
        raise ValueError("The provided file_path must be an absolute path.")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at the specified path: '{file_path}'.")
    try:
        return AudioSegment.from_file(file_path)
    except Exception as e:
        logger.error(f"Pydub failed to load audio file '{file_path}': {e}")
        raise ValueError(f"Could not load audio file. Ensure it is a valid audio format (e.g., wav, mp3). This tool also requires FFmpeg to be installed on the system for most formats. Error: {e}")

class GetAudioInfoTool(BaseTool):
    """Tool to get detailed information about an audio file."""
    def __init__(self, tool_name="get_audio_info"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Retrieves detailed information about an audio file, such as its duration, channels, sample rate, and max amplitude."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"file_path": {"type": "string", "description": "The absolute path to the audio file."}},
            "required": ["file_path"]
        }

    def execute(self, file_path: str, **kwargs: Any) -> str:
        audio = _load_audio(file_path)
        info = {
            "duration_ms": len(audio),
            "channels": audio.channels,
            "sample_width_bytes": audio.sample_width,
            "frame_rate_hz": audio.frame_rate,
            "max_amplitude": audio.max
        }
        return json.dumps(info, indent=2)

class TrimAudioTool(BaseTool):
    """Tool to trim a segment from an audio file."""
    def __init__(self, tool_name="trim_audio"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Trims a specified segment of an audio file (using milliseconds) and saves the result to a new file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the input audio file."},
                "start_ms": {"type": "integer", "description": "Start time of the trim in milliseconds."},
                "end_ms": {"type": "integer", "description": "End time of the trim in milliseconds."},
                "output_path": {"type": "string", "description": "Absolute path to save the trimmed audio."}
            },
            "required": ["file_path", "start_ms", "end_ms", "output_path"]
        }

    def execute(self, file_path: str, start_ms: int, end_ms: int, output_path: str, **kwargs: Any) -> str:
        audio = _load_audio(file_path)
        if not (0 <= start_ms < end_ms <= len(audio)):
            raise ValueError(f"Invalid start/end times. Values must be within the audio duration of {len(audio)}ms.")

        trimmed_audio = audio[start_ms:end_ms]
        trimmed_audio.export(output_path, format=output_path.split('.')[-1])
        
        return json.dumps({"message": "Audio trimmed successfully.", "output_path": output_path}, indent=2)

class ConcatenateAudioTool(BaseTool):
    """Tool to concatenate multiple audio files together."""
    def __init__(self, tool_name="concatenate_audio"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Concatenates a list of audio files into a single output file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_files": {"type": "array", "items": {"type": "string"}, "description": "A list of absolute paths to the audio files to combine."},
                "output_path": {"type": "string", "description": "The absolute path to save the combined audio."}
            },
            "required": ["input_files", "output_path"]
        }

    def execute(self, input_files: List[str], output_path: str, **kwargs: Any) -> str:
        if not input_files:
            raise ValueError("The 'input_files' list cannot be empty.")
        
        combined = AudioSegment.empty()
        for file in input_files:
            combined += _load_audio(file)
        
        combined.export(output_path, format=output_path.split('.')[-1])
        
        return json.dumps({"message": f"Successfully concatenated {len(input_files)} files.", "output_path": output_path}, indent=2)

class ConvertAudioFormatTool(BaseTool):
    """Tool to convert an audio file to a different format."""
    def __init__(self, tool_name="convert_audio_format"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Converts an audio file to a different format (e.g., 'mp3', 'wav', 'flac')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the input audio file."},
                "output_path": {"type": "string", "description": "Absolute path to save the converted audio."},
                "output_format": {"type": "string", "description": "The desired output format (e.g., 'wav', 'mp3')."}
            },
            "required": ["file_path", "output_path", "output_format"]
        }

    def execute(self, file_path: str, output_path: str, output_format: str, **kwargs: Any) -> str:
        audio = _load_audio(file_path)
        audio.export(output_path, format=output_format)
        
        return json.dumps({"message": f"Audio successfully converted to {output_format}.", "output_path": output_path}, indent=2)

class ApplyAudioEffectTool(BaseTool):
    """Tool to apply various common audio effects."""
    def __init__(self, tool_name="apply_audio_effect"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Applies an audio effect (e.g., fade_in, reverse, volume_change) to a file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the input audio file."},
                "effect_type": {"type": "string", "description": "The effect to apply.", "enum": ["fade_in", "fade_out", "volume_change", "speed_change", "reverse"]},
                "output_path": {"type": "string", "description": "Absolute path to save the modified audio."},
                "duration_ms": {"type": "integer", "description": "Required for fades: duration of the fade in milliseconds."},
                "db_change": {"type": "number", "description": "Required for volume change: change in dB (e.g., 3.0 for louder, -3.0 for quieter)."},
                "speed_multiplier": {"type": "number", "description": "Required for speed change: speed multiplier (e.g., 0.5 for half speed, 2.0 for double speed)."}
            },
            "required": ["file_path", "effect_type", "output_path"]
        }

    def execute(self, file_path: str, effect_type: str, output_path: str, **kwargs: Any) -> str:
        audio = _load_audio(file_path)
        
        if effect_type == "fade_in":
            duration = kwargs.get("duration_ms")
            if duration is None: raise ValueError("'duration_ms' is required for 'fade_in'.")
            processed_audio = audio.fade_in(duration)
        elif effect_type == "fade_out":
            duration = kwargs.get("duration_ms")
            if duration is None: raise ValueError("'duration_ms' is required for 'fade_out'.")
            processed_audio = audio.fade_out(duration)
        elif effect_type == "volume_change":
            db = kwargs.get("db_change")
            if db is None: raise ValueError("'db_change' is required for 'volume_change'.")
            processed_audio = audio + db
        elif effect_type == "speed_change":
            multiplier = kwargs.get("speed_multiplier")
            if multiplier is None: raise ValueError("'speed_multiplier' is required for 'speed_change'.")
            processed_audio = audio.set_frame_rate(int(audio.frame_rate * multiplier))
        elif effect_type == "reverse":
            processed_audio = audio.reverse()
        else:
            raise ValueError(f"Unsupported effect type: '{effect_type}'.")

        processed_audio.export(output_path, format=output_path.split('.')[-1])
        
        return json.dumps({"message": f"Effect '{effect_type}' applied successfully.", "output_path": output_path}, indent=2)