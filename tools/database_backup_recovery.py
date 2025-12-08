import logging
import os
import shutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DatabaseBackupRecoveryTool(BaseTool):
    """
    A tool for simulating database backup and recovery operations.
    """

    def __init__(self, tool_name: str = "database_backup_recovery"):
        super().__init__(tool_name)
        self.metadata_file = "db_backups_metadata.json"
        self.default_backup_dir = "db_backups_content"
        self.backups_metadata: Dict[str, Dict[str, Any]] = self._load_backups_metadata()
        os.makedirs(self.default_backup_dir, exist_ok=True)

    @property
    def description(self) -> str:
        return "Simulates database backup and recovery: creates backups, restores from backups, and lists backup details."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The backup/recovery operation to perform.",
                    "enum": ["backup_database", "restore_database", "list_backups", "get_backup_details"]
                },
                "database_id": {"type": "string"},
                "database_name": {"type": "string"},
                "source_path": {"type": "string", "description": "Absolute path to the database files/directory to backup."},
                "backup_location": {"type": "string", "description": "Directory where the backup will be stored."},
                "backup_id": {"type": "string"},
                "target_path": {"type": "string", "description": "Absolute path to the directory where the database should be restored."}
            },
            "required": ["operation"]
        }

    def _load_backups_metadata(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted metadata file '{self.metadata_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_backups_metadata(self) -> None:
        with open(self.metadata_file, 'w') as f:
            json.dump(self.backups_metadata, f, indent=4)

    def _backup_database(self, database_id: str, database_name: str, source_path: str, backup_location: str = None) -> Dict[str, Any]:
        if not all([database_id, database_name, source_path]):
            raise ValueError("Database ID, name, and source path cannot be empty.")
        if not os.path.isabs(source_path): raise ValueError("Source path must be an absolute path.")
        if not os.path.exists(source_path): raise FileNotFoundError(f"Source '{source_path}' not found.")
        if database_id in self.backups_metadata: raise ValueError(f"Backup for database ID '{database_id}' already exists.")

        backup_loc = backup_location if backup_location else self.default_backup_dir
        os.makedirs(backup_loc, exist_ok=True)
        backup_id = f"BKUP-{database_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        specific_backup_dir = os.path.join(backup_loc, backup_id)
        os.makedirs(specific_backup_dir, exist_ok=True)

        if os.path.isfile(source_path):
            shutil.copy2(source_path, specific_backup_dir)
            backed_up_path = os.path.join(specific_backup_dir, os.path.basename(source_path))
        elif os.path.isdir(source_path):
            shutil.copytree(source_path, os.path.join(specific_backup_dir, os.path.basename(source_path)), dirs_exist_ok=True)
            backed_up_path = os.path.join(specific_backup_dir, os.path.basename(source_path))
        else: raise ValueError(f"Source path '{source_path}' is neither a file nor a directory.")

        backup_record = {
            "backup_id": backup_id, "database_id": database_id, "database_name": database_name,
            "source_path": source_path, "backup_location": os.path.abspath(specific_backup_dir),
            "backed_up_path": os.path.abspath(backed_up_path), "timestamp": datetime.now().isoformat(),
            "status": "completed"
        }
        self.backups_metadata[backup_id] = backup_record
        self._save_backups_metadata()
        return backup_record

    def _restore_database(self, backup_id: str, target_path: str) -> Dict[str, Any]:
        if not all([backup_id, target_path]): raise ValueError("Backup ID and target path cannot be empty.")
        if not os.path.isabs(target_path): raise ValueError("Target path must be an absolute path.")
        if backup_id not in self.backups_metadata: raise ValueError(f"Backup '{backup_id}' not found.")

        backup_record = self.backups_metadata[backup_id]
        backed_up_path = backup_record["backed_up_path"]

        if not os.path.exists(backed_up_path): raise FileNotFoundError(f"Backed up data not found at '{backed_up_path}'.")

        os.makedirs(target_path, exist_ok=True)

        if os.path.isdir(backed_up_path):
            for item in os.listdir(backed_up_path):
                s = os.path.join(backed_up_path, item)
                d = os.path.join(target_path, item)
                if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                else: shutil.copy2(s, d)
        elif os.path.isfile(backed_up_path): shutil.copy2(backed_up_path, target_path)
        
        restore_result = {
            "backup_id": backup_id, "database_id": backup_record["database_id"],
            "database_name": backup_record["database_name"], "restored_to_path": os.path.abspath(target_path),
            "timestamp": datetime.now().isoformat(), "status": "completed"
        }
        return restore_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "backup_database":
            return self._backup_database(kwargs.get("database_id"), kwargs.get("database_name"), kwargs.get("source_path"), kwargs.get("backup_location"))
        elif operation == "restore_database":
            return self._restore_database(kwargs.get("backup_id"), kwargs.get("target_path"))
        elif operation == "list_backups":
            return list(self.backups_metadata.values())
        elif operation == "get_backup_details":
            return self.backups_metadata.get(kwargs.get("backup_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DatabaseBackupRecoveryTool functionality...")
    tool = DatabaseBackupRecoveryTool()
    
    db_source_dir = os.path.abspath("my_database_files")
    restore_target_dir = os.path.abspath("restored_db")

    try:
        os.makedirs(db_source_dir, exist_ok=True)
        with open(os.path.join(db_source_dir, "data.db"), "w") as f: f.write("DB content v1")

        print("\n--- Backing up Database ---")
        backup_result = tool.execute(operation="backup_database", database_id="prod_db_001", database_name="Production DB", source_path=db_source_dir)
        print(json.dumps(backup_result, indent=2))
        backup_id = backup_result["backup_id"]

        print("\n--- Restoring Database ---")
        restore_result = tool.execute(operation="restore_database", backup_id=backup_id, target_path=restore_target_dir)
        print(json.dumps(restore_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(db_source_dir): shutil.rmtree(db_source_dir)
        if os.path.exists(restore_target_dir): shutil.rmtree(restore_target_dir)
        if os.path.exists(tool.metadata_file): os.remove(tool.metadata_file)
        if os.path.exists(tool.default_backup_dir): shutil.rmtree(tool.default_backup_dir)
        print("\nCleanup complete.")