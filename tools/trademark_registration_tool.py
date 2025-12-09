import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated trademarks
trademarks: Dict[str, Dict[str, Any]] = {}

class TrademarkRegistrationTool(BaseTool):
    """
    A tool for simulating trademark registration actions.
    """
    def __init__(self, tool_name: str = "trademark_registration_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates trademark actions: checking availability, registration, and status checks."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string", 
                    "description": "The command: 'check_availability', 'register', 'get_status', 'list_all'."
                },
                "trademark_name": {"type": "string", "description": "The name of the trademark to check, register, or query."},
                "owner_name": {"type": "string", "description": "Name of the trademark owner (for registration)."},
                "owner_address": {"type": "string", "description": "Address of the trademark owner (for registration)."}
            },
            "required": ["command"]
        }

    def execute(self, command: str, **kwargs: Any) -> Dict:
        try:
            command = command.lower()
            actions = {
                "check_availability": self._check_availability,
                "register": self._register_trademark,
                "get_status": self._get_registration_status,
                "list_all": self._list_all_trademarks,
            }
            if command not in actions:
                raise ValueError(f"Invalid command. Supported: {list(actions.keys())}")

            # Trademark name is required for most actions
            trademark_name = kwargs.get("trademark_name")
            if command != 'list_all' and not trademark_name:
                raise ValueError("'trademark_name' is required for this command.")

            return actions[command](trademark_name=trademark_name, **kwargs)

        except Exception as e:
            logger.error(f"An error occurred in TrademarkRegistrationTool: {e}")
            return {"error": str(e)}

    def _check_availability(self, trademark_name: str, **kwargs) -> Dict:
        logger.info(f"Checking availability for trademark: {trademark_name}")
        if trademark_name.lower() in trademarks:
            return {"trademark_name": trademark_name, "is_available": False, "message": "Trademark is already registered or pending."}
        else:
            # Simulate checking a larger, external database
            if random.random() < 0.1: # 10% chance of finding a conflict  # nosec B311
                return {"trademark_name": trademark_name, "is_available": False, "message": "Conflict found in simulated external database."}
            return {"trademark_name": trademark_name, "is_available": True, "message": "Trademark appears to be available."}

    def _register_trademark(self, trademark_name: str, owner_name: str, owner_address: str, **kwargs) -> Dict:
        if not owner_name or not owner_address:
            raise ValueError("'owner_name' and 'owner_address' are required for registration.")
        
        logger.info(f"Attempting to register trademark: {trademark_name}")
        if trademark_name.lower() in trademarks:
            raise ValueError(f"Trademark '{trademark_name}' is already registered or pending.")
        
        registration_id = f"TM{random.randint(10000, 99999)}"  # nosec B311
        trademarks[trademark_name.lower()] = {
            "registration_id": registration_id,
            "trademark_name": trademark_name,
            "owner": {"name": owner_name, "address": owner_address},
            "status": "pending_review",
            "application_date": datetime.now(timezone.utc).isoformat(),
            "estimated_completion_date": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
        }
        return {
            "message": "Trademark registration application submitted successfully.",
            "details": trademarks[trademark_name.lower()]
        }

    def _get_registration_status(self, trademark_name: str, **kwargs) -> Dict:
        logger.info(f"Getting registration status for trademark: {trademark_name}")
        record = trademarks.get(trademark_name.lower())
        if not record:
            return {"error": f"Trademark '{trademark_name}' not found in records."}
        
        # Simulate status progression
        if record["status"] == "pending_review" and random.random() < 0.2:  # nosec B311
            record["status"] = "approved"
            record["registration_date"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"Simulated status change: Trademark '{trademark_name}' is now approved.")

        return {"status": record["status"], "details": record}

    def _list_all_trademarks(self, **kwargs) -> Dict:
        if not trademarks:
            return {"message": "No trademarks are currently registered in the simulation."}
        
        # Return a summary to avoid overly large output
        summary_list = [
            {
                "trademark_name": details["trademark_name"],
                "status": details["status"],
                "owner": details["owner"]["name"]
            }
            for tm, details in trademarks.items()
        ]
        return {"registered_trademarks": summary_list}