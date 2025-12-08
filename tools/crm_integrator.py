import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

# Import CRMDBManager from crm_data_cleaner.py
try:
    from .crm_data_cleaner import CRMDBManager
    CRM_DB_MANAGER_AVAILABLE = True
except ImportError:
    CRM_DB_MANAGER_AVAILABLE = False
    logging.warning("CRMDBManager from crm_data_cleaner.py not found. CRM integration will use a separate, simpler data store.")

logger = logging.getLogger(__name__)

INTEGRATIONS_FILE = Path("crm_integrations.json")

class CRMIntegrationManager:
    """Manages CRM integration details, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = INTEGRATIONS_FILE):
        if cls._instance is None:
            cls._instance = super(CRMIntegrationManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.integrations: Dict[str, Any] = cls._instance._load_integrations()
        return cls._instance

    def _load_integrations(self) -> Dict[str, Any]:
        """Loads integration details from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty integrations.")
                return {}
            except Exception as e:
                logger.error(f"Error loading integrations from {self.file_path}: {e}")
                return {}
        return {}

    def _save_integrations(self) -> None:
        """Saves integration details to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.integrations, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving integrations to {self.file_path}: {e}")

    def configure_integration(self, crm_system: str, api_key: str, base_url: str) -> bool:
        if crm_system in self.integrations:
            return False
        self.integrations[crm_system] = {
            "api_key": api_key,
            "base_url": base_url,
            "status": "configured",
            "configured_at": datetime.now().isoformat() + "Z"
        }
        self._save_integrations()
        return True

    def get_integration(self, crm_system: str) -> Optional[Dict[str, Any]]:
        return self.integrations.get(crm_system)

    def list_integrations(self) -> List[Dict[str, Any]]:
        return [{"crm_system": name, "status": details['status'], "configured_at": details['configured_at']} for name, details in self.integrations.items()]

crm_integration_manager = CRMIntegrationManager()

# Use CRMDBManager from crm_data_cleaner.py if available, otherwise create a simple mock
if CRM_DB_MANAGER_AVAILABLE:
    from .crm_data_cleaner import crm_db_manager as crm_data_manager
else:
    class MockCRMDBManager:
        def list_records(self, status: str = None) -> List[Dict[str, Any]]:
            # Return some mock records for simulation
            return [
                {"id": "mock_rec1", "name": "Mock Contact 1", "email": "mock1@example.com", "status": "active"},
                {"id": "mock_rec2", "name": "Mock Contact 2", "email": "mock2@example.com", "status": "active"}
            ]
        def update_record(self, record_id: str, updates: Dict[str, Any]) -> bool:
            # Simulate update
            return True
    crm_data_manager = MockCRMDBManager()
    logging.warning("Using mock CRMDBManager as crm_data_cleaner.py is not available. Data synchronization will be simulated with mock data.")

class ConfigureCRMIntegrationTool(BaseTool):
    """Configures integration details for a CRM system."""
    def __init__(self, tool_name="configure_crm_integration"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Configures integration details (API key, base URL) for a CRM system (e.g., 'Salesforce', 'HubSpot')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "crm_system": {"type": "string", "description": "The CRM system to integrate with.", "enum": ["Salesforce", "HubSpot"]},
                "api_key": {"type": "string", "description": "The API key for the CRM system."},
                "base_url": {"type": "string", "description": "The base URL for the CRM API."}
            },
            "required": ["crm_system", "api_key", "base_url"]
        }

    def execute(self, crm_system: str, api_key: str, base_url: str, **kwargs: Any) -> str:
        success = crm_integration_manager.configure_integration(crm_system, api_key, base_url)
        if success:
            report = {"message": f"CRM integration for '{crm_system}' configured successfully."}
        else:
            report = {"error": f"CRM integration for '{crm_system}' already exists. Use update if you want to modify it."}
        return json.dumps(report, indent=2)

class SyncCRMContactsTool(BaseTool):
    """Simulates synchronizing contacts with a CRM system."""
    def __init__(self, tool_name="sync_crm_contacts"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates synchronizing contacts from the local database to a configured CRM system."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "crm_system": {"type": "string", "description": "The CRM system to synchronize with.", "enum": ["Salesforce", "HubSpot"]},
                "num_contacts_to_sync": {"type": "integer", "description": "Number of contacts to simulate synchronizing.", "default": 10}
            },
            "required": ["crm_system"]
        }

    def execute(self, crm_system: str, num_contacts_to_sync: int = 10, **kwargs: Any) -> str:
        integration = crm_integration_manager.get_integration(crm_system)
        if not integration:
            return json.dumps({"error": f"CRM integration for '{crm_system}' not found. Please configure it first."})
        
        local_contacts = crm_data_manager.list_records(status="active")
        if not local_contacts:
            return json.dumps({"message": "No active local CRM records to synchronize."})

        synced_count = min(num_contacts_to_sync, len(local_contacts))
        
        # Simulate sync process
        status = random.choice(["success", "partial_success", "failure"])  # nosec B311
        
        report = {
            "crm_system": crm_system,
            "sync_type": "contacts",
            "status": status,
            "synced_count": synced_count,
            "message": f"Simulated synchronization of {synced_count} contacts with {crm_system}. Status: {status}."
        }
        return json.dumps(report, indent=2)

class SyncCRMOpportunitiesTool(BaseTool):
    """Simulates synchronizing opportunities with a CRM system."""
    def __init__(self, tool_name="sync_crm_opportunities"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates synchronizing opportunities from the local database to a configured CRM system."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "crm_system": {"type": "string", "description": "The CRM system to synchronize with.", "enum": ["Salesforce", "HubSpot"]},
                "num_opportunities_to_sync": {"type": "integer", "description": "Number of opportunities to simulate synchronizing.", "default": 5}
            },
            "required": ["crm_system"]
        }

    def execute(self, crm_system: str, num_opportunities_to_sync: int = 5, **kwargs: Any) -> str:
        integration = crm_integration_manager.get_integration(crm_system)
        if not integration:
            return json.dumps({"error": f"CRM integration for '{crm_system}' not found. Please configure it first."})
        
        # Simulate local opportunities
        local_opportunities = [{"id": f"opp_{i}", "name": f"Deal {i}", "amount": random.uniform(1000, 10000)} for i in range(num_opportunities_to_sync)]  # nosec B311
        
        # Simulate sync process
        status = random.choice(["success", "failure"])  # nosec B311
        
        report = {
            "crm_system": crm_system,
            "sync_type": "opportunities",
            "status": status,
            "synced_count": len(local_opportunities),
            "message": f"Simulated synchronization of {len(local_opportunities)} opportunities with {crm_system}. Status: {status}."
        }
        return json.dumps(report, indent=2)

class ListCRMIntegrationsTool(BaseTool):
    """Lists all configured CRM integrations."""
    def __init__(self, tool_name="list_crm_integrations"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all configured CRM integrations, showing the CRM system and its status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        integrations = crm_integration_manager.list_integrations()
        if not integrations:
            return json.dumps({"message": "No CRM integrations found."})
        
        return json.dumps({"total_integrations": len(integrations), "integrations": integrations}, indent=2)