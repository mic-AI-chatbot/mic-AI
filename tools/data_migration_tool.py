import logging
import os
import shutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataMigrationTool(BaseTool):
    """
    A tool for simulating data migration processes.
    """

    def __init__(self, tool_name: str = "data_migration_tool"):
        super().__init__(tool_name)
        self.migrations_file = "data_migrations.json"
        self.migrations: Dict[str, Dict[str, Any]] = self._load_migrations()

    @property
    def description(self) -> str:
        return "Simulates data migration processes, including starting, tracking status, listing, and verifying migrations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The migration operation to perform.",
                    "enum": ["start_migration", "get_migration_status", "list_migrations", "verify_migration"]
                },
                "migration_id": {"type": "string"},
                "source_path": {"type": "string", "description": "Absolute path to the source directory or file."},
                "target_path": {"type": "string", "description": "Absolute path to the target directory."},
                "data_set_name": {"type": "string", "default": "all_data"}
            },
            "required": ["operation"]
        }

    def _load_migrations(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.migrations_file):
            with open(self.migrations_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted migrations file '{self.migrations_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_migrations(self) -> None:
        with open(self.migrations_file, 'w') as f:
            json.dump(self.migrations, f, indent=4)

    def _start_migration(self, migration_id: str, source_path: str, target_path: str, data_set_name: str = "all_data") -> Dict[str, Any]:
        if not os.path.isabs(source_path) or not os.path.isabs(target_path):
            raise ValueError("Source and target paths must be absolute paths.")
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source '{source_path}' not found.")
        if migration_id in self.migrations:
            raise ValueError(f"Migration with ID '{migration_id}' already exists.")

        os.makedirs(target_path, exist_ok=True)

        migration_record = {
            "migration_id": migration_id, "source_path": source_path, "target_path": target_path,
            "data_set_name": data_set_name, "status": "in_progress", "started_at": datetime.now().isoformat(),
            "completed_at": None, "files_migrated": 0, "total_files": 0, "errors": []
        }
        self.migrations[migration_id] = migration_record
        self._save_migrations()

        try:
            if os.path.isfile(source_path):
                shutil.copy2(source_path, target_path)
                migration_record["files_migrated"] = 1
                migration_record["total_files"] = 1
            elif os.path.isdir(source_path):
                for item in os.listdir(source_path):
                    s = os.path.join(source_path, item)
                    d = os.path.join(target_path, item)
                    if os.path.isdir(s): shutil.copytree(s, d, dirs_exist_ok=True)
                    else: shutil.copy2(s, d)
                    migration_record["files_migrated"] += 1
                migration_record["total_files"] = len(os.listdir(source_path))
            
            migration_record["status"] = "completed"
            migration_record["completed_at"] = datetime.now().isoformat()
        except Exception as e:
            migration_record["status"] = "failed"
            migration_record["errors"].append(str(e))
        finally:
            self._save_migrations()
        
        return migration_record

    def _get_migration_status(self, migration_id: str) -> Optional[Dict[str, Any]]:
        return self.migrations.get(migration_id)

    def _list_migrations(self) -> List[Dict[str, Any]]:
        return list(self.migrations.values())

    def _verify_migration(self, migration_id: str) -> Dict[str, Any]:
        migration = self._get_migration_status(migration_id)
        if not migration: raise ValueError(f"Migration '{migration_id}' not found.")
        if migration["status"] != "completed": return {"migration_id": migration_id, "status": "not_completed", "message": "Migration is not yet completed, cannot verify."}

        source_path = migration["source_path"]
        target_path = migration["target_path"]
        
        verification_status = "verified"
        issues = []

        if os.path.isfile(source_path):
            if not os.path.exists(os.path.join(target_path, os.path.basename(source_path))):
                issues.append(f"Migrated file '{os.path.basename(source_path)}' not found in target.")
                verification_status = "failed"
        elif os.path.isdir(source_path):
            source_files = set(os.listdir(source_path))
            target_files = set(os.listdir(target_path))
            missing_in_target = source_files - target_files
            if missing_in_target:
                issues.append(f"Files missing in target: {', '.join(missing_in_target)}")
                verification_status = "failed"
        
        return {
            "migration_id": migration_id, "verification_status": verification_status,
            "issues": issues, "verified_at": datetime.now().isoformat()
        }

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "start_migration":
            return self._start_migration(kwargs.get("migration_id"), kwargs.get("source_path"), kwargs.get("target_path"), kwargs.get("data_set_name"))
        elif operation == "get_migration_status":
            return self._get_migration_status(kwargs.get("migration_id"))
        elif operation == "list_migrations":
            return self._list_migrations()
        elif operation == "verify_migration":
            return self._verify_migration(kwargs.get("migration_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataMigrationTool functionality...")
    tool = DataMigrationTool()
    
    source_dir = os.path.abspath("source_data")
    target_dir = os.path.abspath("target_data")
    
    try:
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(source_dir, "file1.txt"), "w") as f: f.write("content1")

        print("\n--- Starting Migration ---")
        migration_result = tool.execute(operation="start_migration", migration_id="mig_001", source_path=source_dir, target_path=target_dir)
        print(json.dumps(migration_result, indent=2))

        print("\n--- Verifying Migration ---")
        verification_result = tool.execute(operation="verify_migration", migration_id="mig_001")
        print(json.dumps(verification_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(source_dir): shutil.rmtree(source_dir)
        if os.path.exists(target_dir): shutil.rmtree(target_dir)
        if os.path.exists(tool.migrations_file): os.remove(tool.migrations_file)
        print("\nCleanup complete.")