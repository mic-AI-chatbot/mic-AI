import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SchemaMigrationSimulatorTool(BaseTool):
    """
    A tool that simulates schema migration, allowing for defining migrations,
    applying, reverting, and checking the status of migrations on a simulated database.
    """

    def __init__(self, tool_name: str = "SchemaMigrationSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.migrations_file = os.path.join(self.data_dir, "migration_definitions.json")
        self.databases_file = os.path.join(self.data_dir, "simulated_databases.json")
        
        # Migration definitions: {migration_id: {name: ..., up_script: ..., down_script: ...}}
        self.migration_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.migrations_file, default={})
        # Database schemas: {database_name: {schema: {table_name: {columns: []}}, applied_migrations: []}}
        self.database_schemas: Dict[str, Dict[str, Any]] = self._load_data(self.databases_file, default={})

    @property
    def description(self) -> str:
        return "Simulates schema migration: define, apply, revert, and check status of migrations on a database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_migration", "apply_migration", "revert_migration", "get_migration_status", "get_database_schema"]},
                "migration_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "up_script": {"type": "string", "description": "Simulated SQL or code for applying the migration."},
                "down_script": {"type": "string", "description": "Simulated SQL or code for reverting the migration."},
                "database_name": {"type": "string", "default": "default_db"}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_migrations(self):
        with open(self.migrations_file, 'w') as f: json.dump(self.migration_definitions, f, indent=2)

    def _save_databases(self):
        with open(self.databases_file, 'w') as f: json.dump(self.database_schemas, f, indent=2)

    def define_migration(self, migration_id: str, name: str, description: str, up_script: str, down_script: str) -> Dict[str, Any]:
        """Defines a new schema migration."""
        if migration_id in self.migration_definitions: raise ValueError(f"Migration '{migration_id}' already exists.")
        
        new_migration = {
            "id": migration_id, "name": name, "description": description,
            "up_script": up_script, "down_script": down_script,
            "defined_at": datetime.now().isoformat()
        }
        self.migration_definitions[migration_id] = new_migration
        self._save_migrations()
        return new_migration

    def apply_migration(self, migration_id: str, database_name: str = "default_db") -> Dict[str, Any]:
        """Simulates applying a schema migration to a database."""
        migration = self.migration_definitions.get(migration_id)
        if not migration: raise ValueError(f"Migration '{migration_id}' not found. Define it first.")
        
        if database_name not in self.database_schemas:
            self.database_schemas[database_name] = {"schema": {}, "applied_migrations": []}
        
        if migration_id in self.database_schemas[database_name]["applied_migrations"]:
            return {"status": "info", "message": f"Migration '{migration_id}' already applied to '{database_name}'."}

        # Simulate schema change (e.g., add a table or column)
        simulated_schema_change = {"table_users": {"columns": ["id", "name", "email", "new_column"]}}
        self.database_schemas[database_name]["schema"].update(simulated_schema_change)
        self.database_schemas[database_name]["applied_migrations"].append(migration_id)
        self._save_databases()
        return {"status": "success", "message": f"Migration '{migration_id}' applied to '{database_name}'."}

    def revert_migration(self, migration_id: str, database_name: str = "default_db") -> Dict[str, Any]:
        """Simulates reverting a schema migration from a database."""
        migration = self.migration_definitions.get(migration_id)
        if not migration: raise ValueError(f"Migration '{migration_id}' not found. Define it first.")
        
        if database_name not in self.database_schemas: raise ValueError(f"Database '{database_name}' not found.")
        if migration_id not in self.database_schemas[database_name]["applied_migrations"]:
            return {"status": "info", "message": f"Migration '{migration_id}' not applied to '{database_name}'."}

        # Simulate schema change (e.g., remove a table or column)
        simulated_schema_revert = {"table_users": {"columns": ["id", "name", "email"]}} # Revert to previous state
        self.database_schemas[database_name]["schema"].update(simulated_schema_revert)
        self.database_schemas[database_name]["applied_migrations"].remove(migration_id)
        self._save_databases()
        return {"status": "success", "message": f"Migration '{migration_id}' reverted from '{database_name}'."}

    def get_migration_status(self, migration_id: str, database_name: str = "default_db") -> Dict[str, Any]:
        """Retrieves the status of a specific migration on a database."""
        if migration_id not in self.migration_definitions: raise ValueError(f"Migration '{migration_id}' not found.")
        
        is_applied = False
        if database_name in self.database_schemas and migration_id in self.database_schemas[database_name]["applied_migrations"]:
            is_applied = True
        
        return {"status": "success", "migration_id": migration_id, "database_name": database_name, "is_applied": is_applied}

    def get_database_schema(self, database_name: str = "default_db") -> Dict[str, Any]:
        """Retrieves the current simulated schema of a database."""
        schema = self.database_schemas.get(database_name, {}).get("schema", {})
        return {"status": "success", "database_name": database_name, "schema": schema}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_migration":
            migration_id = kwargs.get('migration_id')
            name = kwargs.get('name')
            description = kwargs.get('description')
            up_script = kwargs.get('up_script')
            down_script = kwargs.get('down_script')
            if not all([migration_id, name, description, up_script, down_script]):
                raise ValueError("Missing 'migration_id', 'name', 'description', 'up_script', or 'down_script' for 'define_migration' operation.")
            return self.define_migration(migration_id, name, description, up_script, down_script)
        elif operation == "apply_migration":
            migration_id = kwargs.get('migration_id')
            if not migration_id:
                raise ValueError("Missing 'migration_id' for 'apply_migration' operation.")
            return self.apply_migration(migration_id, kwargs.get('database_name', 'default_db'))
        elif operation == "revert_migration":
            migration_id = kwargs.get('migration_id')
            if not migration_id:
                raise ValueError("Missing 'migration_id' for 'revert_migration' operation.")
            return self.revert_migration(migration_id, kwargs.get('database_name', 'default_db'))
        elif operation == "get_migration_status":
            migration_id = kwargs.get('migration_id')
            if not migration_id:
                raise ValueError("Missing 'migration_id' for 'get_migration_status' operation.")
            return self.get_migration_status(migration_id, kwargs.get('database_name', 'default_db'))
        elif operation == "get_database_schema":
            # database_name has a default value, so no strict check needed here
            return self.get_database_schema(kwargs.get('database_name', 'default_db'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SchemaMigrationSimulatorTool functionality...")
    temp_dir = "temp_schema_migration_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    migration_tool = SchemaMigrationSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a migration
        print("\n--- Defining migration 'add_user_address' ---")
        migration_tool.execute(operation="define_migration", migration_id="add_user_address", name="Add Address to Users",
                               description="Adds an address column to the users table.",
                               up_script="ALTER TABLE users ADD COLUMN address VARCHAR(255);",
                               down_script="ALTER TABLE users DROP COLUMN address;")
        print("Migration defined.")

        # 2. Apply the migration
        print("\n--- Applying migration 'add_user_address' to 'main_db' ---")
        migration_tool.execute(operation="apply_migration", migration_id="add_user_address", database_name="main_db")
        print("Migration applied.")

        # 3. Get migration status
        print("\n--- Getting migration status for 'add_user_address' on 'main_db' ---")
        status = migration_tool.execute(operation="get_migration_status", migration_id="add_user_address", database_name="main_db")
        print(json.dumps(status, indent=2))

        # 4. Get database schema
        print("\n--- Getting schema for 'main_db' ---")
        schema = migration_tool.execute(operation="get_database_schema", migration_id="any", database_name="main_db") # migration_id is not used for get_database_schema
        print(json.dumps(schema, indent=2))

        # 5. Revert the migration
        print("\n--- Reverting migration 'add_user_address' from 'main_db' ---")
        migration_tool.execute(operation="revert_migration", migration_id="add_user_address", database_name="main_db")
        print("Migration reverted.")

        # 6. Get database schema again
        print("\n--- Getting schema for 'main_db' after revert ---")
        schema_after_revert = migration_tool.execute(operation="get_database_schema", migration_id="any", database_name="main_db")
        print(json.dumps(schema_after_revert, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")