
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SportsCommentatorSimulatorTool(BaseTool):
    """
    A tool that simulates a sports commentator, generating dynamic textual
    commentary based on game event data.
    """

    def __init__(self, tool_name: str = "SportsCommentatorSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.events_file = os.path.join(self.data_dir, "game_events.json")
        self.commentary_file = os.path.join(self.data_dir, "commentary_logs.json")
        
        # Game events: {event_id: {game_id: ..., event_type: ..., details: {}}}
        self.game_events: Dict[str, Dict[str, Any]] = self._load_data(self.events_file, default={})
        # Commentary logs: {event_id: {commentary: ..., generated_at: ...}}
        self.commentary_logs: Dict[str, Dict[str, Any]] = self._load_data(self.commentary_file, default={})

    @property
    def description(self) -> str:
        return "Simulates a sports commentator: generates dynamic textual commentary based on game event data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_game_event", "generate_commentary", "get_commentary_log"]},
                "event_id": {"type": "string"},
                "game_id": {"type": "string"},
                "event_type": {"type": "string", "enum": ["goal", "foul", "substitution", "penalty", "save"]},
                "details": {"type": "object", "description": "e.g., {'player': 'Messi', 'team': 'Argentina'}"},
                "log_id": {"type": "string", "description": "ID of the commentary log to retrieve."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_events(self):
        with open(self.events_file, 'w') as f: json.dump(self.game_events, f, indent=2)

    def _save_commentary(self):
        with open(self.commentary_file, 'w') as f: json.dump(self.commentary_logs, f, indent=2)

    def add_game_event(self, event_id: str, game_id: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Adds a new game event record."""
        if event_id in self.game_events: raise ValueError(f"Event '{event_id}' already exists.")
        
        new_event = {
            "id": event_id, "game_id": game_id, "event_type": event_type, "details": details,
            "created_at": datetime.now().isoformat()
        }
        self.game_events[event_id] = new_event
        self._save_events()
        return new_event

    def generate_commentary(self, event_id: str) -> Dict[str, Any]:
        """Generates dynamic commentary for a specific game event."""
        event = self.game_events.get(event_id)
        if not event: raise ValueError(f"Game event '{event_id}' not found. Add it first.")
        
        commentary = ""
        player = event["details"].get("player", "a player")
        team = event["details"].get("team", "their team")
        
        if event["event_type"] == "goal":
            commentary = f"GOAL! {player} with a stunning strike for {team}! What a finish!"
        elif event["event_type"] == "foul":
            commentary = f"A foul committed by {player} from {team}. The referee blows the whistle."
        elif event["event_type"] == "substitution":
            player_out = event["details"].get("player_out", "a player")
            player_in = event["details"].get("player_in", "another player")
            commentary = f"Substitution for {team}: {player_out} comes off, {player_in} comes on."
        elif event["event_type"] == "penalty":
            commentary = f"Penalty awarded! {player} steps up to take it for {team}."
        elif event["event_type"] == "save":
            commentary = f"What a save! The goalkeeper denies {player} a certain goal!"
        else:
            commentary = f"An interesting moment in the game involving {player} from {team}."
        
        log_id = f"commentary_{event_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        log_entry = {
            "id": log_id, "event_id": event_id, "commentary": commentary,
            "generated_at": datetime.now().isoformat()
        }
        self.commentary_logs[log_id] = log_entry
        self._save_commentary()
        return log_entry

    def get_commentary_log(self, log_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated commentary log."""
        log = self.commentary_logs.get(log_id)
        if not log: raise ValueError(f"Commentary log '{log_id}' not found.")
        return log

    def execute(self, operation: str, event_id: str, **kwargs: Any) -> Any:
        if operation == "add_game_event":
            return self.add_game_event(event_id, kwargs['game_id'], kwargs['event_type'], kwargs['details'])
        elif operation == "generate_commentary":
            return self.generate_commentary(event_id)
        elif operation == "get_commentary_log":
            return self.get_commentary_log(kwargs['log_id'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SportsCommentatorSimulatorTool functionality...")
    temp_dir = "temp_sports_commentary_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    commentator_tool = SportsCommentatorSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add a goal event
        print("\n--- Adding game event 'goal_001' ---")
        commentator_tool.execute(operation="add_game_event", event_id="goal_001", game_id="match_123", event_type="goal", details={"player": "Ronaldo", "team": "Portugal"})
        print("Event added.")

        # 2. Generate commentary for the goal
        print("\n--- Generating commentary for 'goal_001' ---")
        commentary1 = commentator_tool.execute(operation="generate_commentary", event_id="goal_001")
        print(json.dumps(commentary1, indent=2))

        # 3. Add a foul event
        print("\n--- Adding game event 'foul_001' ---")
        commentator_tool.execute(operation="add_game_event", event_id="foul_001", game_id="match_123", event_type="foul", details={"player": "Ramos", "team": "Spain"})
        print("Event added.")

        # 4. Generate commentary for the foul
        print("\n--- Generating commentary for 'foul_001' ---")
        commentary2 = commentator_tool.execute(operation="generate_commentary", event_id="foul_001")
        print(json.dumps(commentary2, indent=2))

        # 5. Get commentary log
        print(f"\n--- Getting commentary log for '{commentary1['id']}' ---")
        log = commentator_tool.execute(operation="get_commentary_log", event_id="any", log_id=commentary1["id"]) # event_id is not used for get_commentary_log
        print(json.dumps(log, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
