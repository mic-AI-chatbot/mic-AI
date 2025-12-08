import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PatchManagementSimulatorTool(BaseTool):
    """
    A tool that simulates a patch management system, allowing for scanning
    vulnerabilities, deploying patches, and generating compliance reports.
    """

    def __init__(self, tool_name: str = "PatchManagementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.systems_file = os.path.join(self.data_dir, "patch_status.json")
        # Systems structure: {system_id: {status: ..., last_scanned: ..., missing_patches: ..., critical_vulnerabilities: ...}}
        self.systems: Dict[str, Dict[str, Any]] = self._load_data(self.systems_file, default={})

    @property
    def description(self) -> str:
        return "Simulates patch management: scan vulnerabilities, deploy patches, get status, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["register_system", "scan_vulnerabilities", "deploy_patches", "get_patch_status", "generate_report"]},
                "system_id": {"type": "string"},
                "patch_ids": {"type": "array", "items": {"type": "string"}, "description": "List of patch IDs to deploy."},
                "report_type": {"type": "string", "enum": ["summary", "detailed"], "default": "summary"}
            },
            "required": ["operation", "system_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.systems_file, 'w') as f: json.dump(self.systems, f, indent=2)

    def register_system(self, system_id: str) -> Dict[str, Any]:
        """Registers a new system for patch management."""
        if system_id in self.systems: raise ValueError(f"System '{system_id}' already registered.")
        
        self.systems[system_id] = {
            "status": "unknown",
            "last_scanned": None,
            "missing_patches": 0,
            "critical_vulnerabilities": 0
        }
        self._save_data()
        return {"status": "success", "message": f"System '{system_id}' registered."}

    def scan_vulnerabilities(self, system_id: str) -> Dict[str, Any]:
        """Simulates scanning a system for missing patches and vulnerabilities."""
        if system_id not in self.systems: raise ValueError(f"System '{system_id}' not registered.")
        
        self.systems[system_id]["missing_patches"] = random.randint(0, 5)  # nosec B311
        self.systems[system_id]["critical_vulnerabilities"] = random.randint(0, 2)  # nosec B311
        self.systems[system_id]["last_scanned"] = datetime.now().isoformat()
        self.systems[system_id]["status"] = "scanned"
        self._save_data()
        return {"status": "success", "message": f"System '{system_id}' scanned for vulnerabilities."}

    def deploy_patches(self, system_id: str, patch_ids: List[str]) -> Dict[str, Any]:
        """Simulates deploying patches to a system."""
        if system_id not in self.systems: raise ValueError(f"System '{system_id}' not registered.")
        
        # Simulate successful deployment reducing missing patches and vulnerabilities
        self.systems[system_id]["missing_patches"] = max(0, self.systems[system_id]["missing_patches"] - len(patch_ids))
        self.systems[system_id]["critical_vulnerabilities"] = max(0, self.systems[system_id]["critical_vulnerabilities"] - random.randint(0, min(len(patch_ids), 2)))  # nosec B311
        self.systems[system_id]["status"] = "patched"
        self._save_data()
        return {"status": "success", "message": f"Patches deployed to system '{system_id}'."}

    def get_patch_status(self, system_id: str) -> Dict[str, Any]:
        """Retrieves the patch status of a system."""
        if system_id not in self.systems: raise ValueError(f"System '{system_id}' not registered.")
        
        status = self.systems[system_id]
        compliance = "Compliant" if status["missing_patches"] == 0 and status["critical_vulnerabilities"] == 0 else "Non-Compliant"
        
        return {
            "system_id": system_id,
            "status": status["status"],
            "compliance": compliance,
            "missing_patches": status["missing_patches"],
            "critical_vulnerabilities": status["critical_vulnerabilities"],
            "last_scanned": status["last_scanned"]
        }

    def generate_report(self, system_id: str, report_type: str = "summary") -> Dict[str, Any]:
        """Generates a patch compliance report for a system."""
        status_data = self.get_patch_status(system_id)
        
        if report_type == "summary":
            return {
                "report_type": "summary",
                "system_id": system_id,
                "compliance": status_data["compliance"],
                "message": f"System '{system_id}' is {status_data['compliance']}."
            }
        elif report_type == "detailed":
            return {
                "report_type": "detailed",
                "system_id": system_id,
                "compliance": status_data["compliance"],
                "details": status_data
            }
        else:
            raise ValueError(f"Unsupported report type: {report_type}.")

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "register_system": self.register_system,
            "scan_vulnerabilities": self.scan_vulnerabilities,
            "deploy_patches": self.deploy_patches,
            "get_patch_status": self.get_patch_status,
            "generate_report": self.generate_report
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating PatchManagementSimulatorTool functionality...")
    temp_dir = "temp_patch_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    patch_tool = PatchManagementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Register a system
        print("\n--- Registering system 'server_prod_01' ---")
        patch_tool.execute(operation="register_system", system_id="server_prod_01")
        print("System registered.")

        # 2. Scan for vulnerabilities
        print("\n--- Scanning 'server_prod_01' for vulnerabilities ---")
        patch_tool.execute(operation="scan_vulnerabilities", system_id="server_prod_01")
        print("Scan completed.")

        # 3. Get patch status
        print("\n--- Getting patch status for 'server_prod_01' ---")
        status1 = patch_tool.execute(operation="get_patch_status", system_id="server_prod_01")
        print(json.dumps(status1, indent=2))

        # 4. Deploy patches
        print("\n--- Deploying patches to 'server_prod_01' ---")
        patch_tool.execute(operation="deploy_patches", system_id="server_prod_01", patch_ids=["KB12345", "KB67890"])
        print("Patches deployed.")

        # 5. Get patch status again
        print("\n--- Getting patch status for 'server_prod_01' after patching ---")
        status2 = patch_tool.execute(operation="get_patch_status", system_id="server_prod_01")
        print(json.dumps(status2, indent=2))

        # 6. Generate a detailed report
        print("\n--- Generating detailed report for 'server_prod_01' ---")
        report = patch_tool.execute(operation="generate_report", system_id="server_prod_01", report_type="detailed")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")