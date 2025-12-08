import logging
import json
import os
from datetime import datetime, timedelta
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CONTRACTS_FILE = Path("contracts.json")

class ContractManager:
    """Manages contract lifecycle, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CONTRACTS_FILE):
        if cls._instance is None:
            cls._instance = super(ContractManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.contracts: Dict[str, Any] = cls._instance._load_contracts()
        return cls._instance

    def _load_contracts(self) -> Dict[str, Any]:
        """Loads contracts from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty contracts.")
                return {}
            except Exception as e:
                logger.error(f"Error loading contracts from {self.file_path}: {e}")
                return {}
        return {}

    def _save_contracts(self) -> None:
        """Saves contracts to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.contracts, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving contracts to {self.file_path}: {e}")

    def create_contract(self, contract_id: str, title: str, parties: List[str], start_date: str, end_date: str, value: float, milestones: List[Dict[str, Any]]) -> bool:
        if contract_id in self.contracts:
            return False
        self.contracts[contract_id] = {
            "title": title,
            "parties": parties,
            "start_date": start_date,
            "end_date": end_date,
            "value": value,
            "status": "active", # Default status
            "milestones": milestones,
            "created_at": datetime.now().isoformat() + "Z",
            "last_updated_at": datetime.now().isoformat() + "Z"
        }
        self._save_contracts()
        return True

    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        return self.contracts.get(contract_id)

    def update_contract_status(self, contract_id: str, new_status: str) -> bool:
        if contract_id not in self.contracts:
            return False
        self.contracts[contract_id]["status"] = new_status
        self.contracts[contract_id]["last_updated_at"] = datetime.now().isoformat() + "Z"
        self._save_contracts()
        return True

    def delete_contract(self, contract_id: str) -> bool:
        if contract_id in self.contracts:
            del self.contracts[contract_id]
            self._save_contracts()
            return True
        return False

    def list_contracts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if not status:
            return [{"contract_id": c_id, "title": details['title'], "status": details['status'], "end_date": details['end_date']} for c_id, details in self.contracts.items()]
        
        filtered_list = []
        for c_id, details in self.contracts.items():
            if details['status'] == status:
                filtered_list.append({"contract_id": c_id, "title": details['title'], "status": details['status'], "end_date": details['end_date']})
        return filtered_list

    def update_milestone_status(self, contract_id: str, milestone_name: str, new_status: str) -> bool:
        if contract_id not in self.contracts:
            return False
        
        for milestone in self.contracts[contract_id]["milestones"]:
            if milestone["name"] == milestone_name:
                milestone["status"] = new_status
                milestone["updated_at"] = datetime.now().isoformat() + "Z"
                self._save_contracts()
                return True
        return False

contract_manager = ContractManager()

class CreateContractTool(BaseTool):
    """Creates a new contract in the contract lifecycle manager."""
    def __init__(self, tool_name="create_contract"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new contract with specified details, including parties, dates, value, and milestones."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "A unique ID for the contract."},
                "title": {"type": "string", "description": "The title or summary of the contract."},
                "parties": {"type": "array", "items": {"type": "string"}, "description": "A list of parties involved in the contract."},
                "start_date": {"type": "string", "description": "The contract start date (YYYY-MM-DD)."},
                "end_date": {"type": "string", "description": "The contract end date (YYYY-MM-DD)."},
                "value": {"type": "number", "description": "The monetary value of the contract."},
                "milestones": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name of the milestone."},
                            "due_date": {"type": "string", "description": "Milestone due date (YYYY-MM-DD)."},
                            "status": {"type": "string", "description": "Status of the milestone.", "enum": ["pending", "completed", "overdue"], "default": "pending"}
                        },
                        "required": ["name", "due_date"]
                    },
                    "description": "Optional: A list of contract milestones.", "default": []
                }
            },
            "required": ["contract_id", "title", "parties", "start_date", "end_date", "value"]
        }

    def execute(self, contract_id: str, title: str, parties: List[str], start_date: str, end_date: str, value: float, milestones: List[Dict[str, Any]] = None, **kwargs: Any) -> str:
        if milestones is None: milestones = []
        success = contract_manager.create_contract(contract_id, title, parties, start_date, end_date, value, milestones)
        if success:
            report = {"message": f"Contract '{contract_id}' ('{title}') created successfully. Status: active."}
        else:
            report = {"error": f"Contract with ID '{contract_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class GetContractDetailsTool(BaseTool):
    """Retrieves details of a specific contract."""
    def __init__(self, tool_name="get_contract_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves details of a specific contract, including its parties, dates, value, status, and milestones."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"contract_id": {"type": "string", "description": "The ID of the contract to retrieve."}},
            "required": ["contract_id"]
        }

    def execute(self, contract_id: str, **kwargs: Any) -> str:
        contract = contract_manager.get_contract(contract_id)
        if contract:
            return json.dumps(contract, indent=2)
        else:
            return json.dumps({"error": f"Contract with ID '{contract_id}' not found."})

class UpdateContractStatusTool(BaseTool):
    """Updates the status of a contract."""
    def __init__(self, tool_name="update_contract_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Updates the status of an existing contract (e.g., 'active', 'expired', 'terminated', 'pending', 'draft')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "The ID of the contract to update."},
                "new_status": {"type": "string", "description": "The new status for the contract.", "enum": ["active", "expired", "terminated", "pending", "draft"]}
            },
            "required": ["contract_id", "new_status"]
        }

    def execute(self, contract_id: str, new_status: str, **kwargs: Any) -> str:
        success = contract_manager.update_contract_status(contract_id, new_status)
        if success:
            report = {"message": f"Contract '{contract_id}' status updated to '{new_status}' successfully."}
        else:
            report = {"error": f"Contract with ID '{contract_id}' not found."}
        return json.dumps(report, indent=2)

class DeleteContractTool(BaseTool):
    """Deletes a contract."""
    def __init__(self, tool_name="delete_contract"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deletes a contract from the contract lifecycle manager using its unique ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"contract_id": {"type": "string", "description": "The ID of the contract to delete."}},
            "required": ["contract_id"]
        }

    def execute(self, contract_id: str, **kwargs: Any) -> str:
        success = contract_manager.delete_contract(contract_id)
        if success:
            report = {"message": f"Contract '{contract_id}' deleted successfully."}
        else:
            report = {"error": f"Contract with ID '{contract_id}' not found."}
        return json.dumps(report, indent=2)

class ListContractsTool(BaseTool):
    """Lists all contracts, optionally filtered by status."""
    def __init__(self, tool_name="list_contracts"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all contracts, optionally filtered by status, showing their ID, title, status, and end date."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional: Filter contracts by status.", "enum": ["active", "expired", "terminated", "pending", "draft"], "default": None}
            },
            "required": []
        }

    def execute(self, status: Optional[str] = None, **kwargs: Any) -> str:
        contracts = contract_manager.list_contracts(status)
        if not contracts:
            return json.dumps({"message": "No contracts found matching the criteria."})
        
        return json.dumps({"total_contracts": len(contracts), "contracts": contracts}, indent=2)

class MonitorContractMilestonesTool(BaseTool):
    """Monitors contract milestones and updates their status."""
    def __init__(self, tool_name="monitor_contract_milestones"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Monitors contract milestones, checks their due dates against the current date, and updates their status (e.g., 'pending', 'completed', 'overdue')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "The ID of the contract to monitor milestones for."},
                "milestone_name": {"type": "string", "description": "The name of the milestone to update."},
                "new_status": {"type": "string", "description": "The new status for the milestone.", "enum": ["pending", "completed", "overdue"]}
            },
            "required": ["contract_id", "milestone_name", "new_status"]
        }

    def execute(self, contract_id: str, milestone_name: str, new_status: str, **kwargs: Any) -> str:
        contract = contract_manager.get_contract(contract_id)
        if not contract:
            return json.dumps({"error": f"Contract '{contract_id}' not found."})
        
        success = contract_manager.update_milestone_status(contract_id, milestone_name, new_status)
        if success:
            report = {"message": f"Milestone '{milestone_name}' for contract '{contract_id}' updated to '{new_status}'."}
        else:
            report = {"error": f"Milestone '{milestone_name}' not found in contract '{contract_id}'."}
        return json.dumps(report, indent=2)
