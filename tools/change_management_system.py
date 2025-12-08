import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import ChangeRequest
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class CreateChangeRequestTool(BaseTool):
    """Creates a new change request in the persistent database."""
    def __init__(self, tool_name="create_change_request"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new change request with a unique ID, title, description, requested by, priority, and impact."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "A unique ID for the new change request."},
                "title": {"type": "string", "description": "A brief title for the change request."},
                "description": {"type": "string", "description": "A detailed description of the proposed change."},
                "requested_by": {"type": "string", "description": "The name or ID of the person requesting the change."},
                "priority": {"type": "string", "description": "The priority of the change request.", "enum": ["low", "medium", "high"], "default": "medium"},
                "impact": {"type": "string", "description": "The potential impact of the change.", "enum": ["low", "medium", "high"], "default": "medium"}
            },
            "required": ["request_id", "title", "description", "requested_by"]
        }

    def execute(self, request_id: str, title: str, description: str, requested_by: str, priority: str = "medium", impact: str = "medium", **kwargs: Any) -> str:
        db = next(get_db())
        try:
            now = datetime.now().isoformat() + "Z"
            new_request = ChangeRequest(
                request_id=request_id,
                title=title,
                description=description,
                requested_by=requested_by,
                status="pending_approval",
                priority=priority,
                impact=impact,
                created_at=now,
                updated_at=now
            )
            db.add(new_request)
            db.commit()
            db.refresh(new_request)
            report = {"message": f"Change request '{request_id}' ('{title}') created successfully by '{requested_by}'. Status: pending_approval."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Change request with ID '{request_id}' already exists. Please choose a unique ID."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating change request: {e}")
            report = {"error": f"Failed to create change request: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetChangeRequestStatusTool(BaseTool):
    """Retrieves the current status and details of a specific change request."""
    def __init__(self, tool_name="get_change_request_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status and details of a specific change request."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"request_id": {"type": "string", "description": "The ID of the change request to retrieve status for."}},
            "required": ["request_id"]
        }

    def execute(self, request_id: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            change_request = db.query(ChangeRequest).filter(ChangeRequest.request_id == request_id).first()
            if not change_request:
                return json.dumps({"error": f"Change request with ID '{request_id}' not found."})
            
            report = {
                "request_id": change_request.request_id,
                "title": change_request.title,
                "description": change_request.description,
                "requested_by": change_request.requested_by,
                "status": change_request.status,
                "priority": change_request.priority,
                "impact": change_request.impact,
                "assigned_to": change_request.assigned_to,
                "created_at": change_request.created_at,
                "updated_at": change_request.updated_at
            }
        except Exception as e:
            logger.error(f"Error getting change request status: {e}")
            report = {"error": f"Failed to get change request status: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class UpdateChangeRequestStatusTool(BaseTool):
    """Updates the status of a change request."""
    def __init__(self, tool_name="update_change_request_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Updates the status of a change request (e.g., 'approved', 'rejected', 'in_progress', 'implemented', 'closed')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "description": "The ID of the change request to update."},
                "status": {"type": "string", "description": "The new status for the change request.", "enum": ["pending_approval", "approved", "rejected", "in_progress", "implemented", "closed"]},
                "assigned_to": {"type": "string", "description": "Optional: The name or ID of the person assigned to implement the change."}
            },
            "required": ["request_id", "status"]
        }

    def execute(self, request_id: str, status: str, assigned_to: str = None, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            change_request = db.query(ChangeRequest).filter(ChangeRequest.request_id == request_id).first()
            if not change_request:
                return json.dumps({"error": f"Change request with ID '{request_id}' not found."})
            
            change_request.status = status
            if assigned_to:
                change_request.assigned_to = assigned_to
            change_request.updated_at = datetime.now().isoformat() + "Z"
            db.commit()
            db.refresh(change_request)
            
            report = {"message": f"Change request '{request_id}' status updated to '{status}'."}
            if assigned_to:
                report["message"] += f" Assigned to '{assigned_to}'."
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating change request status: {e}")
            report = {"error": f"Failed to update change request status: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListChangeRequestsTool(BaseTool):
    """Lists all change requests, optionally filtering by status."""
    def __init__(self, tool_name="list_change_requests"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all change requests, optionally filtering by their current status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional: Filter requests by status.", "enum": ["pending_approval", "approved", "rejected", "in_progress", "implemented", "closed"]}
            },
            "required": []
        }

    def execute(self, status: str = None, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            query = db.query(ChangeRequest)
            if status:
                query = query.filter(ChangeRequest.status == status)
            
            requests = query.order_by(ChangeRequest.created_at.desc()).all()
            
            request_list = [{
                "request_id": r.request_id,
                "title": r.title,
                "description": r.description,
                "requested_by": r.requested_by,
                "status": r.status,
                "priority": r.priority,
                "impact": r.impact,
                "assigned_to": r.assigned_to,
                "created_at": r.created_at,
                "updated_at": r.updated_at
            } for r in requests]
            
            report = {
                "total_requests": len(request_list),
                "change_requests": request_list
            }
        except Exception as e:
            logger.error(f"Error listing change requests: {e}")
            report = {"error": f"Failed to list change requests: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
