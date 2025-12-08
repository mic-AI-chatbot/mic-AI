import logging
import os
import shutil
import json
from datetime import datetime
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataArchivingTool(BaseTool):
    """
    A tool for archiving and retrieving data on the local file system.
    """

    def __init__(self, tool_name: str = "data_archiving_tool"):
        super().__init__(tool_name)
        self.metadata_file = "archive_metadata.json"
        self.metadata: Dict[str, Any] = self._load_metadata()

    @property
    def description(self) -> str:
        return "Archives files to a specified directory and retrieves them, managing metadata for the archives."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The action to perform: 'archive', 'retrieve', or 'list'.",
                    "enum": ["archive", "retrieve", "list"]
                },
                "source_path": {
                    "type": "string",
                    "description": "The absolute path of the file to archive."
                },
                "archive_dir": {
                    "type": "string",
                    "description": "The directory to store the archived file.",
                    "default": "archive"
                },
                "archive_id": {
                    "type": "string",
                    "description": "The ID of the archive to retrieve."
                },
                "restore_path": {
                    "type": "string",
                    "description": "The absolute path to restore the file to."
                }
            },
            "required": ["operation"]
        }

    def _load_metadata(self) -> Dict[str, Any]:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted metadata file '{self.metadata_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_metadata(self) -> None:
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=4)

    def _archive_data(self, source_path: str, archive_dir: str) -> Dict[str, Any]:
        if not os.path.isabs(source_path):
            raise ValueError("Source path must be an absolute path.")
        if not os.path.exists(source_path) or not os.path.isfile(source_path):
            raise FileNotFoundError(f"Source file not found at '{source_path}'.")

        os.makedirs(archive_dir, exist_ok=True)
        archive_id = f"ARCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        archive_path = os.path.join(archive_dir, f"{archive_id}-{os.path.basename(source_path)}")

        shutil.move(source_path, archive_path)
        
        archive_entry = {
            "archive_id": archive_id,
            "original_path": source_path,
            "archived_path": os.path.abspath(archive_path),
            "archive_date": datetime.now().isoformat(),
            "status": "archived"
        }
        self.metadata[archive_id] = archive_entry
        self._save_metadata()
        logger.info(f"File '{source_path}' archived to '{archive_path}' with ID '{archive_id}'.")
        return archive_entry

    def _retrieve_data(self, archive_id: str, restore_path: str) -> Dict[str, Any]:
        if not os.path.isabs(restore_path):
            raise ValueError("Restore path must be an absolute path.")
        if archive_id not in self.metadata:
            raise ValueError(f"Archive ID '{archive_id}' not found.")

        archive_entry = self.metadata[archive_id]
        archived_file_path = archive_entry["archived_path"]

        if not os.path.exists(archived_file_path):
            raise FileNotFoundError(f"Archived file not found at '{archived_file_path}'.")

        os.makedirs(os.path.dirname(restore_path), exist_ok=True)
        shutil.move(archived_file_path, restore_path)
        
        archive_entry["status"] = "retrieved"
        archive_entry["restored_path"] = restore_path
        self._save_metadata()
        logger.info(f"File with ID '{archive_id}' retrieved to '{restore_path}'.")
        return archive_entry

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "archive":
            source_path = kwargs.get("source_path")
            if not source_path:
                raise ValueError("Missing 'source_path' for archive operation.")
            return self._archive_data(source_path, kwargs.get("archive_dir", "archive"))
        elif operation == "retrieve":
            archive_id = kwargs.get("archive_id")
            restore_path = kwargs.get("restore_path")
            if not all([archive_id, restore_path]):
                raise ValueError("Missing 'archive_id' or 'restore_path' for retrieve operation.")
            return self._retrieve_data(archive_id, restore_path)
        elif operation == "list":
            return list(self.metadata.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataArchivingTool functionality...")
    tool = DataArchivingTool()
    
    dummy_file = os.path.abspath("dummy_to_archive.txt")
    with open(dummy_file, "w") as f:
        f.write("This is test data.")

    archive_id = None
    restore_path = os.path.abspath("restored_file.txt")

    try:
        print(f"\n--- Archiving '{dummy_file}' ---")
        archive_result = tool.execute(operation="archive", source_path=dummy_file, archive_dir="temp_archive")
        print(json.dumps(archive_result, indent=2))
        archive_id = archive_result["archive_id"]

        print("\n--- Listing Archives ---")
        archives_list = tool.execute(operation="list")
        print(json.dumps(archives_list, indent=2))

        print(f"\n--- Retrieving '{archive_id}' to '{restore_path}' ---")
        retrieve_result = tool.execute(operation="retrieve", archive_id=archive_id, restore_path=restore_path)
        print(json.dumps(retrieve_result, indent=2))
        
        with open(restore_path, "r") as f:
            print(f"Restored file content: '{f.read()}'")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up
        if os.path.exists("temp_archive"):
            shutil.rmtree("temp_archive")
        if os.path.exists(tool.metadata_file):
            os.remove(tool.metadata_file)
        if os.path.exists(dummy_file):
            os.remove(dummy_file)
        if os.path.exists(restore_path):
            os.remove(restore_path)
        print("\nCleanup complete.")