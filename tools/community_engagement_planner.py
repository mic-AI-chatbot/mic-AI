import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import CommunityEvent, Volunteer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class PlanCommunityEventTool(BaseTool):
    """Plans a new community engagement event and stores it in the persistent database."""
    def __init__(self, tool_name="plan_community_event"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Plans a new community engagement event, defining its name, date, location, and description."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_name": {"type": "string", "description": "A unique name for the community event."},
                "date": {"type": "string", "description": "The date of the event (YYYY-MM-DD)."},
                "location": {"type": "string", "description": "The location where the event will take place."},
                "description": {"type": "string", "description": "Optional: A brief description of the event.", "default": ""}
            },
            "required": ["event_name", "date", "location"]
        }

    def execute(self, event_name: str, date: str, location: str, description: str = "", **kwargs: Any) -> str:
        db = next(get_db())
        try:
            now = datetime.now().isoformat() + "Z"
            new_event = CommunityEvent(
                event_name=event_name,
                date=date,
                location=location,
                description=description,
                status="planned",
                created_at=now
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            report = {"message": f"Community event '{event_name}' planned for {date} at {location}. Status: planned."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Event '{event_name}' already exists. Please choose a unique name."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error planning community event: {e}")
            report = {"error": f"Failed to plan community event: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ManageVolunteersTool(BaseTool):
    """Manages volunteers for a community event (add or assign role)."""
    def __init__(self, tool_name="manage_volunteers"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Manages volunteers for a specified community event, allowing for adding volunteers and assigning roles."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_name": {"type": "string", "description": "The name of the community event."},
                "volunteer_name": {"type": "string", "description": "The name of the volunteer to manage."},
                "action": {"type": "string", "description": "The action to perform.", "enum": ["add", "assign_role"]},
                "role": {"type": "string", "description": "Optional: The role to assign to the volunteer (e.g., 'registration', 'setup').", "default": "unassigned"}
            },
            "required": ["event_name", "volunteer_name", "action"]
        }

    def execute(self, event_name: str, volunteer_name: str, action: str, role: str = "unassigned", **kwargs: Any) -> str:
        db = next(get_db())
        try:
            event = db.query(CommunityEvent).filter(CommunityEvent.event_name == event_name).first()
            if not event:
                return json.dumps({"error": f"Event '{event_name}' not found. Please plan it first."})
            
            if action == "add":
                now = datetime.now().isoformat() + "Z"
                new_volunteer = Volunteer(
                    event_name=event_name,
                    volunteer_name=volunteer_name,
                    role=role,
                    added_at=now
                )
                db.add(new_volunteer)
                db.commit()
                db.refresh(new_volunteer)
                report = {"message": f"Volunteer '{volunteer_name}' added to event '{event_name}' with role '{role}'."}
            elif action == "assign_role":
                volunteer = db.query(Volunteer).filter(
                    Volunteer.event_name == event_name,
                    Volunteer.volunteer_name == volunteer_name
                ).first()
                if volunteer:
                    volunteer.role = role
                    db.commit()
                    db.refresh(volunteer)
                    report = {"message": f"Role '{role}' assigned to volunteer '{volunteer_name}' for event '{event_name}'."}
                else:
                    report = {"error": f"Volunteer '{volunteer_name}' not found in event '{event_name}'."}
            else:
                report = {"error": f"Unsupported action '{action}'. Supported actions are 'add' and 'assign_role'."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Volunteer '{volunteer_name}' already added to event '{event_name}'."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error managing volunteers: {e}")
            report = {"error": f"Failed to manage volunteers: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListCommunityEventsTool(BaseTool):
    """Lists all planned community events."""
    def __init__(self, tool_name="list_community_events"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all planned community events, showing their name, date, location, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            events = db.query(CommunityEvent).order_by(CommunityEvent.date.desc()).all()
            if not events:
                return json.dumps({"message": "No community events found."})
            
            event_list = [{
                "event_name": e.event_name,
                "date": e.date,
                "location": e.location,
                "status": e.status
            } for e in events]
            
            report = {"total_events": len(event_list), "events": event_list}
        except Exception as e:
            logger.error(f"Error listing community events: {e}")
            report = {"error": f"Failed to list community events: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListEventVolunteersTool(BaseTool):
    """Lists all volunteers for a specific community event."""
    def __init__(self, tool_name="list_event_volunteers"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all volunteers for a specific community event, showing their names and assigned roles."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"event_name": {"type": "string", "description": "The name of the community event to list volunteers for."}},
            "required": ["event_name"]
        }

    def execute(self, event_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            event = db.query(CommunityEvent).options(joinedload(CommunityEvent.volunteers)).filter(CommunityEvent.event_name == event_name).first()
            if not event:
                return json.dumps({"error": f"Event '{event_name}' not found."})
            
            volunteer_list = [{
                "volunteer_name": v.volunteer_name,
                "role": v.role,
                "added_at": v.added_at
            } for v in event.volunteers]

            if not volunteer_list:
                return json.dumps({"message": f"No volunteers found for event '{event_name}'."})
                
            report = {"event_name": event_name, "total_volunteers": len(volunteer_list), "volunteers": volunteer_list}
        except Exception as e:
            logger.error(f"Error listing event volunteers: {e}")
            report = {"error": f"Failed to list event volunteers: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
