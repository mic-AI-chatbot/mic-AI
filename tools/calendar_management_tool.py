import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import CalendarEvent
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

logger = logging.getLogger(__name__)

class CreateCalendarEventTool(BaseTool):
    """Creates a new calendar event in the persistent database."""
    def __init__(self, tool_name="create_calendar_event"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new calendar event with a summary, description, location, start/end datetimes, and optional attendees."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "A unique identifier for the event."},
                "summary": {"type": "string", "description": "The title or summary of the event."},
                "description": {"type": "string", "description": "Optional: A detailed description of the event.", "default": ""},
                "location": {"type": "string", "description": "Optional: The physical location of the event.", "default": ""},
                "start_datetime": {"type": "string", "description": "The start date and time in 'YYYY-MM-DD HH:MM' format."},
                "end_datetime": {"type": "string", "description": "The end date and time in 'YYYY-MM-DD HH:MM' format."},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "Optional: A list of attendees' email addresses.", "default": []}
            },
            "required": ["event_id", "summary", "start_datetime", "end_datetime"]
        }

    def execute(self, event_id: str, summary: str, start_datetime: str, end_datetime: str, description: str = "", location: str = "", attendees: List[str] = None, **kwargs: Any) -> str:
        try:
            start = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M')
            end = datetime.strptime(end_datetime, '%Y-%m-%d %H:%M')
        except ValueError:
            return json.dumps({"error": "Invalid datetime format. Please use 'YYYY-MM-DD HH:MM'."})

        if attendees is None:
            attendees = []

        db = next(get_db())
        try:
            new_event = CalendarEvent(
                event_id=event_id,
                summary=summary,
                description=description,
                location=location,
                start_datetime=start.isoformat(),
                end_datetime=end.isoformat(),
                attendees=json.dumps(attendees),
                created_at=datetime.now().isoformat() + "Z"
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            report = {"message": f"Calendar event '{summary}' created with ID '{event_id}'."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Event with ID '{event_id}' already exists. Please choose a unique ID."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating calendar event: {e}")
            report = {"error": f"Failed to create calendar event: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListCalendarEventsTool(BaseTool):
    """Lists existing calendar events."""
    def __init__(self, tool_name="list_calendar_events"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all existing calendar events, optionally filtering by a keyword in the summary or a date range."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Optional: A keyword to filter events by their summary."},
                "start_date": {"type": "string", "description": "Optional: Filter events starting on or after this date (YYYY-MM-DD)."},
                "end_date": {"type": "string", "description": "Optional: Filter events ending on or before this date (YYYY-MM-DD)."}
            },
            "required": []
        }

    def execute(self, keyword: str = None, start_date: str = None, end_date: str = None, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            query = db.query(CalendarEvent)
            if keyword:
                query = query.filter(CalendarEvent.summary.ilike(f"%{keyword}%"))
            if start_date:
                query = query.filter(CalendarEvent.start_datetime >= datetime.strptime(start_date, '%Y-%m-%d').isoformat())
            if end_date:
                query = query.filter(CalendarEvent.end_datetime <= (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).isoformat())
            
            events = query.order_by(CalendarEvent.start_datetime).all()
            if not events:
                return json.dumps({"message": "No calendar events found matching the criteria."})
            
            event_list = [{
                "event_id": e.event_id,
                "summary": e.summary,
                "description": e.description,
                "location": e.location,
                "start_datetime": e.start_datetime,
                "end_datetime": e.end_datetime,
                "attendees": json.loads(e.attendees),
                "created_at": e.created_at
            } for e in events]
            
            report = {"total_events": len(event_list), "events": event_list}
        except Exception as e:
            logger.error(f"Error listing calendar events: {e}")
            report = {"error": f"Failed to list calendar events: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class UpdateCalendarEventTool(BaseTool):
    """Updates an existing calendar event."""
    def __init__(self, tool_name="update_calendar_event"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Updates an existing calendar event's details (summary, description, location, start/end datetimes, attendees)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The ID of the event to update."},
                "summary": {"type": "string", "description": "Optional: The new title or summary of the event."},
                "description": {"type": "string", "description": "Optional: The new detailed description of the event."},
                "location": {"type": "string", "description": "Optional: The new physical location of the event."},
                "start_datetime": {"type": "string", "description": "Optional: The new start date and time in 'YYYY-MM-DD HH:MM' format."},
                "end_datetime": {"type": "string", "description": "Optional: The new end date and time in 'YYYY-MM-DD HH:MM' format."},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "Optional: The new list of attendees' email addresses."}
            },
            "required": ["event_id"]
        }

    def execute(self, event_id: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            event = db.query(CalendarEvent).filter(CalendarEvent.event_id == event_id).first()
            if not event:
                return json.dumps({"error": f"Event with ID '{event_id}' not found."})
            
            updates_made = False
            if "summary" in kwargs and kwargs["summary"] is not None:
                event.summary = kwargs["summary"]
                updates_made = True
            if "description" in kwargs and kwargs["description"] is not None:
                event.description = kwargs["description"]
                updates_made = True
            if "location" in kwargs and kwargs["location"] is not None:
                event.location = kwargs["location"]
                updates_made = True
            if "start_datetime" in kwargs and kwargs["start_datetime"] is not None:
                try:
                    event.start_datetime = datetime.strptime(kwargs["start_datetime"], '%Y-%m-%d %H:%M').isoformat()
                    updates_made = True
                except ValueError:
                    return json.dumps({"error": "Invalid datetime format for start_datetime. Please use 'YYYY-MM-DD HH:MM'."})
            if "end_datetime" in kwargs and kwargs["end_datetime"] is not None:
                try:
                    event.end_datetime = datetime.strptime(kwargs["end_datetime"], '%Y-%m-%d %H:%M').isoformat()
                    updates_made = True
                except ValueError:
                    return json.dumps({"error": "Invalid datetime format for end_datetime. Please use 'YYYY-MM-DD HH:MM'."})
            if "attendees" in kwargs and kwargs["attendees"] is not None:
                event.attendees = json.dumps(kwargs["attendees"])
                updates_made = True
            
            if updates_made:
                db.commit()
                db.refresh(event)
                report = {"message": f"Event '{event_id}' updated successfully."}
            else:
                report = {"message": "No valid fields provided for update or no changes made."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating calendar event: {e}")
            report = {"error": f"Failed to update calendar event: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class DeleteCalendarEventTool(BaseTool):
    """Deletes a calendar event."""
    def __init__(self, tool_name="delete_calendar_event"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deletes a calendar event using its unique event ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"event_id": {"type": "string", "description": "The ID of the event to delete."}},
            "required": ["event_id"]
        }

    def execute(self, event_id: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            event = db.query(CalendarEvent).filter(CalendarEvent.event_id == event_id).first()
            if event:
                db.delete(event)
                db.commit()
                report = {"message": f"Event '{event_id}' deleted successfully."}
            else:
                report = {"error": f"Event with ID '{event_id}' not found."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting calendar event: {e}")
            report = {"error": f"Failed to delete calendar event: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class FindAvailableTimeSlotsTool(BaseTool):
    """Finds available time slots in a calendar."""
    def __init__(self, tool_name="find_available_time_slots"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Finds available time slots within a specified date range and duration, considering existing events."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "The start date for searching available slots (YYYY-MM-DD)."},
                "end_date": {"type": "string", "description": "The end date for searching available slots (YYYY-MM-DD)."},
                "duration_minutes": {"type": "integer", "description": "The required duration for the time slot in minutes."}
            },
            "required": ["start_date", "end_date", "duration_minutes"]
        }

    def execute(self, start_date: str, end_date: str, duration_minutes: int, **kwargs: Any) -> str:
        try:
            search_start = datetime.strptime(start_date, '%Y-%m-%d')
            search_end = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return json.dumps({"error": "Invalid date format. Please use 'YYYY-MM-DD'."})

        db = next(get_db())
        try:
            # Fetch all events that overlap with the search range
            # An event overlaps if (event.start < search_end_plus_one_day AND event.end > search_start)
            all_events_query = db.query(CalendarEvent).filter(
                or_(
                    CalendarEvent.start_datetime < (search_end + timedelta(days=1)).isoformat(),
                    CalendarEvent.end_datetime > search_start.isoformat()
                )
            ).order_by(CalendarEvent.start_datetime).all()
            
            busy_slots = []
            for event in all_events_query:
                busy_slots.append({
                    "start": datetime.fromisoformat(event.start_datetime),
                    "end": datetime.fromisoformat(event.end_datetime)
                })
            
            available_slots = []
            current_day = search_start
            while current_day <= search_end:
                # Assume working hours from 9 AM to 5 PM (adjust as needed)
                day_start_time = current_day.replace(hour=9, minute=0, second=0, microsecond=0)
                day_end_time = current_day.replace(hour=17, minute=0, second=0, microsecond=0)

                # Ensure we don't suggest slots in the past for the current day
                if current_day.date() == datetime.now().date() and day_start_time < datetime.now():
                    day_start_time = datetime.now()

                temp_time = day_start_time
                while temp_time + timedelta(minutes=duration_minutes) <= day_end_time:
                    is_available = True
                    potential_slot_end = temp_time + timedelta(minutes=duration_minutes)
                    
                    for busy in busy_slots:
                        # Check for overlap: (start1 < end2 and end1 > start2)
                        if not (potential_slot_end <= busy["start"] or temp_time >= busy["end"]):
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append({
                            "start": temp_time.strftime('%Y-%m-%d %H:%M'),
                            "end": potential_slot_end.strftime('%Y-%m-%d %H:%M')
                        })
                    
                    temp_time += timedelta(minutes=30) # Check every 30 minutes for new slots
                current_day += timedelta(days=1)
            
            report = {
                "search_start_date": start_date,
                "search_end_date": end_date,
                "required_duration_minutes": duration_minutes,
                "available_slots": available_slots[:10] # Show up to 10 available slots for brevity
            }
        except Exception as e:
            logger.error(f"Error finding available time slots: {e}")
            report = {"error": f"Failed to find available time slots: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
