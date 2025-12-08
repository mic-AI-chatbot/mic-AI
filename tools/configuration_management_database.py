import logging
import json
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CI_FILE_PATH = 'cis_data.json'

class CMDBManager:
    """Manages Configuration Items (CIs) in a CMDB, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: str = CI_FILE_PATH):
        if cls._instance is None:
            cls._instance = super(CMDBManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.cis: Dict[str, Any] = cls._instance._load_cis()
        return cls._instance

    def _load_cis(self) -> Dict[str, Any]:
        """Loads CIs from the JSON file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty CIs.")
                return {}
            except Exception as e:
                logger.error(f"Error loading CIs from {self.file_path}: {e}")
                return {}
        return {}

    def _save_cis(self) -> None:
        """Saves CIs to the JSON file."""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cis, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving CIs to {self.file_path}: {e}")

    def create_ci(self, ci_id: str, name: str, ci_type: str, attributes: Dict[str, Any]) -> bool:
        if ci_id in self.cis:
            return False
        self.cis[ci_id] = {
            "name": name,
            "type": ci_type,
            "attributes": attributes,
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z"
        }
        self._save_cis()
        return True

    def get_ci(self, ci_id: str) -> Optional[Dict[str, Any]]:
        return self.cis.get(ci_id)

    def update_ci(self, ci_id: str, name: Optional[str] = None, ci_type: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None) -> bool:
        if ci_id not in self.cis:
            return False
        
        if name is not None: self.cis[ci_id]["name"] = name
        if ci_type is not None: self.cis[ci_id]["type"] = ci_type
        if attributes is not None: self.cis[ci_id]["attributes"].update(attributes)
        
        self.cis[ci_id]["updated_at"] = datetime.now().isoformat() + "Z"
        self._save_cis()
        return True

    def delete_ci(self, ci_id: str) -> bool:
        if ci_id in self.cis:
            del self.cis[ci_id]
            self._save_cis()
            return True
        return False

    def list_cis(self, ci_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not ci_type:
            return [{"ci_id": ci_id, "name": details['name'], "type": details['type'], "updated_at": details['updated_at']} for ci_id, details in self.cis.items()]
        
        filtered_list = []
        for ci_id, details in self.cis.items():
            if details['type'] == ci_type:
                filtered_list.append({"ci_id": ci_id, "name": details['name'], "type": details['type'], "updated_at": details['updated_at']})
        return filtered_list

cmdb_manager = CMDBManager()

class CreateCITool(BaseTool):
    """Creates a new Configuration Item (CI) in the CMDB."""
    def __init__(self, tool_name="create_ci"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new Configuration Item (CI) in the CMDB with a unique ID, name, type, and attributes."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ci_id": {"type": "string", "description": "A unique ID for the Configuration Item."},
                "name": {"type": "string", "description": "The name of the Configuration Item."},
                "ci_type": {"type": "string", "description": "The type of CI (e.g., 'server', 'application', 'database')."},
                "attributes": {"type": "object", "description": "A dictionary of attributes for the CI (e.g., {'ip_address': '192.168.1.1', 'owner': 'IT_Dept'}).", "default": {}}
            },
            "required": ["ci_id", "name", "ci_type"]
        }

    def execute(self, ci_id: str, name: str, ci_type: str, attributes: Dict[str, Any] = None, **kwargs: Any) -> str:
        if attributes is None: attributes = {}
        success = cmdb_manager.create_ci(ci_id, name, ci_type, attributes)
        if success:
            report = {"message": f"Configuration Item '{ci_id}' ('{name}') created successfully."}
        else:
            report = {"error": f"Configuration Item with ID '{ci_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class GetCITool(BaseTool):
    """Retrieves a Configuration Item (CI) by its ID."""
    def __init__(self, tool_name="get_ci"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves a Configuration Item (CI) from the CMDB using its unique ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"ci_id": {"type": "string", "description": "The unique ID of the Configuration Item to retrieve."}},
            "required": ["ci_id"]
        }

    def execute(self, ci_id: str, **kwargs: Any) -> str:
        ci = cmdb_manager.get_ci(ci_id)
        if ci:
            return json.dumps(ci, indent=2)
        else:
            return json.dumps({"error": f"Configuration Item with ID '{ci_id}' not found."})

class UpdateCITool(BaseTool):
    """Updates an existing Configuration Item (CI) in the CMDB."""
    def __init__(self, tool_name="update_ci"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Updates an existing Configuration Item (CI) in the CMDB. Can update its name, type, or attributes."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ci_id": {"type": "string", "description": "The unique ID of the Configuration Item to update."},
                "name": {"type": "string", "description": "Optional: The new name of the Configuration Item.", "default": None},
                "ci_type": {"type": "string", "description": "Optional: The new type of CI.", "default": None},
                "attributes": {"type": "object", "description": "Optional: A dictionary of attributes to update for the CI. Existing attributes will be overwritten, new ones added.", "default": None}
            },
            "required": ["ci_id"]
        }

    def execute(self, ci_id: str, name: Optional[str] = None, ci_type: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None, **kwargs: Any) -> str:
        success = cmdb_manager.update_ci(ci_id, name, ci_type, attributes)
        if success:
            report = {"message": f"Configuration Item '{ci_id}' updated successfully."}
        else:
            report = {"error": f"Configuration Item with ID '{ci_id}' not found or no changes made."}
        return json.dumps(report, indent=2)

class DeleteCITool(BaseTool):
    """Deletes a Configuration Item (CI) from the CMDB."""
    def __init__(self, tool_name="delete_ci"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deletes a Configuration Item (CI) from the CMDB using its unique ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"ci_id": {"type": "string", "description": "The unique ID of the Configuration Item to delete."}},
            "required": ["ci_id"]
        }

    def execute(self, ci_id: str, **kwargs: Any) -> str:
        success = cmdb_manager.delete_ci(ci_id)
        if success:
            report = {"message": f"Configuration Item '{ci_id}' deleted successfully."}
        else:
            report = {"error": f"Configuration Item with ID '{ci_id}' not found."}
        return json.dumps(report, indent=2)

class ListCITool(BaseTool):
    """Lists all Configuration Items (CIs), optionally filtered by type."""
    def __init__(self, tool_name="list_cis"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all Configuration Items (CIs), optionally filtered by type, showing their ID, name, and type."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ci_type": {"type": "string", "description": "Optional: Filter CIs by type (e.g., 'server', 'application').", "default": None}
            },
            "required": []
        }

    def execute(self, ci_type: Optional[str] = None, **kwargs: Any) -> str:
        cis = cmdb_manager.list_cis(ci_type)
        if not cis:
            return json.dumps({"message": "No Configuration Items found matching the criteria."})
        
        return json.dumps({"total_cis": len(cis), "configuration_items": cis}, indent=2)
