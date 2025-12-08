import logging
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DatabaseQueryTool(BaseTool):
    """
    A tool for simulating database query operations.
    """

    def __init__(self, tool_name: str = "database_query_tool"):
        super().__init__(tool_name)
        self.db_file = "simulated_database.json"
        self.db_state: Dict[str, Dict[str, Any]] = self._load_db_state()
        if "databases" not in self.db_state:
            self.db_state["databases"] = {}

    @property
    def description(self) -> str:
        return "Simulates database query operations: creates tables, inserts data, executes SQL-like queries, updates, and deletes data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The database operation to perform.",
                    "enum": ["create_table", "insert_data", "execute_query", "update_data", "delete_data", "get_table_schema", "list_tables"]
                },
                "db_id": {"type": "string"},
                "table_name": {"type": "string"},
                "schema": {"type": "object"},
                "data": {"type": "object"},
                "query": {"type": "string"},
                "set_data": {"type": "object"},
                "where_clause": {"type": "string"}
            },
            "required": ["operation", "db_id"]
        }

    def _load_db_state(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted database file '{self.db_file}'. Starting fresh.")
                    return {"databases": {}}
        return {"databases": {}}

    def _save_db_state(self) -> None:
        with open(self.db_file, 'w') as f:
            json.dump(self.db_state, f, indent=4)

    def _get_database(self, db_id: str) -> Dict[str, Any]:
        if db_id not in self.db_state["databases"]:
            self.db_state["databases"][db_id] = {"tables": {}}
        return self.db_state["databases"][db_id]

    def _create_table(self, db_id: str, table_name: str, schema: Dict[str, str]) -> Dict[str, Any]:
        db = self._get_database(db_id)
        if table_name in db["tables"]: raise ValueError(f"Table '{table_name}' already exists in database '{db_id}'.")
        if not schema: raise ValueError("Table schema cannot be empty.")

        new_table = {
            "table_name": table_name, "schema": schema, "data": [], "created_at": datetime.now().isoformat()
        }
        db["tables"][table_name] = new_table
        self._save_db_state()
        return new_table

    def _insert_data(self, db_id: str, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        db = self._get_database(db_id)
        table = db["tables"].get(table_name)
        if not table: raise ValueError(f"Table '{table_name}' not found in database '{db_id}'.")
        
        for col, col_type in table["schema"].items():
            if col not in data: logger.warning(f"Missing column '{col}' in insert data for table '{table_name}'.")

        table["data"].append(data)
        self._save_db_state()
        return data

    def _execute_query(self, db_id: str, query: str) -> List[Dict[str, Any]]:
        db = self._get_database(db_id)
        query_upper = query.upper().strip()

        if query_upper.startswith("SELECT"):
            parts = query_upper.split("FROM", 1)
            if len(parts) < 2: raise ValueError("Invalid SELECT query format.")
            
            from_part = parts[1].strip()
            table_name_match = re.match(r"(\w+)", from_part)
            if not table_name_match: raise ValueError("Could not parse table name from query.")
            table_name = table_name_match.group(1)

            table = db["tables"].get(table_name)
            if not table: raise ValueError(f"Table '{table_name}' not found in database '{db_id}'.")
            
            where_clause = ""
            if "WHERE" in query_upper: where_clause = query_upper.split("WHERE", 1)[1].strip()

            results = []
            for record in table["data"]:
                match = True
                if where_clause:
                    try:
                        col, op, val = where_clause.split(maxsplit=2)
                        col = col.strip(); op = op.strip(); val = val.strip().strip("'\"")
                        record_value = record.get(col)
                        if record_value is None: match = False
                        else:
                            if isinstance(record_value, (int, float)): val = type(record_value)(val)
                            if op == "=": match = (record_value == val)
                            elif op == "!=": match = (record_value != val)
                            elif op == ">": match = (record_value > val)
                            elif op == "<": match = (record_value < val)
                            elif op == ">=": match = (record_value >= val)
                            elif op == "<=": match = (record_value <= val)
                            else: match = True
                    except ValueError: match = True
                if match: results.append(record)
            return results
        else:
            logger.warning(f"Unsupported query type: '{query}'. Only SELECT queries are simulated.")
            return []

    def _update_data(self, db_id: str, table_name: str, set_data: Dict[str, Any], where_clause: Optional[str] = None) -> Dict[str, Any]:
        db = self._get_database(db_id)
        table = db["tables"].get(table_name)
        if not table: raise ValueError(f"Table '{table_name}' not found in database '{db_id}'.")
        
        updated_count = 0
        for record in table["data"]:
            should_update = True
            if where_clause:
                try:
                    col, op, val = where_clause.split(maxsplit=2)
                    col = col.strip(); op = op.strip(); val = val.strip().strip("'\"")
                    record_value = record.get(col)
                    if record_value is None: should_update = False
                    else:
                        if isinstance(record_value, (int, float)): val = type(record_value)(val)
                        if op == "=": should_update = (record_value == val)
                        elif op == "!=": should_update = (record_value != val)
                        elif op == ">": should_update = (record_value > val)
                        elif op == "<": should_update = (record_value < val)
                        elif op == ">=": should_update = (record_value >= val)
                        elif op == "<=": should_update = (record_value <= val)
                        else: should_update = False
                except ValueError: should_update = False
            
            if should_update: record.update(set_data); updated_count += 1
        
        self._save_db_state()
        return {"table_name": table_name, "updated_count": updated_count}

    def _delete_data(self, db_id: str, table_name: str, where_clause: Optional[str] = None) -> Dict[str, Any]:
        db = self._get_database(db_id)
        table = db["tables"].get(table_name)
        if not table: raise ValueError(f"Table '{table_name}' not found in database '{db_id}'.")
        
        initial_count = len(table["data"])
        if not where_clause: table["data"] = []
        else:
            remaining_data = []
            for record in table["data"]:
                should_delete = True
                try:
                    col, op, val = where_clause.split(maxsplit=2)
                    col = col.strip(); op = op.strip(); val = val.strip().strip("'\"")
                    record_value = record.get(col)
                    if record_value is None: should_delete = False
                    else:
                        if isinstance(record_value, (int, float)): val = type(record_value)(val)
                        if op == "=": should_delete = (record_value == val)
                        elif op == "!=": should_delete = (record_value != val)
                        elif op == ">": should_delete = (record_value > val)
                        elif op == "<": should_delete = (record_value < val)
                        elif op == ">=": should_delete = (record_value >= val)
                        elif op == "<=": should_delete = (record_value <= val)
                        else: should_delete = False
                except ValueError: should_delete = False
                
                if not should_delete: remaining_data.append(record)
            table["data"] = remaining_data
        
        deleted_count = initial_count - len(table["data"])
        self._save_db_state()
        return {"table_name": table_name, "deleted_count": deleted_count}

    def execute(self, operation: str, db_id: str, **kwargs: Any) -> Any:
        if operation == "create_table":
            return self._create_table(db_id, kwargs.get("table_name"), kwargs.get("schema"))
        elif operation == "insert_data":
            return self._insert_data(db_id, kwargs.get("table_name"), kwargs.get("data"))
        elif operation == "execute_query":
            return self._execute_query(db_id, kwargs.get("query"))
        elif operation == "update_data":
            return self._update_data(db_id, kwargs.get("table_name"), kwargs.get("set_data"), kwargs.get("where_clause"))
        elif operation == "delete_data":
            return self._delete_data(db_id, kwargs.get("table_name"), kwargs.get("where_clause"))
        elif operation == "get_table_schema":
            return self._get_database(db_id)["tables"].get(kwargs.get("table_name"))["schema"]
        elif operation == "list_tables":
            return list(self._get_database(db_id)["tables"].keys())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DatabaseQueryTool functionality...")
    tool = DatabaseQueryTool()
    
    try:
        print("\n--- Creating Table ---")
        tool.execute(operation="create_table", db_id="my_app_db", table_name="users", schema={"id": "INTEGER", "name": "TEXT"})
        
        print("\n--- Inserting Data ---")
        tool.execute(operation="insert_data", db_id="my_app_db", table_name="users", data={"id": 1, "name": "Alice"})

        print("\n--- Executing Query ---")
        query_results = tool.execute(operation="execute_query", db_id="my_app_db", query="SELECT * FROM users WHERE id = 1")
        print(json.dumps(query_results, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.db_file): os.remove(tool.db_file)
        print("\nCleanup complete.")
