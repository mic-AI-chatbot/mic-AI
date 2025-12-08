import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DatabaseMigrationTool(BaseTool):
    """
    A tool for simulating database migration processes.
    """

    def __init__(self, tool_name: str = "database_migration_tool"):
        super().__init__(tool_name)
        self.migrations_file = "db_migrations.json"
        self.migrations: Dict[str, Dict[str, Any]] = self._load_migrations()

    @property
    def description(self) -> str:
        return "Simulates database migration processes: creates, applies, reverts, and lists migrations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The migration operation to perform.",
                    "enum": ["create_migration", "apply_migration", "revert_migration", "list_migrations", "get_migration_status"]
                },
                "migration_id": {"type": "string"},
                "description": {"type": "string"},
                "db_type": {"type": "string", "default": "generic"}
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

    def _create_migration(self, migration_id: str, description: str, db_type: str = "generic") -> Dict[str, Any]:
        if not all([migration_id, description]):
            raise ValueError("Migration ID and description cannot be empty.")
        if migration_id in self.migrations:
            raise ValueError(f"Migration '{migration_id}' already exists.")

        new_migration = {
            "migration_id": migration_id, "description": description, "db_type": db_type,
            "status": "pending", "created_at": datetime.now().isoformat(),
            "applied_at": None, "reverted_at": None
        }
        self.migrations[migration_id] = new_migration
        self._save_migrations()
        return new_migration

    def _apply_migration(self, migration_id: str) -> Dict[str, Any]:
        migration = self.migrations.get(migration_id)
        if not migration: raise ValueError(f"Migration '{migration_id}' not found.")
        if migration["status"] == "applied": raise ValueError(f"Migration '{migration_id}' is already applied.")

        migration["status"] = "applied"
        migration["applied_at"] = datetime.now().isoformat()
        self._save_migrations()
        return migration

    def _revert_migration(self, migration_id: str) -> Dict[str, Any]:
        migration = self.migrations.get(migration_id)
        if not migration: raise ValueError(f"Migration '{migration_id}' not found.")
        if migration["status"] == "reverted": raise ValueError(f"Migration '{migration_id}' is already reverted.")

        migration["status"] = "reverted"
        migration["reverted_at"] = datetime.now().isoformat()
        self._save_migrations()
        return migration

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_migration":
            return self._create_migration(kwargs.get("migration_id"), kwargs.get("description"), kwargs.get("db_type", "generic"))
        elif operation == "apply_migration":
            return self._apply_migration(kwargs.get("migration_id"))
        elif operation == "revert_migration":
            return self._revert_migration(kwargs.get("migration_id"))
        elif operation == "list_migrations":
            db_type = kwargs.get("db_type")
            if db_type: return [m for m in self.migrations.values() if m.get("db_type") == db_type]
            return list(self.migrations.values())
        elif operation == "get_migration_status":
            return self.migrations.get(kwargs.get("migration_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DatabaseMigrationTool functionality...")
    tool = DatabaseMigrationTool()
    
    try:
        print("\n--- Creating Migration ---")
        tool.execute(operation="create_migration", migration_id="001_initial_schema", description="Setup initial database schema.", db_type="sqlite")
        
        print("\n--- Applying Migration ---")
        tool.execute(operation="apply_migration", migration_id="001_initial_schema")

        print("\n--- Getting Migration Status ---")
        status = tool.execute(operation="get_migration_status", migration_id="001_initial_schema")
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.migrations_file): os.remove(tool.migrations_file)
        print("\nCleanup complete.")