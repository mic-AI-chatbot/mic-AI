import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool
import os

logger = logging.getLogger(__name__)

# In-memory storage for simulated enrolled voice profiles
enrolled_voices: Dict[str, Dict[str, Any]] = {}

class VoiceBiometricsSystemTool(BaseTool):
    """
    A tool to simulate a voice biometrics system for enrollment, verification, and identification.
    """
    def __init__(self, tool_name: str = "voice_biometrics_system_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates voice biometrics: enroll, verify, identify speakers, and list enrolled voices."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'enroll', 'verify', 'identify', 'list_enrolled'."
                },
                "speaker_id": {"type": "string", "description": "The unique ID of the speaker."},
                "audio_sample_path": {"type": "string", "description": "The local file path to the audio sample."},
                "threshold": {
                    "type": "number",
                    "description": "Confidence threshold for verification/identification (0.0 to 1.0).",
                    "default": 0.7
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            speaker_id = kwargs.get("speaker_id")
            audio_sample_path = kwargs.get("audio_sample_path")

            if action in ['enroll', 'verify', 'identify'] and not audio_sample_path:
                raise ValueError(f"'audio_sample_path' is required for the '{action}' action.")
            if action in ['enroll', 'verify'] and not speaker_id:
                raise ValueError(f"'speaker_id' is required for the '{action}' action.")

            actions = {
                "enroll": self._enroll_voice,
                "verify": self._verify_voice,
                "identify": self._identify_speaker,
                "list_enrolled": self._list_enrolled_voices,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VoiceBiometricsSystemTool: {e}")
            return {"error": str(e)}

    def _enroll_voice(self, speaker_id: str, audio_sample_path: str, **kwargs) -> Dict:
        if speaker_id in enrolled_voices:
            raise ValueError(f"Speaker '{speaker_id}' is already enrolled.")
        if not os.path.exists(audio_sample_path):
            raise FileNotFoundError(f"Audio sample not found at '{audio_sample_path}'.")

        logger.info(f"Simulating enrollment for speaker '{speaker_id}'.")
        
        enrolled_voices[speaker_id] = {
            "audio_path": audio_sample_path,
            "enrollment_date": datetime.now().isoformat(),
            "voice_features_hash": hash(audio_sample_path) # Simple simulation of voiceprint
        }
        return {"message": "Speaker enrolled successfully.", "speaker_id": speaker_id, "details": enrolled_voices[speaker_id]}

    def _verify_voice(self, speaker_id: str, audio_sample_path: str, threshold: float = 0.7, **kwargs) -> Dict:
        if speaker_id not in enrolled_voices:
            return {"speaker_id": speaker_id, "verified": False, "confidence": 0.0, "reason": "Speaker not enrolled."}
        if not os.path.exists(audio_sample_path):
            raise FileNotFoundError(f"Audio sample not found at '{audio_sample_path}'.")

        logger.info(f"Simulating verification for speaker '{speaker_id}'.")
        
        # Simulate matching based on hash and random factor
        enrolled_hash = enrolled_voices[speaker_id]["voice_features_hash"]
        sample_hash = hash(audio_sample_path)
        
        if enrolled_hash == sample_hash: # Perfect match
            confidence = random.uniform(0.9, 0.99)  # nosec B311
        else:
            confidence = random.uniform(0.3, 0.8) # Some overlap possible, or not  # nosec B311

        verified = confidence >= threshold
        return {"speaker_id": speaker_id, "verified": verified, "confidence": round(confidence, 4), "threshold": threshold}

    def _identify_speaker(self, audio_sample_path: str, threshold: float = 0.7, **kwargs) -> Dict:
        if not enrolled_voices:
            return {"identified_speaker": None, "confidence": 0.0, "reason": "No voices enrolled for identification."}
        if not os.path.exists(audio_sample_path):
            raise FileNotFoundError(f"Audio sample not found at '{audio_sample_path}'.")

        logger.info(f"Simulating speaker identification from '{audio_sample_path}'.")
        
        # Simulate identification by picking a random enrolled speaker
        identified_speaker = random.choice(list(enrolled_voices.keys()))  # nosec B311
        confidence = random.uniform(0.6, 0.95) # Random confidence  # nosec B311
        
        if confidence >= threshold:
            return {"identified_speaker": identified_speaker, "confidence": round(confidence, 4), "threshold": threshold}
        else:
            return {"identified_speaker": None, "confidence": round(confidence, 4), "reason": "No speaker identified above threshold."}

    def _list_enrolled_voices(self, **kwargs) -> Dict:
        if not enrolled_voices:
            return {"message": "No voices are currently enrolled."}
        
        summary = {
            speaker_id: {
                "enrollment_date": details["enrollment_date"],
                "audio_path": details["audio_path"]
            } for speaker_id, details in enrolled_voices.items()
        }
        return {"enrolled_speakers": summary}