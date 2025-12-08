import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RealtimeCollaborationSimulatorTool(BaseTool):
    """
    A tool that simulates real-time collaboration sessions, allowing for
    starting sessions, editing documents, sending messages, and tracking activity.
    """

    def __init__(self, tool_name: str = "RealtimeCollaborationSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.sessions_file = os.path.join(self.data_dir, "collaboration_sessions.json")
        # Sessions structure: {session_id: {document_id: ..., content: ..., participants: [], activity_log: []}}
        self.collaboration_sessions: Dict[str, Dict[str, Any]] = self._load_data(self.sessions_file, default={})

    @property
    def description(self) -> str:
        return "Simulates real-time collaboration: start sessions, edit documents, send messages, track activity."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["start_session", "edit_document", "send_message", "get_session_status"]},
                "session_id": {"type": "string"},
                "document_id": {"type": "string"},
                "initial_content": {"type": "string"},
                "user_id": {"type": "string"},
                "new_content": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["operation", "session_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.sessions_file, 'w') as f: json.dump(self.collaboration_sessions, f, indent=2)

    def start_session(self, session_id: str, document_id: str, initial_content: str, user_id: str) -> Dict[str, Any]:
        """Starts a new real-time collaboration session."""
        if session_id in self.collaboration_sessions: raise ValueError(f"Session '{session_id}' already exists.")
        
        new_session = {
            "id": session_id, "document_id": document_id, "content": initial_content,
            "participants": [user_id], "activity_log": [],
            "started_at": datetime.now().isoformat()
        }
        new_session["activity_log"].append({"timestamp": datetime.now().isoformat(), "user": user_id, "action": "session_started"})
        self.collaboration_sessions[session_id] = new_session
        self._save_data()
        return new_session

    def edit_document(self, session_id: str, user_id: str, new_content: str) -> Dict[str, Any]:
        """Simulates a user editing the document in a session."""
        session = self.collaboration_sessions.get(session_id)
        if not session: raise ValueError(f"Session '{session_id}' not found.")
        
        session["content"] = new_content
        if user_id not in session["participants"]: session["participants"].append(user_id)
        session["activity_log"].append({"timestamp": datetime.now().isoformat(), "user": user_id, "action": "edited_document"})
        self._save_data()
        return {"status": "success", "message": f"User '{user_id}' edited document in session '{session_id}'."}

    def send_message(self, session_id: str, user_id: str, message: str) -> Dict[str, Any]:
        """Simulates a user sending a message in the session chat."""
        session = self.collaboration_sessions.get(session_id)
        if not session: raise ValueError(f"Session '{session_id}' not found.")
        
        if user_id not in session["participants"]: session["participants"].append(user_id)
        session["activity_log"].append({"timestamp": datetime.now().isoformat(), "user": user_id, "action": "sent_message", "message": message})
        self._save_data()
        return {"status": "success", "message": f"User '{user_id}' sent message in session '{session_id}'."}

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Retrieves the current status of a collaboration session."""
        session = self.collaboration_sessions.get(session_id)
        if not session: raise ValueError(f"Session '{session_id}' not found.")
        return session

    def execute(self, operation: str, session_id: str, **kwargs: Any) -> Any:
        if operation == "start_session":
            document_id = kwargs.get('document_id')
            initial_content = kwargs.get('initial_content')
            user_id = kwargs.get('user_id')
            if not all([document_id, initial_content, user_id]):
                raise ValueError("Missing 'document_id', 'initial_content', or 'user_id' for 'start_session' operation.")
            return self.start_session(session_id, document_id, initial_content, user_id)
        elif operation == "edit_document":
            user_id = kwargs.get('user_id')
            new_content = kwargs.get('new_content')
            if not all([user_id, new_content]):
                raise ValueError("Missing 'user_id' or 'new_content' for 'edit_document' operation.")
            return self.edit_document(session_id, user_id, new_content)
        elif operation == "send_message":
            user_id = kwargs.get('user_id')
            message = kwargs.get('message')
            if not all([user_id, message]):
                raise ValueError("Missing 'user_id' or 'message' for 'send_message' operation.")
            return self.send_message(session_id, user_id, message)
        elif operation == "get_session_status":
            # No additional kwargs required for get_session_status
            return self.get_session_status(session_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RealtimeCollaborationSimulatorTool functionality...")
    temp_dir = "temp_collaboration_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    collab_tool = RealtimeCollaborationSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Start a collaboration session
        print("\n--- Starting collaboration session 'proj_doc_edit' ---")
        session_result = collab_tool.execute(operation="start_session", session_id="proj_doc_edit", document_id="project_plan.md", initial_content="# Project Plan\n", user_id="alice")
        print(json.dumps(session_result, indent=2))

        # 2. Simulate user editing the document
        print("\n--- User 'bob' edits the document ---")
        collab_tool.execute(operation="edit_document", session_id="proj_doc_edit", user_id="bob", new_content="# Project Plan\n## Introduction\nThis is a new project.")
        print("Document edited.")

        # 3. Simulate user sending a message
        print("\n--- User 'alice' sends a message ---")
        collab_tool.execute(operation="send_message", session_id="proj_doc_edit", user_id="alice", message="Hi Bob, I've updated the intro.")
        print("Message sent.")

        # 4. Get session status
        print("\n--- Getting session status for 'proj_doc_edit' ---")
        status = collab_tool.execute(operation="get_session_status", session_id="proj_doc_edit")
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")