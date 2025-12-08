import logging
import json
import sqlite3
import random
import re
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

DB_FILE = "customs_declarations.db"

class CustomsDBManager:
    """Manages customs declarations in a SQLite database."""
    _instance = None

    def __new__(cls, db_file):
        if cls._instance is None:
            cls._instance = super(CustomsDBManager, cls).__new__(cls)
            cls._instance.db_file = db_file
            cls._instance._create_table()
        return cls._instance

    def _get_connection(self):
        return sqlite3.connect(self.db_file)

    def _create_table(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS declarations (
                        declaration_id TEXT PRIMARY KEY,
                        shipment_details TEXT NOT NULL, -- Stored as JSON string
                        items TEXT NOT NULL, -- Stored as JSON string
                        total_declared_value REAL NOT NULL,
                        declaration_date TEXT NOT NULL,
                        status TEXT NOT NULL,
                        warnings TEXT, -- Stored as JSON string
                        validation_report TEXT -- Stored as JSON string
                    )
                """)
        except sqlite3.Error as e:
            logger.error(f"Database table creation error: {e}")

    def add_declaration(self, declaration_id: str, shipment_details: Dict[str, Any], items: List[Dict[str, Any]], total_declared_value: float, declaration_date: str, status: str, warnings: List[str]) -> bool:
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO declarations (declaration_id, shipment_details, items, total_declared_value, declaration_date, status, warnings) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (declaration_id, json.dumps(shipment_details), json.dumps(items), total_declared_value, declaration_date, status, json.dumps(warnings))
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def get_declaration(self, declaration_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM declarations WHERE declaration_id = ?", (declaration_id,))
            row = cursor.fetchone()
            if row:
                declaration = dict(row)
                declaration["shipment_details"] = json.loads(declaration["shipment_details"])
                declaration["items"] = json.loads(declaration["items"])
                declaration["warnings"] = json.loads(declaration["warnings"])
                if declaration["validation_report"]:
                    declaration["validation_report"] = json.loads(declaration["validation_report"])
                return declaration
            return None

    def list_declarations(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT declaration_id, total_declared_value, declaration_date, status FROM declarations WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY declaration_date DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_declaration_validation_report(self, declaration_id: str, validation_report: Dict[str, Any], new_status: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE declarations SET validation_report = ?, status = ? WHERE declaration_id = ?",
                (json.dumps(validation_report), new_status, declaration_id)
            )
            return cursor.rowcount > 0

customs_db_manager = CustomsDBManager(DB_FILE)

class GenerateCustomsDeclarationTool(BaseTool):
    """Generates a customs declaration form and stores it persistently."""
    def __init__(self, tool_name="generate_customs_declaration"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a customs declaration form based on shipment details and a list of items, returning a declaration ID and summary."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "declaration_id": {"type": "string"},
                "shipment_details": {
                    "type": "object",
                    "description": "Details of the shipment (e.g., {'shipper': 'Company A', 'consignee': 'Company B', 'destination_country': 'USA'})."
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "quantity": {"type": "integer"},
                            "value": {"type": "number"},
                            "hs_code": {"type": "string", "description": "Optional: Harmonized System code (e.g., '851712')."}
                        },
                        "required": ["description", "quantity", "value"]
                    },
                    "description": "A list of items in the shipment, each with description, quantity, value, and optional HS code."
                }
            },
            "required": ["declaration_id", "shipment_details", "items"]
        }

    def execute(self, declaration_id: str, shipment_details: Dict[str, Any], items: List[Dict[str, Any]], **kwargs: Any) -> str:
        total_value = sum(item.get("value", 0) * item.get("quantity", 1) for item in items)
        
        warnings = []
        missing_hs_codes = [item["description"] for item in items if "hs_code" not in item or not item["hs_code"]]
        if missing_hs_codes:
            warnings.append(f"Missing HS codes for items: {', '.join(missing_hs_codes)}. May cause delays.")

        success = customs_db_manager.add_declaration(declaration_id, shipment_details, items, total_value, datetime.now().strftime('%Y-%m-%d'), "generated", warnings)
        
        if success:
            report = {
                "message": f"Customs declaration '{declaration_id}' generated successfully.",
                "declaration_id": declaration_id,
                "total_declared_value": round(total_value, 2),
                "warnings": warnings
            }
        else:
            report = {"error": f"Declaration with ID '{declaration_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class ValidateCustomsDeclarationTool(BaseTool):
    """Validates a customs declaration against a set of rules."""
    def __init__(self, tool_name="validate_customs_declaration"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Validates a customs declaration against a set of rules (e.g., completeness, HS code validity, value accuracy), returning a validation report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "declaration_id": {"type": "string"},
                "validation_rules": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["completeness", "hs_codes", "value_accuracy"]},
                    "default": ["completeness", "hs_codes"]
                }
            },
            "required": ["declaration_id"]
        }

    def execute(self, declaration_id: str, validation_rules: List[str] = ["completeness", "hs_codes"], **kwargs: Any) -> str:
        declaration = customs_db_manager.get_declaration(declaration_id)
        if not declaration:
            return json.dumps({"error": f"Declaration with ID '{declaration_id}' not found."})
        
        validation_report = {
            "declaration_id": declaration_id,
            "validation_status": "passed",
            "issues": []
        }

        if "completeness" in validation_rules:
            required_shipment_fields = ["shipper", "consignee", "destination_country"]
            for field in required_shipment_fields:
                if field not in declaration["shipment_details"]:
                    validation_report["issues"].append(f"Missing required shipment detail: '{field}'.")
                    validation_report["validation_status"] = "failed"
            if not declaration["items"]:
                validation_report["issues"].append("No items declared in the shipment.")
                validation_report["validation_status"] = "failed"

        if "hs_codes" in validation_rules:
            for item in declaration["items"]:
                if "hs_code" not in item or not item["hs_code"]:
                    validation_report["issues"].append(f"Missing HS code for item: '{item.get('description', 'N/A')}'.")
                    validation_report["validation_status"] = "failed"
                elif not re.fullmatch(r'\d{6}', item["hs_code"]): # Simulate 6-digit HS code
                    validation_report["issues"].append(f"Invalid HS code format for item: '{item.get('description', 'N/A')}'. Must be 6 digits.")
                    validation_report["validation_status"] = "failed"

        if "value_accuracy" in validation_rules:
            # Simulate checking if declared value is within a reasonable range
            if declaration["total_declared_value"] < 10.0 and any(item["value"] > 50 for item in declaration["items"]):
                validation_report["issues"].append("Total declared value seems unusually low compared to item values.")
                validation_report["validation_status"] = "failed"

        new_status = "validated" if validation_report["validation_status"] == "passed" else "validation_failed"
        customs_db_manager.update_declaration_validation_report(declaration_id, validation_report, new_status)

        return json.dumps(validation_report, indent=2)

class GetDeclarationDetailsTool(BaseTool):
    """Retrieves the full details of a specific customs declaration."""
    def __init__(self, tool_name="get_declaration_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the full details of a specific customs declaration, including shipment details, items, total value, and validation report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"declaration_id": {"type": "string"}},
            "required": ["declaration_id"]
        }

    def execute(self, declaration_id: str, **kwargs: Any) -> str:
        declaration = customs_db_manager.get_declaration(declaration_id)
        if not declaration:
            return json.dumps({"error": f"Declaration with ID '{declaration_id}' not found."})
            
        return json.dumps(declaration, indent=2)

class ListDeclarationsTool(BaseTool):
    """Lists all customs declarations."""
    def __init__(self, tool_name="list_declarations"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all customs declarations, showing their ID, total declared value, date, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["generated", "validated", "validation_failed"], "default": None}
            },
            "required": []
        }

    def execute(self, status: Optional[str] = None, **kwargs: Any) -> str:
        declarations = customs_db_manager.list_declarations(status)
        if not declarations:
            return json.dumps({"message": "No customs declarations found matching the criteria."})
        
        return json.dumps({"total_declarations": len(declarations), "declarations": declarations}, indent=2)