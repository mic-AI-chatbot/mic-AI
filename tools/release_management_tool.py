import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ReleaseManagementSimulatorTool(BaseTool):
    """
    A tool that simulates release management, allowing for creating, deploying,
    rolling back, and reporting on software releases.
    """

    def __init__(self, tool_name: str = "ReleaseManagementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.releases_file = os.path.join(self.data_dir, "software_releases.json")
        # Releases structure: {release_id: {version: ..., description: ..., status: ..., deployments: {}}}
        self.releases: Dict[str, Dict[str, Any]] = self._load_data(self.releases_file, default={})

    @property
    def description(self) -> str:
        return "Simulates release management: create, deploy, rollback, and report on software releases."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_release", "get_release_status", "deploy_release", "rollback_release", "generate_report"]},
                "release_id": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
                "environment": {"type": "string", "enum": ["dev", "staging", "production"]}
            },
            "required": ["operation", "release_id"]
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
        with open(self.releases_file, 'w') as f: json.dump(self.releases, f, indent=2)

    def create_release(self, release_id: str, version: str, description: str) -> Dict[str, Any]:
        """Creates a new software release record."""
        if release_id in self.releases: raise ValueError(f"Release '{release_id}' already exists.")
        
        new_release = {
            "id": release_id, "version": version, "description": description,
            "status": "created", "deployments": {},
            "created_at": datetime.now().isoformat()
        }
        self.releases[release_id] = new_release
        self._save_data()
        return new_release

    def get_release_status(self, release_id: str) -> Dict[str, Any]:
        """Retrieves the status of a specific release."""
        release = self.releases.get(release_id)
        if not release: raise ValueError(f"Release '{release_id}' not found.")
        return release

    def deploy_release(self, release_id: str, environment: str) -> Dict[str, Any]:
        """Simulates deploying a release to an environment."""
        release = self.releases.get(release_id)
        if not release: raise ValueError(f"Release '{release_id}' not found.")
        
        release["deployments"][environment] = {"status": "deployed", "timestamp": datetime.now().isoformat()}
        release["status"] = "deployed" # Overall status
        self._save_data()
        return {"status": "success", "message": f"Release '{release_id}' deployed to '{environment}'."}

    def rollback_release(self, release_id: str, environment: str) -> Dict[str, Any]:
        """Simulates rolling back a release from an environment."""
        release = self.releases.get(release_id)
        if not release: raise ValueError(f"Release '{release_id}' not found.")
        if environment not in release["deployments"]: raise ValueError(f"Release '{release_id}' not deployed to '{environment}'.")
        
        release["deployments"][environment]["status"] = "rolled_back"
        release["deployments"][environment]["rolled_back_at"] = datetime.now().isoformat()
        release["status"] = "rolled_back" # Overall status
        self._save_data()
        return {"status": "success", "message": f"Release '{release_id}' rolled back from '{environment}'."}

    def generate_report(self) -> List[Dict[str, Any]]:
        """Generates a report summarizing the status of all releases."""
        report = []
        for release_id, release_data in self.releases.items():
            report.append({
                "release_id": release_id,
                "version": release_data["version"],
                "status": release_data["status"],
                "deployments": release_data["deployments"]
            })
        return report

    def execute(self, operation: str, release_id: str, **kwargs: Any) -> Any:
        if operation == "create_release":
            version = kwargs.get('version')
            description = kwargs.get('description')
            if not all([version, description]):
                raise ValueError("Missing 'version' or 'description' for 'create_release' operation.")
            return self.create_release(release_id, version, description)
        elif operation == "get_release_status":
            # No additional kwargs required for get_release_status
            return self.get_release_status(release_id)
        elif operation == "deploy_release":
            environment = kwargs.get('environment')
            if not environment:
                raise ValueError("Missing 'environment' for 'deploy_release' operation.")
            return self.deploy_release(release_id, environment)
        elif operation == "rollback_release":
            environment = kwargs.get('environment')
            if not environment:
                raise ValueError("Missing 'environment' for 'rollback_release' operation.")
            return self.rollback_release(release_id, environment)
        elif operation == "generate_report":
            # No additional kwargs required for generate_report
            return self.generate_report()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ReleaseManagementSimulatorTool functionality...")
    temp_dir = "temp_release_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    release_tool = ReleaseManagementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a release
        print("\n--- Creating release 'REL-001' (v1.0) ---")
        release_tool.execute(operation="create_release", release_id="REL-001", version="1.0", description="Initial product launch.")
        print("Release created.")

        # 2. Deploy the release to staging
        print("\n--- Deploying 'REL-001' to 'staging' ---")
        release_tool.execute(operation="deploy_release", release_id="REL-001", environment="staging")
        print("Deployed to staging.")

        # 3. Get release status
        print("\n--- Getting status for 'REL-001' ---")
        status = release_tool.execute(operation="get_release_status", release_id="REL-001")
        print(json.dumps(status, indent=2))

        # 4. Deploy the release to production
        print("\n--- Deploying 'REL-001' to 'production' ---")
        release_tool.execute(operation="deploy_release", release_id="REL-001", environment="production")
        print("Deployed to production.")

        # 5. Generate report
        print("\n--- Generating release report ---")
        report = release_tool.execute(operation="generate_report")
        print(json.dumps(report, indent=2))

        # 6. Rollback from staging (simulated)
        print("\n--- Rolling back 'REL-001' from 'staging' ---")
        release_tool.execute(operation="rollback_release", release_id="REL-001", environment="staging")
        print("Rolled back from staging.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")