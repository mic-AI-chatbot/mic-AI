import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataSharingPlatformTool(BaseTool):
    """
    A tool for simulating a data sharing platform, allowing for the registration
    of data assets, definition of sharing agreements, and management of access.
    """

    def __init__(self, tool_name: str = "data_sharing_platform"):
        super().__init__(tool_name)
        self.assets_file = "shared_data_assets.json"
        self.agreements_file = "sharing_agreements.json"
        self.data_assets: Dict[str, Dict[str, Any]] = self._load_state(self.assets_file)
        self.sharing_agreements: Dict[str, Dict[str, Any]] = self._load_state(self.agreements_file)

    @property
    def description(self) -> str:
        return "Simulates a data sharing platform: registers assets, defines agreements, and manages access."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data sharing operation to perform.",
                    "enum": ["register_data_asset", "define_sharing_agreement", "share_data", "manage_access", "list_data_assets", "list_sharing_agreements"]
                },
                "asset_id": {"type": "string"},
                "asset_name": {"type": "string"},
                "description": {"type": "string"},
                "sensitivity_level": {"type": "string", "enum": ["public", "internal", "confidential", "restricted"]},
                "agreement_id": {"type": "string"},
                "recipient": {"type": "string"},
                "terms": {"type": "object"},
                "new_status": {"type": "string", "enum": ["active", "revoked", "expired"]}
            },
            "required": ["operation"]
        }

    def _load_state(self, file_path: str) -> Dict[str, Any]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted state file '{file_path}'. Starting fresh.")
                    return {}
        return {}

    def _save_state(self, state: Dict[str, Any], file_path: str) -> None:
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=4)

    def _register_data_asset(self, asset_id: str, asset_name: str, description: str, sensitivity_level: str) -> Dict[str, Any]:
        if not all([asset_id, asset_name, description, sensitivity_level]):
            raise ValueError("Asset ID, name, description, and sensitivity level cannot be empty.")
        if asset_id in self.data_assets:
            raise ValueError(f"Data asset '{asset_id}' already exists.")
        if sensitivity_level not in ["public", "internal", "confidential", "restricted"]:
            raise ValueError(f"Invalid sensitivity_level: '{sensitivity_level}'.")

        new_asset = {
            "asset_id": asset_id, "asset_name": asset_name, "description": description,
            "sensitivity_level": sensitivity_level, "registered_at": datetime.now().isoformat()
        }
        self.data_assets[asset_id] = new_asset
        self._save_state(self.data_assets, self.assets_file)
        return new_asset

    def _define_sharing_agreement(self, agreement_id: str, asset_id: str, recipient: str, terms: Dict[str, Any]) -> Dict[str, Any]:
        if not all([agreement_id, asset_id, recipient, terms]):
            raise ValueError("Agreement ID, asset ID, recipient, and terms cannot be empty.")
        if agreement_id in self.sharing_agreements:
            raise ValueError(f"Sharing agreement '{agreement_id}' already exists.")
        if asset_id not in self.data_assets:
            raise ValueError(f"Data asset '{asset_id}' not registered.")

        new_agreement = {
            "agreement_id": agreement_id, "asset_id": asset_id, "recipient": recipient,
            "terms": terms, "status": "pending", "defined_at": datetime.now().isoformat()
        }
        self.sharing_agreements[agreement_id] = new_agreement
        self._save_state(self.sharing_agreements, self.agreements_file)
        return new_agreement

    def _share_data(self, agreement_id: str) -> Dict[str, Any]:
        agreement = self.sharing_agreements.get(agreement_id)
        if not agreement: raise ValueError(f"Sharing agreement '{agreement_id}' not found.")
        if agreement["status"] != "active": raise ValueError(f"Sharing agreement '{agreement_id}' is not active.")

        asset = self.data_assets.get(agreement["asset_id"])
        if not asset: raise ValueError(f"Data asset '{agreement['asset_id']}' not found for agreement '{agreement_id}'.")

        sharing_result = {
            "agreement_id": agreement_id, "asset_id": agreement["asset_id"], "recipient": agreement["recipient"],
            "status": "data_shared", "message": f"Simulated data sharing for asset '{asset['asset_name']}' with '{agreement['recipient']}' under agreement '{agreement_id}'.",
            "shared_at": datetime.now().isoformat()
        }
        return sharing_result

    def _manage_access(self, agreement_id: str, new_status: str) -> Dict[str, Any]:
        agreement = self.sharing_agreements.get(agreement_id)
        if not agreement: raise ValueError(f"Sharing agreement '{agreement_id}' not found.")
        if new_status not in ["active", "revoked", "expired"]: raise ValueError(f"Invalid new_status: '{new_status}'.")

        agreement["status"] = new_status
        agreement["last_updated_at"] = datetime.now().isoformat()
        self._save_state(self.sharing_agreements, self.agreements_file)
        return agreement

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "register_data_asset":
            return self._register_data_asset(kwargs.get("asset_id"), kwargs.get("asset_name"), kwargs.get("description"), kwargs.get("sensitivity_level"))
        elif operation == "define_sharing_agreement":
            return self._define_sharing_agreement(kwargs.get("agreement_id"), kwargs.get("asset_id"), kwargs.get("recipient"), kwargs.get("terms"))
        elif operation == "share_data":
            return self._share_data(kwargs.get("agreement_id"))
        elif operation == "manage_access":
            return self._manage_access(kwargs.get("agreement_id"), kwargs.get("new_status"))
        elif operation == "list_data_assets":
            return list(self.data_assets.values())
        elif operation == "list_sharing_agreements":
            recipient = kwargs.get("recipient")
            if recipient: return [a for a in self.sharing_agreements.values() if a.get("recipient") == recipient]
            return list(self.sharing_agreements.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataSharingPlatformTool functionality...")
    tool = DataSharingPlatformTool()
    
    try:
        print("\n--- Registering Data Asset ---")
        tool.execute(operation="register_data_asset", asset_id="customer_data", asset_name="Customer PII", description="Sensitive customer info.", sensitivity_level="restricted")
        
        print("\n--- Defining Sharing Agreement ---")
        tool.execute(operation="define_sharing_agreement", agreement_id="agree_001", asset_id="customer_data", recipient="Analytics_Team", terms={"purpose": "analysis"})

        print("\n--- Managing Access (Activate) ---")
        tool.execute(operation="manage_access", agreement_id="agree_001", new_status="active")

        print("\n--- Sharing Data ---")
        share_result = tool.execute(operation="share_data", agreement_id="agree_001")
        print(json.dumps(share_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.assets_file): os.remove(tool.assets_file)
        if os.path.exists(tool.agreements_file): os.remove(tool.agreements_file)
        print("\nCleanup complete.")