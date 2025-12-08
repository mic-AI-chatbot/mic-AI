import logging
import os
import shutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DigitalAssetManagementSystemTool(BaseTool):
    """
    A tool for simulating a Digital Asset Management (DAM) system.
    """

    def __init__(self, tool_name: str = "digital_asset_management_system"):
        super().__init__(tool_name)
        self.metadata_file = "digital_assets_metadata.json"
        self.content_dir = "digital_assets_content"
        self.assets_metadata: Dict[str, Dict[str, Any]] = self._load_assets_metadata()
        os.makedirs(self.content_dir, exist_ok=True)

    @property
    def description(self) -> str:
        return "Simulates a Digital Asset Management (DAM) system: uploads, retrieves, downloads, and manages digital assets."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The asset management operation to perform.",
                    "enum": ["upload_asset", "get_asset_details", "download_asset", "list_assets"]
                },
                "asset_name": {"type": "string"},
                "asset_type": {"type": "string"},
                "file_path": {"type": "string", "description": "Absolute path to the source file for upload."},
                "tags": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string"},
                "asset_id": {"type": "string"},
                "destination_path": {"type": "string", "description": "Absolute path to save the downloaded asset."},
                "filter_asset_type": {"type": "string"},
                "filter_tag": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_assets_metadata(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted metadata file '{self.metadata_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_assets_metadata(self) -> None:
        with open(self.metadata_file, 'w') as f:
            json.dump(self.assets_metadata, f, indent=4)

    def _get_asset_storage_path(self, asset_id: str, file_name: str) -> str:
        asset_dir = os.path.join(self.content_dir, asset_id)
        os.makedirs(asset_dir, exist_ok=True)
        return os.path.join(asset_dir, file_name)

    def _upload_asset(self, asset_name: str, asset_type: str, file_path: str, tags: Optional[List[str]] = None, description: Optional[str] = None) -> Dict[str, Any]:
        if not all([asset_name, asset_type, file_path]): raise ValueError("Asset name, type, and file path cannot be empty.")
        if not os.path.isabs(file_path): raise ValueError("File path must be an absolute path.")
        if not os.path.exists(file_path) or not os.path.isfile(file_path): raise FileNotFoundError(f"Source file not found at '{file_path}'.")

        asset_id = f"ASSET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        file_name = os.path.basename(file_path)
        stored_file_path = self._get_asset_storage_path(asset_id, file_name)

        shutil.copy2(file_path, stored_file_path)
        
        new_asset = {
            "asset_id": asset_id, "asset_name": asset_name, "asset_type": asset_type,
            "description": description, "tags": tags or [], "original_file_name": file_name,
            "stored_file_path": os.path.abspath(stored_file_path), "uploaded_at": datetime.now().isoformat()
        }
        self.assets_metadata[asset_id] = new_asset
        self._save_assets_metadata()
        return new_asset

    def _get_asset_details(self, asset_id: str) -> Optional[Dict[str, Any]]:
        return self.assets_metadata.get(asset_id)

    def _download_asset(self, asset_id: str, destination_path: str) -> Dict[str, Any]:
        if not all([asset_id, destination_path]): raise ValueError("Asset ID and destination path cannot be empty.")
        if not os.path.isabs(destination_path): raise ValueError("Destination path must be an absolute path.")
        asset = self.assets_metadata.get(asset_id)
        if not asset: raise ValueError(f"Asset '{asset_id}' not found.")
        
        source_file_path = asset["stored_file_path"]
        if not os.path.exists(source_file_path): raise FileNotFoundError(f"Stored asset file not found at '{source_file_path}'.")

        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.copy2(source_file_path, destination_path)
        
        download_result = {
            "asset_id": asset_id, "asset_name": asset["asset_name"], "downloaded_to": os.path.abspath(destination_path),
            "downloaded_at": datetime.now().isoformat(), "status": "completed"
        }
        return download_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "upload_asset":
            return self._upload_asset(kwargs.get("asset_name"), kwargs.get("asset_type"), kwargs.get("file_path"), kwargs.get("tags"), kwargs.get("description"))
        elif operation == "get_asset_details":
            return self._get_asset_details(kwargs.get("asset_id"))
        elif operation == "download_asset":
            return self._download_asset(kwargs.get("asset_id"), kwargs.get("destination_path"))
        elif operation == "list_assets":
            asset_type = kwargs.get("filter_asset_type")
            tag = kwargs.get("filter_tag")
            filtered_assets = list(self.assets_metadata.values())
            if asset_type: filtered_assets = [a for a in filtered_assets if a.get("asset_type") == asset_type]
            if tag: filtered_assets = [a for a in filtered_assets if tag in a.get("tags", [])]
            return filtered_assets
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DigitalAssetManagementSystemTool functionality...")
    tool = DigitalAssetManagementSystemTool()
    
    dummy_image_path = os.path.abspath("dummy_image.jpg")
    download_dir = os.path.abspath("downloaded_assets")

    try:
        with open(dummy_image_path, "w") as f: f.write("simulated image content")
        os.makedirs(download_dir, exist_ok=True)

        print("\n--- Uploading Asset ---")
        asset_result = tool.execute(operation="upload_asset", asset_name="Product_Hero_Image", asset_type="image", file_path=dummy_image_path, tags=["product", "marketing"])
        print(json.dumps(asset_result, indent=2))
        asset_id = asset_result["asset_id"]

        print("\n--- Downloading Asset ---")
        download_path = os.path.join(download_dir, "downloaded_image.jpg")
        download_result = tool.execute(operation="download_asset", asset_id=asset_id, destination_path=download_path)
        print(json.dumps(download_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(dummy_image_path): os.remove(dummy_image_path)
        if os.path.exists(tool.metadata_file): os.remove(tool.metadata_file)
        if os.path.exists(tool.content_dir): shutil.rmtree(tool.content_dir)
        if os.path.exists(download_dir): shutil.rmtree(download_dir)
        print("\nCleanup complete.")
