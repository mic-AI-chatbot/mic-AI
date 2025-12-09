import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SpeakerManagementSimulatorTool(BaseTool):
    """
    A tool that simulates speaker management, allowing for adding speakers,
    assigning them to events, and tracking their schedules.
    """

    def __init__(self, tool_name: str = "SpeakerManagementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.speakers_file = os.path.join(self.data_dir, "speaker_profiles.json")
        self.assignments_file = os.path.join(self.data_dir, "event_assignments.json")
        
        # Speaker profiles: {speaker_id: {name: ..., expertise: [], availability: {start_date: ..., end_date: ...}}}
        self.speaker_profiles: Dict[str, Dict[str, Any]] = self._load_data(self.speakers_file, default={})
        # Event assignments: {event_id: {speaker_id: ..., event_date: ..., event_topic: ...}}
        self.event_assignments: Dict[str, Dict[str, Any]] = self._load_data(self.assignments_file, default={})

    @property
    def description(self) -> str:
        return "Simulates speaker management: add speakers, assign to events, and track schedules."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_speaker", "assign_speaker_to_event", "get_speaker_schedule", "list_speakers"]},
                "speaker_id": {"type": "string"},
                "name": {"type": "string"},
                "expertise": {"type": "array", "items": {"type": "string"}},
                "availability_start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "availability_end_date": {"type": "string", "description": "YYYY-MM-DD"},
                "event_id": {"type": "string"},
                "event_date": {"type": "string", "description": "YYYY-MM-DD"},
                "event_topic": {"type": "string"}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_speakers(self):
        with open(self.speakers_file, 'w') as f: json.dump(self.speaker_profiles, f, indent=2)

    def _save_assignments(self):
        with open(self.assignments_file, 'w') as f: json.dump(self.event_assignments, f, indent=2)

    def add_speaker(self, speaker_id: str, name: str, expertise: List[str], availability_start_date: str, availability_end_date: str) -> Dict[str, Any]:
        """Adds a new speaker profile."""
        if speaker_id in self.speaker_profiles: raise ValueError(f"Speaker '{speaker_id}' already exists.")
        
        new_speaker = {
            "id": speaker_id, "name": name, "expertise": expertise,
            "availability": {"start_date": availability_start_date, "end_date": availability_end_date},
            "created_at": datetime.now().isoformat()
        }
        self.speaker_profiles[speaker_id] = new_speaker
        self._save_speakers()
        return new_speaker

    def assign_speaker_to_event(self, speaker_id: str, event_id: str, event_date: str, event_topic: str) -> Dict[str, Any]:
        """Assigns a speaker to an event, checking availability."""
        speaker = self.speaker_profiles.get(speaker_id)
        if not speaker: raise ValueError(f"Speaker '{speaker_id}' not found. Add them first.")
        
        event_dt = datetime.strptime(event_date, "%Y-%m-%d").date()
        avail_start_dt = datetime.strptime(speaker["availability"]["start_date"], "%Y-%m-%d").date()
        avail_end_dt = datetime.strptime(speaker["availability"]["end_date"], "%Y-%m-%d").date()
        
        if not (avail_start_dt <= event_dt <= avail_end_dt):
            return {"status": "error", "message": f"Speaker '{speaker_id}' is not available on {event_date}."}
        
        if event_id in self.event_assignments: raise ValueError(f"Event '{event_id}' already has an assigned speaker.")
        
        new_assignment = {
            "event_id": event_id, "speaker_id": speaker_id, "event_date": event_date,
            "event_topic": event_topic, "assigned_at": datetime.now().isoformat()
        }
        self.event_assignments[event_id] = new_assignment
        self._save_assignments()
        return new_assignment

    def get_speaker_schedule(self, speaker_id: str) -> List[Dict[str, Any]]:
        """Retrieves a speaker's assigned events."""
        if speaker_id not in self.speaker_profiles: raise ValueError(f"Speaker '{speaker_id}' not found.")
        
        schedule = [assignment for assignment in self.event_assignments.values() if assignment["speaker_id"] == speaker_id]
        return schedule

    def list_speakers(self) -> List[Dict[str, Any]]:
        """Lists all defined speakers."""
        return list(self.speaker_profiles.values())

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_speaker":
            speaker_id = kwargs.get('speaker_id')
            name = kwargs.get('name')
            expertise = kwargs.get('expertise')
            availability_start_date = kwargs.get('availability_start_date')
            availability_end_date = kwargs.get('availability_end_date')
            if not all([speaker_id, name, expertise, availability_start_date, availability_end_date]):
                raise ValueError("Missing 'speaker_id', 'name', 'expertise', 'availability_start_date', or 'availability_end_date' for 'add_speaker' operation.")
            return self.add_speaker(speaker_id, name, expertise, availability_start_date, availability_end_date)
        elif operation == "assign_speaker_to_event":
            speaker_id = kwargs.get('speaker_id')
            event_id = kwargs.get('event_id')
            event_date = kwargs.get('event_date')
            event_topic = kwargs.get('event_topic')
            if not all([speaker_id, event_id, event_date, event_topic]):
                raise ValueError("Missing 'speaker_id', 'event_id', 'event_date', or 'event_topic' for 'assign_speaker_to_event' operation.")
            return self.assign_speaker_to_event(speaker_id, event_id, event_date, event_topic)
        elif operation == "get_speaker_schedule":
            speaker_id = kwargs.get('speaker_id')
            if not speaker_id:
                raise ValueError("Missing 'speaker_id' for 'get_speaker_schedule' operation.")
            return self.get_speaker_schedule(speaker_id)
        elif operation == "list_speakers":
            # No additional kwargs required for list_speakers
            return self.list_speakers()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SpeakerManagementSimulatorTool functionality...")
    temp_dir = "temp_speaker_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    speaker_tool = SpeakerManagementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add a speaker
        print("\n--- Adding speaker 'Dr_AI_Expert' ---")
        speaker_tool.execute(operation="add_speaker", speaker_id="Dr_AI_Expert", name="Dr. Ava Intelligence", expertise=["AI", "Machine Learning"], availability_start_date="2025-12-01", availability_end_date="2026-01-31")
        print("Speaker added.")

        # 2. Assign speaker to an event
        print("\n--- Assigning 'Dr_AI_Expert' to 'Tech_Conf_2025' ---")
        assignment_result = speaker_tool.execute(operation="assign_speaker_to_event", speaker_id="Dr_AI_Expert", event_id="Tech_Conf_2025", event_date="2025-12-15", event_topic="Future of AI")
        print(json.dumps(assignment_result, indent=2))

        # 3. Get speaker schedule
        print("\n--- Getting schedule for 'Dr_AI_Expert' ---")
        schedule = speaker_tool.execute(operation="get_speaker_schedule", speaker_id="Dr_AI_Expert")
        print(json.dumps(schedule, indent=2))

        # 4. Add another speaker
        print("\n--- Adding speaker 'Dr_Quantum_Guru' ---")
        speaker_tool.execute(operation="add_speaker", speaker_id="Dr_Quantum_Guru", name="Dr. Q. Bits", expertise=["Quantum Computing"], availability_start_date="2026-02-01", availability_end_date="2026-03-31")
        print("Speaker added.")

        # 5. List all speakers
        print("\n--- Listing all speakers ---")
        all_speakers = speaker_tool.execute(operation="list_speakers", speaker_id="any") # speaker_id is not used for list_speakers
        print(json.dumps(all_speakers, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")