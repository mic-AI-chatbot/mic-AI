import logging
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated venues and bookings
venues: Dict[str, Dict[str, Any]] = {
    "main_hall": {"capacity": 200, "price_per_hour": 150, "amenities": ["projector", "sound_system"]},
    "conference_room_a": {"capacity": 25, "price_per_hour": 50, "amenities": ["whiteboard", "teleconferencing"]},
    "garden_terrace": {"capacity": 100, "price_per_hour": 120, "amenities": ["outdoor_seating", "sound_system"]}
}
bookings: Dict[str, Dict[str, Any]] = {}

class VenueBookingSystemTool(BaseTool):
    """
    A tool for simulating a venue booking system.
    """
    def __init__(self, tool_name: str = "venue_booking_system_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates a venue booking system: checking availability, booking, canceling, and listing venues."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'list_venues', 'check_availability', 'book', 'cancel', 'get_booking_details'."
                },
                "venue_id": {"type": "string", "description": "The ID of the venue (e.g., 'main_hall')."},
                "booking_id": {"type": "string", "description": "The ID of an existing booking."},
                "date": {"type": "string", "description": "The date for the event (YYYY-MM-DD)."},
                "start_time": {"type": "string", "description": "The start time (HH:MM, 24-hour format)."},
                "duration_hours": {"type": "integer", "description": "The duration of the booking in hours."},
                "customer_name": {"type": "string", "description": "Name of the person booking the venue."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            actions = {
                "list_venues": self._list_venues,
                "check_availability": self._check_availability,
                "book": self._book_venue,
                "cancel": self._cancel_booking,
                "get_booking_details": self._get_booking_details,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VenueBookingSystemTool: {e}")
            return {"error": str(e)}

    def _list_venues(self, **kwargs) -> Dict:
        return {"available_venues": venues}

    def _check_availability(self, venue_id: str, date: str, start_time: str, duration_hours: int, **kwargs) -> Dict:
        if not all([venue_id, date, start_time, duration_hours]):
            raise ValueError("'venue_id', 'date', 'start_time', and 'duration_hours' are required.")
        
        is_available, reason = self._is_slot_available(venue_id, date, start_time, duration_hours)
        return {"venue_id": venue_id, "is_available": is_available, "reason": reason}

    def _book_venue(self, venue_id: str, date: str, start_time: str, duration_hours: int, customer_name: str, **kwargs) -> Dict:
        if not all([venue_id, date, start_time, duration_hours, customer_name]):
            raise ValueError("Missing required parameters for booking.")

        is_available, reason = self._is_slot_available(venue_id, date, start_time, duration_hours)
        if not is_available:
            raise ValueError(f"Cannot book venue. Reason: {reason}")

        booking_id = f"BKG-{random.randint(1000, 9999)}"  # nosec B311
        venue_details = venues[venue_id]
        total_price = venue_details["price_per_hour"] * duration_hours
        
        new_booking = {
            "booking_id": booking_id,
            "venue_id": venue_id,
            "customer_name": customer_name,
            "date": date,
            "start_time": start_time,
            "duration_hours": duration_hours,
            "total_price": total_price,
            "status": "confirmed"
        }
        bookings[booking_id] = new_booking
        logger.info(f"Venue '{venue_id}' booked successfully with ID {booking_id}.")
        return {"message": "Booking successful.", "booking_details": new_booking}

    def _cancel_booking(self, booking_id: str, **kwargs) -> Dict:
        if not booking_id:
            raise ValueError("'booking_id' is required to cancel.")
        if booking_id not in bookings:
            raise ValueError(f"Booking ID '{booking_id}' not found.")
            
        bookings[booking_id]["status"] = "cancelled"
        logger.info(f"Booking '{booking_id}' has been cancelled.")
        return {"message": "Booking cancelled successfully.", "booking_id": booking_id}

    def _get_booking_details(self, booking_id: str, **kwargs) -> Dict:
        if not booking_id:
            raise ValueError("'booking_id' is required.")
        if booking_id not in bookings:
            raise ValueError(f"Booking ID '{booking_id}' not found.")
        return {"booking_details": bookings[booking_id]}

    def _is_slot_available(self, venue_id: str, date: str, start_time: str, duration_hours: int) -> (bool, str):
        if venue_id not in venues:
            return False, f"Venue ID '{venue_id}' does not exist."
            
        try:
            requested_start = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            requested_end = requested_start + timedelta(hours=duration_hours)
        except ValueError:
            return False, "Invalid date or time format. Use YYYY-MM-DD and HH:MM."

        for booking in bookings.values():
            if booking["venue_id"] == venue_id and booking["status"] == "confirmed":
                booked_start = datetime.strptime(f"{booking['date']} {booking['start_time']}", "%Y-%m-%d %H:%M")
                booked_end = booked_start + timedelta(hours=booking["duration_hours"])
                
                # Check for overlap
                if max(requested_start, booked_start) < min(requested_end, booked_end):
                    return False, f"Time slot conflicts with existing booking {booking['booking_id']}."
        
        return True, "Time slot is available."