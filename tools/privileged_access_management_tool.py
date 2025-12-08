import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PrivilegedAccessManagementSimulatorTool(BaseTool):
    """
    A tool that simulates Privileged Access Management (PAM), allowing for
    requesting, approving, revoking, and auditing privileged access sessions.
    """

    def __init__(self, tool_name: str = "PrivilegedAccessManagementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.requests_file = os.path.join(self.data_dir, "access_requests.json")
        self.sessions_file = os.path.join(self.data_dir, "privileged_sessions.json")
        
        # Access requests: {request_id: {user_id: ..., resource_id: ..., status: ...}}
        self.access_requests: Dict[str, Dict[str, Any]] = self._load_data(self.requests_file, default={})
        # Privileged sessions: {session_id: {user_id: ..., resource_id: ..., status: ...}}
        self.privileged_sessions: Dict[str, Dict[str, Any]] = self._load_data(self.sessions_file, default={})

    @property
    def description(self) -> str:
        return "Simulates PAM: request, approve, revoke, and audit privileged access sessions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["request_access", "approve_access", "revoke_access", "audit_sessions"]},
                "user_id": {"type": "string"},
                "resource_id": {"type": "string"},
                "duration_hours": {"type": "integer", "minimum": 1, "maximum": 24},
                "request_id": {"type": "string"},
                "approver_id": {"type": "string"},
                "session_id": {"type": "string"}
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

    def _save_requests(self):
        with open(self.requests_file, 'w') as f: json.dump(self.access_requests, f, indent=2)

    def _save_sessions(self):
        with open(self.sessions_file, 'w') as f: json.dump(self.privileged_sessions, f, indent=2)

    def request_access(self, user_id: str, resource_id: str, duration_hours: int) -> Dict[str, Any]:
        """Simulates requesting privileged access to a resource."""
        request_id = f"REQ-{user_id}-{resource_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        if request_id in self.access_requests: raise ValueError(f"Request '{request_id}' already exists.")
        
        new_request = {
            "id": request_id, "user_id": user_id, "resource_id": resource_id,
            "duration_hours": duration_hours, "status": "pending",
            "requested_at": datetime.now().isoformat()
        }
        self.access_requests[request_id] = new_request
        self._save_requests()
        return new_request

    def approve_access(self, request_id: str, approver_id: str) -> Dict[str, Any]:
        """Simulates approving a privileged access request."""
        request = self.access_requests.get(request_id)
        if not request: raise ValueError(f"Access request '{request_id}' not found.")
        if request["status"] != "pending": raise ValueError(f"Request '{request_id}' is not pending.")
        
        request["status"] = "approved"
        request["approver_id"] = approver_id
        request["approved_at"] = datetime.now().isoformat()
        self._save_requests()

        # Create a simulated privileged session
        session_id = f"SESS-{request_id}"
        session_end_time = datetime.now() + timedelta(hours=request["duration_hours"])
        new_session = {
            "id": session_id, "user_id": request["user_id"], "resource_id": request["resource_id"],
            "start_time": datetime.now().isoformat(), "end_time": session_end_time.isoformat(),
            "status": "active", "request_id": request_id
        }
        self.privileged_sessions[session_id] = new_session
        self._save_sessions()
        return {"status": "success", "message": f"Request '{request_id}' approved. Session '{session_id}' active."
}

    def revoke_access(self, session_id: str) -> Dict[str, Any]:
        """Simulates revoking an active privileged access session."""
        session = self.privileged_sessions.get(session_id)
        if not session: raise ValueError(f"Session '{session_id}' not found.")
        if session["status"] != "active": raise ValueError(f"Session '{session_id}' is not active.")
        
        session["status"] = "revoked"
        session["revoked_at"] = datetime.now().isoformat()
        self._save_sessions()
        return {"status": "success", "message": f"Session '{session_id}' revoked."}

    def audit_sessions(self, user_id: Optional[str] = None, resource_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Audits privileged sessions, optionally filtered by user or resource."""
        filtered_sessions = list(self.privileged_sessions.values())
        if user_id: filtered_sessions = [s for s in filtered_sessions if s["user_id"] == user_id]
        if resource_id: filtered_sessions = [s for s in filtered_sessions if s["resource_id"] == resource_id]
        
        return filtered_sessions

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "request_access":
            user_id = kwargs.get('user_id')
            resource_id = kwargs.get('resource_id')
            duration_hours = kwargs.get('duration_hours')
            if not all([user_id, resource_id, duration_hours]):
                raise ValueError("Missing 'user_id', 'resource_id', or 'duration_hours' for 'request_access' operation.")
            return self.request_access(user_id, resource_id, duration_hours)
        elif operation == "approve_access":
            request_id = kwargs.get('request_id')
            approver_id = kwargs.get('approver_id')
            if not all([request_id, approver_id]):
                raise ValueError("Missing 'request_id' or 'approver_id' for 'approve_access' operation.")
            return self.approve_access(request_id, approver_id)
        elif operation == "revoke_access":
            session_id = kwargs.get('session_id')
            if not session_id:
                raise ValueError("Missing 'session_id' for 'revoke_access' operation.")
            return self.revoke_access(session_id)
        elif operation == "audit_sessions":
            # user_id and resource_id are optional, so no strict check needed here
            return self.audit_sessions(kwargs.get('user_id'), kwargs.get('resource_id'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PrivilegedAccessManagementSimulatorTool functionality...")
    temp_dir = "temp_pam_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    pam_tool = PrivilegedAccessManagementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Request access
        print("\n--- Requesting access for 'dev_alice' to 'prod_db' for 2 hours ---")
        request_result = pam_tool.execute(operation="request_access", user_id="dev_alice", resource_id="prod_db", duration_hours=2)
        request_id = request_result["id"]
        print(json.dumps(request_result, indent=2))

        # 2. Approve access
        print(f"\n--- Approving request '{request_id}' by 'security_bob' ---")
        approve_result = pam_tool.execute(operation="approve_access", request_id=request_id, approver_id="security_bob")
        session_id = approve_result["message"].split("'")[3] # Extract session ID
        print(json.dumps(approve_result, indent=2))

        # 3. Audit sessions
        print("\n--- Auditing active sessions ---")
        active_sessions = pam_tool.execute(operation="audit_sessions")
        print(json.dumps(active_sessions, indent=2))

        # 4. Revoke access
        print(f"\n--- Revoking session '{session_id}' ---")
        revoke_result = pam_tool.execute(operation="revoke_access", session_id=session_id)
        print(json.dumps(revoke_result, indent=2))

        # 5. Audit sessions again to confirm revocation
        print("\n--- Auditing sessions after revocation ---")
        audited_sessions_after = pam_tool.execute(operation="audit_sessions")
        print(json.dumps(audited_sessions_after, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")