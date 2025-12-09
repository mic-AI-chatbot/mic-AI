import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SoftwareAssetManagementSimulatorTool(BaseTool):
    """
    A tool that simulates Software Asset Management (SAM), allowing for
    tracking licenses, monitoring usage, and generating compliance reports.
    """

    def __init__(self, tool_name: str = "SoftwareAssetManagementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.assets_file = os.path.join(self.data_dir, "software_assets.json")
        self.usage_file = os.path.join(self.data_dir, "software_usage_records.json")
        
        # Software assets: {asset_id: {name: ..., version: ..., license_type: ..., total_licenses: ..., current_usage_count: ...}}
        self.software_assets: Dict[str, Dict[str, Any]] = self._load_data(self.assets_file, default={})
        # Usage records: {asset_id: [{timestamp: ..., user_id: ...}]}
        self.usage_records: Dict[str, List[Dict[str, Any]]] = self._load_data(self.usage_file, default={})

    @property
    def description(self) -> str:
        return "Simulates SAM: track licenses, monitor usage, and generate compliance reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_software_asset", "monitor_usage", "generate_compliance_report", "get_asset_details"]},
                "asset_id": {"type": "string"},
                "name": {"type": "string"},
                "version": {"type": "string"},
                "license_type": {"type": "string", "enum": ["per_user", "per_device", "site_license"]},
                "total_licenses": {"type": "integer", "minimum": 1},
                "user_id": {"type": "string", "description": "ID of the user using the software."}
            },
            "required": ["operation", "asset_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_assets(self):
        with open(self.assets_file, 'w') as f: json.dump(self.software_assets, f, indent=2)

    def _save_usage(self):
        with open(self.usage_file, 'w') as f: json.dump(self.usage_records, f, indent=2)

    def add_software_asset(self, asset_id: str, name: str, version: str, license_type: str, total_licenses: int) -> Dict[str, Any]:
        """Adds a new software asset record."""
        if asset_id in self.software_assets: raise ValueError(f"Software asset '{asset_id}' already exists.")
        
        new_asset = {
            "id": asset_id, "name": name, "version": version, "license_type": license_type,
            "total_licenses": total_licenses, "current_usage_count": 0,
            "added_at": datetime.now().isoformat()
        }
        self.software_assets[asset_id] = new_asset
        self._save_assets()
        return new_asset

    def monitor_usage(self, asset_id: str, user_id: str) -> Dict[str, Any]:
        """Simulates monitoring software usage by a user."""
        asset = self.software_assets.get(asset_id)
        if not asset: raise ValueError(f"Software asset '{asset_id}' not found. Add it first.")
        
        # Increment usage count
        asset["current_usage_count"] += 1
        self._save_assets()

        log_entry = {
            "timestamp": datetime.now().isoformat(), "user_id": user_id, "event": "usage"
        }
        self.usage_records.setdefault(asset_id, []).append(log_entry)
        self._save_usage()
        return {"status": "success", "message": f"Usage for '{asset_id}' by '{user_id}' recorded."}

    def generate_compliance_report(self, asset_id: str) -> Dict[str, Any]:
        """Generates a compliance report for a software asset."""
        asset = self.software_assets.get(asset_id)
        if not asset: raise ValueError(f"Software asset '{asset_id}' not found.")
        
        compliance_status = "compliant"
        violations = []
        
        if asset["current_usage_count"] > asset["total_licenses"]:
            compliance_status = "non-compliant"
            violations.append(f"Usage ({asset['current_usage_count']}) exceeds total licenses ({asset['total_licenses']}).")
        
        report_id = f"sam_report_{asset_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "asset_id": asset_id, "name": asset["name"],
            "version": asset["version"], "license_type": asset["license_type"],
            "total_licenses": asset["total_licenses"], "current_usage_count": asset["current_usage_count"],
            "compliance_status": compliance_status, "violations": violations,
            "generated_at": datetime.now().isoformat()
        }
        return report

    def get_asset_details(self, asset_id: str) -> Dict[str, Any]:
        """Retrieves the details of a software asset."""
        asset = self.software_assets.get(asset_id)
        if not asset: raise ValueError(f"Software asset '{asset_id}' not found.")
        return asset

    def execute(self, operation: str, asset_id: str, **kwargs: Any) -> Any:
        if operation == "add_software_asset":
            name = kwargs.get('name')
            version = kwargs.get('version')
            license_type = kwargs.get('license_type')
            total_licenses = kwargs.get('total_licenses')
            if not all([name, version, license_type, total_licenses is not None]):
                raise ValueError("Missing 'name', 'version', 'license_type', or 'total_licenses' for 'add_software_asset' operation.")
            return self.add_software_asset(asset_id, name, version, license_type, total_licenses)
        elif operation == "monitor_usage":
            user_id = kwargs.get('user_id')
            if not user_id:
                raise ValueError("Missing 'user_id' for 'monitor_usage' operation.")
            return self.monitor_usage(asset_id, user_id)
        elif operation == "generate_compliance_report":
            # No additional kwargs required for generate_compliance_report
            return self.generate_compliance_report(asset_id)
        elif operation == "get_asset_details":
            # No additional kwargs required for get_asset_details
            return self.get_asset_details(asset_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SoftwareAssetManagementSimulatorTool functionality...")
    temp_dir = "temp_sam_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sam_tool = SoftwareAssetManagementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add a software asset
        print("\n--- Adding software asset 'Microsoft_Office' ---")
        sam_tool.execute(operation="add_software_asset", asset_id="MS_OFFICE_2023", name="Microsoft Office", version="2023", license_type="per_user", total_licenses=5)
        print("Asset added.")

        # 2. Monitor usage (within limits)
        print("\n--- Monitoring usage for 'MS_OFFICE_2023' (3 users) ---")
        sam_tool.execute(operation="monitor_usage", asset_id="MS_OFFICE_2023", user_id="user_alice")
        sam_tool.execute(operation="monitor_usage", asset_id="MS_OFFICE_2023", user_id="user_bob")
        sam_tool.execute(operation="monitor_usage", asset_id="MS_OFFICE_2023", user_id="user_charlie")
        print("Usage monitored.")

        # 3. Generate compliance report
        print("\n--- Generating compliance report for 'MS_OFFICE_2023' ---")
        report1 = sam_tool.execute(operation="generate_compliance_report", asset_id="MS_OFFICE_2023")
        print(json.dumps(report1, indent=2))

        # 4. Monitor usage (exceeding limits)
        print("\n--- Monitoring usage for 'MS_OFFICE_2023' (6 users, exceeding limit) ---")
        sam_tool.execute(operation="monitor_usage", asset_id="MS_OFFICE_2023", user_id="user_david")
        sam_tool.execute(operation="monitor_usage", asset_id="MS_OFFICE_2023", user_id="user_eve")
        sam_tool.execute(operation="monitor_usage", asset_id="MS_OFFICE_2023", user_id="user_frank")
        print("Usage monitored.")

        # 5. Generate compliance report again
        print("\n--- Generating compliance report for 'MS_OFFICE_2023' (after exceeding) ---")
        report2 = sam_tool.execute(operation="generate_compliance_report", asset_id="MS_OFFICE_2023")
        print(json.dumps(report2, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")