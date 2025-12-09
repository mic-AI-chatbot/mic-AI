import logging
import random
import string
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated tickets
tickets: Dict[str, Dict[str, Any]] = {}

class TicketingManagementTool(BaseTool):
    """
    A tool for simulating ticketing management actions.
    """
    def __init__(self, tool_name: str = "ticketing_management_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates ticketing management actions, such as creating, updating, getting, or listing tickets."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string", 
                    "description": "The command to execute: 'create_ticket', 'update_ticket', 'get_ticket_details', or 'list_tickets'."
                },
                "ticket_id": {"type": "string", "description": "The ID of the ticket. If not provided for creation, a random one will be generated."},
                "title": {"type": "string", "description": "The title of the ticket (required for 'create_ticket')."},
                "description": {"type": "string", "description": "The description of the ticket (required for 'create_ticket')."},
                "priority": {"type": "string", "description": "The priority of the ticket (e.g., 'low', 'medium', 'high')."},
                "status": {"type": "string", "description": "The status of the ticket (e.g., 'open', 'in_progress', 'closed')."},
                "filter_status": {"type": "string", "description": "Filter by status for 'list_tickets' (e.g., 'open', 'closed')."}
            },
            "required": ["command"]
        }

    def execute(self, command: str, **kwargs: Dict[str, Any]) -> str:
        try:
            if command == "create_ticket":
                title = kwargs.get("title")
                description = kwargs.get("description")
                if not title or not description:
                    return "Error: 'title' and 'description' are required for creating a ticket."
                
                ticket_id = kwargs.get("ticket_id") or self._generate_ticket_id()
                priority = kwargs.get("priority", "medium")
                return self._create_ticket(ticket_id, title, description, priority)

            elif command == "update_ticket":
                ticket_id = kwargs.get("ticket_id")
                if not ticket_id:
                    return "Error: 'ticket_id' is required for updating a ticket."
                
                return self._update_ticket(ticket_id, kwargs.get("status"), kwargs.get("priority"))

            elif command == "get_ticket_details":
                ticket_id = kwargs.get("ticket_id")
                if not ticket_id:
                    return "Error: 'ticket_id' is required to get ticket details."
                return self._get_ticket_details(ticket_id)

            elif command == "list_tickets":
                return self._list_tickets(kwargs.get("filter_status"))

            else:
                return f"Error: Unknown command '{command}'. Available commands are: create_ticket, update_ticket, get_ticket_details, list_tickets."
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred in TicketingManagementTool: {e}")
            return f"An unexpected error occurred: {e}"

    def _generate_ticket_id(self, length=8):
        """Generates a random alphanumeric ticket ID."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))  # nosec B311

    def _create_ticket(self, ticket_id: str, title: str, description: str, priority: str = "medium") -> str:
        logger.info(f"Attempting to create ticket: {ticket_id}")
        if ticket_id in tickets:
            raise ValueError(f"Ticket '{ticket_id}' already exists.")
        
        tickets[ticket_id] = {
            "title": title,
            "description": description,
            "priority": priority,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Ticket '{ticket_id}' created successfully.")
        return f"Ticket '{ticket_id}' created successfully. Title: '{title}', Priority: '{priority}'."

    def _update_ticket(self, ticket_id: str, status: Optional[str] = None, priority: Optional[str] = None) -> str:
        logger.info(f"Attempting to update ticket: {ticket_id}")
        if ticket_id not in tickets:
            raise ValueError(f"Ticket '{ticket_id}' not found.")
        
        if status:
            tickets[ticket_id]["status"] = status
        if priority:
            tickets[ticket_id]["priority"] = priority
        
        tickets[ticket_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Ticket '{ticket_id}' updated successfully.")
        return f"Ticket '{ticket_id}' updated. Current status: {tickets[ticket_id]['status']}, Priority: {tickets[ticket_id]['priority']}."

    def _get_ticket_details(self, ticket_id: str) -> str:
        logger.info(f"Attempting to get ticket details for: {ticket_id}")
        if ticket_id not in tickets:
            raise ValueError(f"Ticket '{ticket_id}' not found.")
        
        details = tickets[ticket_id]
        details_message = (
            f"--- Ticket Details for '{ticket_id}' ---\n"
            f"Title: {details.get('title')}\n"
            f"Description: {details.get('description')}\n"
            f"Priority: {details.get('priority')}\n"
            f"Status: {details.get('status')}\n"
            f"Created At: {details.get('created_at')}\n"
            f"Last Updated: {details.get('updated_at', 'N/A')}"
        )
        logger.info(f"Details retrieved for ticket '{ticket_id}'.")
        return details_message

    def _list_tickets(self, filter_status: Optional[str] = None) -> str:
        logger.info(f"Listing tickets with filter: {filter_status}")
        if not tickets:
            return "There are currently no tickets."

        filtered_tickets = tickets.items()
        if filter_status:
            filtered_tickets = [item for item in filtered_tickets if item[1]['status'] == filter_status]

        if not filtered_tickets:
            return f"No tickets found with status '{filter_status}'."

        report = "--- Ticket List ---\n"
        for ticket_id, details in filtered_tickets:
            report += f"ID: {ticket_id}, Title: {details['title']}, Status: {details['status']}, Priority: {details['priority']}\n"
        
        return report
        return report