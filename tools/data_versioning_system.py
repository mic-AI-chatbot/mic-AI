import logging
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataVersioningTool(BaseTool):
    """
    A tool for simulating a data versioning system.
    """

    def __init__(self, tool_name: str = "data_versioning_system"):
        super().__init__(tool_name)
        self.metadata_file = "data_versions_metadata.json"
        self.content_dir = "data_versions_content"
        self.versions_metadata: Dict[str, List[Dict[str, Any]]] = self._load_versions_metadata()
        os.makedirs(self.content_dir, exist_ok=True)

    @property
    def description(self) -> str:
        return "Simulates a data versioning system: creates, retrieves, and lists versions of data sets."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The versioning operation to perform.",
                    "enum": ["create_version", "retrieve_version", "list_versions", "get_latest_version"]
                },
                "data_set_id": {"type": "string"},
                "data_content": {"type": "string"},
                "commit_message": {"type": "string"},
                "version_id": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_versions_metadata(self) -> Dict[str, List[Dict[str, Any]]]:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted metadata file '{self.metadata_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_versions_metadata(self) -> None:
        with open(self.metadata_file, 'w') as f:
            json.dump(self.versions_metadata, f, indent=4)

    def _get_data_set_content_dir(self, data_set_id: str) -> str:
        data_set_dir = os.path.join(self.content_dir, data_set_id)
        os.makedirs(data_set_dir, exist_ok=True)
        return data_set_dir

    def _create_version(self, data_set_id: str, data_content: str, commit_message: str) -> Dict[str, Any]:
        if not all([data_set_id, data_content, commit_message]):
            raise ValueError("Data set ID, content, and commit message cannot be empty.")

        version_id = f"V-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        version_file_name = f"{version_id}.txt"
        data_set_content_dir = self._get_data_set_content_dir(data_set_id)
        version_file_path = os.path.join(data_set_content_dir, version_file_name)

        with open(version_file_path, 'w') as f: f.write(data_content)

        new_version = {
            "version_id": version_id, "data_set_id": data_set_id, "commit_message": commit_message,
            "created_at": datetime.now().isoformat(), "content_path": os.path.abspath(version_file_path)
        }
        if data_set_id not in self.versions_metadata: self.versions_metadata[data_set_id] = []
        self.versions_metadata[data_set_id].append(new_version)
        self._save_versions_metadata()
        return new_version

    def _retrieve_version(self, data_set_id: str, version_id: str) -> Dict[str, Any]:
        if data_set_id not in self.versions_metadata: raise ValueError(f"Data set '{data_set_id}' not found.")
        
        version_info = next((v for v in self.versions_metadata[data_set_id] if v["version_id"] == version_id), None)
        if not version_info: raise ValueError(f"Version '{version_id}' not found for data set '{data_set_id}'.")

        with open(version_info["content_path"], 'r') as f: content = f.read()
        version_info["data_content"] = content
        return version_info

    def _list_versions(self, data_set_id: str) -> List[Dict[str, Any]]:
        if data_set_id not in self.versions_metadata: return []
        return self.versions_metadata[data_set_id]

    def _get_latest_version(self, data_set_id: str) -> Optional[Dict[str, Any]]:
        if data_set_id not in self.versions_metadata or not self.versions_metadata[data_set_id]: return None
        
        latest_version_info = max(self.versions_metadata[data_set_id], key=lambda v: v["created_at"])
        with open(latest_version_info["content_path"], 'r') as f: content = f.read()
        latest_version_info["data_content"] = content
        return latest_version_info

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_version":
            return self._create_version(kwargs.get("data_set_id"), kwargs.get("data_content"), kwargs.get("commit_message"))
        elif operation == "retrieve_version":
            return self._retrieve_version(kwargs.get("data_set_id"), kwargs.get("version_id"))
        elif operation == "list_versions":
            return self._list_versions(kwargs.get("data_set_id"))
        elif operation == "get_latest_version":
            return self._get_latest_version(kwargs.get("data_set_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataVersioningTool functionality...")
    tool = DataVersioningTool()
    
    try:
        print("\n--- Creating Version ---")
        tool.execute(operation="create_version", data_set_id="customer_data", data_content="{'id': 1, 'name': 'Alice'}", commit_message="Initial customer data")
        
        print("\n--- Listing Versions ---")
        versions = tool.execute(operation="list_versions", data_set_id="customer_data")
        print(json.dumps(versions, indent=2))

        print("\n--- Retrieving Latest Version ---")
        latest_version = tool.execute(operation="get_latest_version", data_set_id="customer_data")
        print(json.dumps(latest_version, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.metadata_file): os.remove(tool.metadata_file)
        if os.path.exists(tool.content_dir): shutil.rmtree(tool.content_dir)
        print("\nCleanup complete.")