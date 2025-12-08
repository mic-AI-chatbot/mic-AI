import logging
import json
import os
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports to avoid loading them if not needed and to handle potential ImportError
try:
    from transformers import pipeline
    # librosa and soundfile are often dependencies of audio-classification pipelines
    import librosa
    import soundfile as sf
    TRANSFORMERS_AUDIO_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AUDIO_AVAILABLE = False
    logging.warning("transformers, librosa, or soundfile not found. Audio event detection tool will not be available.")

logger = logging.getLogger(__name__)

class AudioEventDetectorModel:
    """Manages the audio classification model for event detection, using a singleton pattern."""
    _classifier = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioEventDetectorModel, cls).__new__(cls)
            if not TRANSFORMERS_AUDIO_AVAILABLE:
                logger.error("Required libraries for audio event detection are not installed. Please install 'transformers', 'librosa', and 'soundfile'.")
                return cls._instance # Return instance without classifier
            
            if cls._classifier is None:
                try:
                    logger.info("Initializing audio classification model (MIT/ast-finetuned-audioset-10-10-0.4593)...")
                    cls._classifier = pipeline("audio-classification", model="MIT/ast-finetuned-audioset-10-10-0.4593")
                    logger.info("Audio classification model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load audio classification model: {e}")
        return cls._instance

    def detect_events(self, audio_path: str) -> List[Dict[str, Any]]:
        if not self._classifier:
            return [{"error": "Audio classification model not available. Check logs for loading errors."}]

        if not os.path.exists(audio_path):
            return [{"error": f"Audio file not found at '{audio_path}'."}]

        try:
            # The pipeline expects a file path or raw audio data.
            # It handles loading and preprocessing internally.
            predictions = self._classifier(audio_path)
            return predictions
        except Exception as e:
            logger.error(f"Audio event detection failed for '{audio_path}': {e}")
            return [{"error": f"An error occurred during audio event detection: {e}"}]

audio_event_detector_instance = AudioEventDetectorModel()

class DetectAudioEventsTool(BaseTool):
    """Detects audio events in an audio file using a pre-trained AI model."""
    def __init__(self, tool_name="detect_audio_events"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Detects various audio events (e.g., speech, music, environmental sounds) present in an audio file using a pre-trained audio classification model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"audio_file_path": {"type": "string", "description": "The absolute path to the audio file to analyze."}},
            "required": ["audio_file_path"]
        }

    def execute(self, audio_file_path: str, **kwargs: Any) -> str:
        results = audio_event_detector_instance.detect_events(audio_file_path)
        return json.dumps(results, indent=2)