import logging
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

DB_FILE = "event_registration.db"

class EventDBManager:
    """Manages the database for the event registration system."""
    _instance = None

    def __new__(cls, db_file):
        if cls._instance is None:
            cls._instance = super(EventDBManager, cls).__new__(cls)
            cls._instance.db_file = db_file
            cls._instance._create_tables()
        return cls._instance

    def _get_connection(self):
        return sqlite3.connect(self.db_file)

    def _create_tables(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        event_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        capacity INTEGER
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS attendees (
                        attendee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        registration_date TEXT,
                        FOREIGN KEY (event_id) REFERENCES events (event_id),
                        UNIQUE(event_id, email)
                    )
                """)
        except sqlite3.Error as e:
            logger.error(f"Database table creation error: {e}")

    def create_event(self, event_id: str, name: str, capacity: int) -> bool:
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO events (event_id, name, capacity) VALUES (?, ?, ?)", (event_id, name, capacity))
                return True
            except sqlite3.IntegrityError:
                return False

    def get_event(self, event_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_attendee_count(self, event_id: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM attendees WHERE event_id = ?", (event_id,))
            count = cursor.fetchone()
            return count[0] if count else 0

    def register_attendee(self, event_id: str, name: str, email: str) -> int:
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO attendees (event_id, name, email, registration_date) VALUES (?, ?, ?, ?)",
                    (event_id, name, email, datetime.utcnow().isoformat() + "Z")
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return -1 # Indicates a duplicate registration

    def get_attendee(self, attendee_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendees WHERE attendee_id = ?", (attendee_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_event_attendees(self, event_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendees WHERE event_id = ? ORDER BY registration_date", (event_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

event_db_manager = EventDBManager(DB_FILE)

class CreateEventTool(BaseTool):
    """Creates a new event with a name and capacity."""
    def __init__(self, tool_name="create_event"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new event with a unique ID, name, and attendee capacity."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "A unique identifier for the event (e.g., 'tech_conf_2025')."},
                "name": {"type": "string", "description": "The official name of the event."},
                "capacity": {"type": "integer", "description": "The maximum number of attendees."}
            },
            "required": ["event_id", "name", "capacity"]
        }

    def execute(self, event_id: str, name: str, capacity: int, **kwargs: Any) -> str:
        success = event_db_manager.create_event(event_id, name, capacity)
        if success:
            report = {"message": f"Event '{name}' (ID: {event_id}) was created successfully with a capacity of {capacity}."}
        else:
            report = {"error": f"An event with ID '{event_id}' already exists."}
        return json.dumps(report, indent=2)

class RegisterAttendeeTool(BaseTool):
    """Registers an attendee for an event, checking capacity first."""
    def __init__(self, tool_name="register_attendee"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Registers a new attendee for an event, after checking for event existence and capacity."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The ID of the event to register for."},
                "name": {"type": "string", "description": "The full name of the attendee."},
                "email": {"type": "string", "description": "The email address of the attendee."}
            },
            "required": ["event_id", "name", "email"]
        }

    def execute(self, event_id: str, name: str, email: str, **kwargs: Any) -> str:
        event = event_db_manager.get_event(event_id)
        if not event:
            return json.dumps({"error": f"Event with ID '{event_id}' not found."})

        current_attendees = event_db_manager.get_attendee_count(event_id)
        if current_attendees >= event["capacity"]:
            return json.dumps({"error": f"Event '{event['name']}' is at full capacity ({event['capacity']}). Cannot register new attendees."})

        attendee_id = event_db_manager.register_attendee(event_id, name, email)
        if attendee_id != -1:
            report = {"message": "Registration successful.", "attendee_id": attendee_id, "name": name, "event_id": event_id}
        else:
            report = {"error": f"An attendee with the email '{email}' is already registered for event '{event_id}'."}
        return json.dumps(report, indent=2)

class GetAttendeeDetailsTool(BaseTool):
    """Retrieves registration details for a specific attendee."""
    def __init__(self, tool_name="get_attendee_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the full registration details for a specific attendee by their unique attendee ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"attendee_id": {"type": "integer", "description": "The unique ID of the attendee."}},
            "required": ["attendee_id"]
        }

    def execute(self, attendee_id: int, **kwargs: Any) -> str:
        attendee = event_db_manager.get_attendee(attendee_id)
        if attendee:
            return json.dumps(attendee, indent=2)
        else:
            return json.dumps({"error": f"Attendee with ID '{attendee_id}' not found."})

class ListEventAttendeesTool(BaseTool):
    """Lists all attendees for a specific event."""
    def __init__(self, tool_name="list_event_attendees"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves a list of all attendees registered for a specific event."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"event_id": {"type": "string", "description": "The ID of the event."}},
            "required": ["event_id"]
        }

    def execute(self, event_id: str, **kwargs: Any) -> str:
        event = event_db_manager.get_event(event_id)
        if not event:
            return json.dumps({"error": f"Event with ID '{event_id}' not found."})
        
        attendees = event_db_manager.get_event_attendees(event_id)
        report = {
            "event_id": event_id,
            "event_name": event["name"],
            "attendee_count": len(attendees),
            "attendees": attendees
        }
        return json.dumps(report, indent=2)