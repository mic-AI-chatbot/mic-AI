import logging
import json
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import UserEvent
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class TrackUserEventTool(BaseTool):
    """Tracks a user event and stores it in the database."""
    def __init__(self, tool_name="track_user_event"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Tracks a specific user event (e.g., 'button_click', 'page_view', 'purchase') with associated properties for behavioral analysis."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user performing the event."},
                "event_name": {"type": "string", "description": "The name of the event to track (e.g., 'login', 'add_to_cart')."},
                "properties": {
                    "type": "object",
                    "description": "Optional: A dictionary of additional properties for the event (e.g., {\"product_id\": \"XYZ\", \"value\": 99.99})."
                }
            },
            "required": ["user_id", "event_name"]
        }

    def execute(self, user_id: str, event_name: str, properties: Dict[str, Any] = None, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            new_event = UserEvent(
                user_id=user_id,
                event_name=event_name,
                timestamp=datetime.now().isoformat() + "Z",
                properties=json.dumps(properties) if properties else "{}"
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            report = {"message": f"User '{user_id}' event '{event_name}' tracked successfully.", "event_id": new_event.id}
        except Exception as e:
            db.rollback()
            logger.error(f"Error tracking user event: {e}")
            report = {"error": f"Failed to track user event: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class AnalyzeUserJourneysTool(BaseTool):
    """Analyzes user journeys to identify common paths and drop-off points."""
    def __init__(self, tool_name="analyze_user_journeys"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes user journeys to identify common paths, drop-off points, and event sequences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Optional: The ID of a specific user to analyze their journey. If not provided, general common paths are analyzed."},
                "min_journey_length": {"type": "integer", "description": "Minimum number of events for a journey to be considered in general analysis.", "default": 3}
            },
            "required": []
        }

    def execute(self, user_id: str = None, min_journey_length: int = 3, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            if user_id:
                events = db.query(UserEvent).filter(UserEvent.user_id == user_id).order_by(UserEvent.timestamp).all()
                if not events:
                    return json.dumps({"error": f"No events found for user '{user_id}'."})
                
                journey = [e.event_name for e in events]
                report = {
                    "user_id": user_id,
                    "user_journey": journey,
                    "message": f"Detailed journey for user '{user_id}' analyzed."
                }
            else:
                all_events = db.query(UserEvent).order_by(UserEvent.user_id, UserEvent.timestamp).all()
                journeys_by_user = {}
                for event in all_events:
                    journeys_by_user.setdefault(event.user_id, []).append(event.event_name)
                
                common_paths = Counter()
                for uid, journey in journeys_by_user.items():
                    if len(journey) >= min_journey_length:
                        for i in range(len(journey) - min_journey_length + 1):
                            common_paths[tuple(journey[i:i+min_journey_length])] += 1
                
                top_paths = common_paths.most_common(5)
                
                report = {
                    "message": "General user journey analysis performed.",
                    "top_common_paths": [{"path": list(p), "count": c} for p, c in top_paths]
                }
        except Exception as e:
            logger.error(f"Error analyzing user journeys: {e}")
            report = {"error": f"Failed to analyze user journeys: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetConversionFunnelTool(BaseTool):
    """Calculates conversion rates for a specified event funnel."""
    def __init__(self, tool_name="get_conversion_funnel"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Calculates conversion rates for a specified sequence of events (a funnel), showing user progression and drop-off at each step."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "funnel_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "An ordered list of event names that define the conversion funnel (e.g., ['page_view', 'add_to_cart', 'purchase'])."
                }
            },
            "required": ["funnel_steps"]
        }

    def execute(self, funnel_steps: List[str], **kwargs: Any) -> str:
        if not funnel_steps:
            return json.dumps({"error": "Funnel steps cannot be empty."})

        db = next(get_db())
        try:
            all_events = db.query(UserEvent).order_by(UserEvent.user_id, UserEvent.timestamp).all()
            
            user_event_sequences = {}
            for event in all_events:
                user_event_sequences.setdefault(event.user_id, []).append(event)
            
            for user_id in user_event_sequences:
                user_event_sequences[user_id].sort(key=lambda x: x.timestamp)

            funnel_report = []
            users_at_each_step = [set() for _ in funnel_steps]

            for user_id, events in user_event_sequences.items():
                current_funnel_step_index = 0
                for event in events:
                    if current_funnel_step_index < len(funnel_steps) and event.event_name == funnel_steps[current_funnel_step_index]:
                        users_at_each_step[current_funnel_step_index].add(user_id)
                        current_funnel_step_index += 1
            
            for i, step in enumerate(funnel_steps):
                current_users = users_at_each_step[i]
                
                if i == 0:
                    starting_users_for_step = len(current_users)
                    conversion_rate_from_previous = 100.0 if starting_users_for_step > 0 else 0.0
                else:
                    previous_users = users_at_each_step[i-1]
                    converted_users = len(current_users.intersection(previous_users))
                    starting_users_for_step = len(previous_users)
                    conversion_rate_from_previous = (converted_users / starting_users_for_step) * 100 if starting_users_for_step > 0 else 0.0
                
                funnel_report.append({
                    "step": step,
                    "users_completed_step": len(current_users),
                    "conversion_rate_from_previous_step_percent": round(conversion_rate_from_previous, 2)
                })
        except Exception as e:
            logger.error(f"Error calculating conversion funnel: {e}")
            report = {"error": f"Failed to calculate conversion funnel: {e}"}
        finally:
            db.close()
        return json.dumps(funnel_report, indent=2)
