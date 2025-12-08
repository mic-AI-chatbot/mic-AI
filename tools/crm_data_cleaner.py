import logging
import json
import sqlite3
import random
import re
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

DB_FILE = "crm_data.db"

class CRMDBManager:
    """Manages CRM records in a SQLite database."""
    _instance = None

    def __new__(cls, db_file):
        if cls._instance is None:
            cls._instance = super(CRMDBManager, cls).__new__(cls)
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
                    CREATE TABLE IF NOT EXISTS records (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT,
                        phone TEXT,
                        address TEXT,
                        status TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
        except sqlite3.Error as e:
            logger.error(f"Database table creation error: {e}")

    def add_record(self, record_id: str, name: str, email: str, phone: Optional[str], address: Optional[str]) -> bool:
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                now = datetime.now().isoformat() + "Z"
                cursor.execute(
                    "INSERT INTO records (id, name, email, phone, address, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (record_id, name, email, phone, address, "active", now, now)
                )
                return True
            except sqlite3.IntegrityError: # Handles PRIMARY KEY constraint failure
                return False

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_records(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = "SELECT id, name, email, status FROM records WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_record(self, record_id: str, updates: Dict[str, Any]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            set_clauses = []
            params = []
            
            # Whitelist of allowed columns to update to prevent SQL injection
            allowed_columns = ["name", "email", "phone", "address", "status"]

            for key, value in updates.items():
                if key not in allowed_columns:
                    logger.warning(f"Attempted to update disallowed column: {key}. Skipping.")
                    continue
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            if not set_clauses: # No valid updates provided
                return False

            params.append(datetime.now().isoformat() + "Z") # updated_at
            params.append(record_id)
            
            query = f"UPDATE records SET {', '.join(set_clauses)}, updated_at = ? WHERE id = ?" # nosec B608
            cursor.execute(query, params)
            return cursor.rowcount > 0

    def delete_record(self, record_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
            return cursor.rowcount > 0

crm_db_manager = CRMDBManager(DB_FILE)

class AddCRMRecordTool(BaseTool):
    """Adds a new CRM record to the database."""
    def __init__(self, tool_name="add_crm_record"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new CRM record with contact details to the database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "A unique ID for the CRM record."},
                "name": {"type": "string", "description": "The name of the contact."},
                "email": {"type": "string", "description": "The email address of the contact."},
                "phone": {"type": "string", "description": "Optional: The phone number of the contact.", "default": None},
                "address": {"type": "string", "description": "Optional: The address of the contact.", "default": None}
            },
            "required": ["record_id", "name", "email"]
        }

    def execute(self, record_id: str, name: str, email: str, phone: Optional[str] = None, address: Optional[str] = None, **kwargs: Any) -> str:
        success = crm_db_manager.add_record(record_id, name, email, phone, address)
        if success:
            report = {"message": f"CRM record '{record_id}' ('{name}') added successfully."}
        else:
            report = {"error": f"CRM record with ID '{record_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class DeduplicateCRMRecordsTool(BaseTool):
    """Deduplicates CRM records based on email or ID."""
    def __init__(self, tool_name="deduplicate_crm_records"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deduplicates CRM records in the database based on email or ID, marking duplicate entries as 'inactive'."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        records = crm_db_manager.list_records(status="active")
        
        seen_emails = {} # email: record_id of the first seen record
        duplicates_found = []
        
        for record in records:
            if record["email"] and record["email"] in seen_emails:
                duplicates_found.append({"duplicate_id": record["id"], "original_id": seen_emails[record["email"]]})
                crm_db_manager.update_record(record["id"], {"status": "inactive"})
            else:
                if record["email"]:
                    seen_emails[record["email"]] = record["id"]
        
        if not duplicates_found:
            return json.dumps({"message": "No duplicate CRM records found based on email."})
        
        return json.dumps({"message": f"Deduplication completed. Found {len(duplicates_found)} duplicates.", "duplicates_marked_inactive": duplicates_found}, indent=2)

class StandardizeCRMDataFormatTool(BaseTool):
    """Standardizes various data formats within CRM records."""
    def __init__(self, tool_name="standardize_crm_data_format"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Standardizes various data formats within CRM records (e.g., phone numbers, addresses, names) to ensure consistency."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "Optional: The ID of a specific CRM record to standardize. If not provided, all active records are processed.", "default": None},
                "standardization_rules": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["phone_numbers", "addresses", "names"]},
                    "description": "Specific rules to apply (e.g., 'phone_numbers', 'addresses', 'names').",
                    "default": ["phone_numbers", "addresses", "names"]
                }
            },
            "required": []
        }

    def execute(self, record_id: Optional[str] = None, standardization_rules: List[str] = ["phone_numbers", "addresses", "names"], **kwargs: Any) -> str:
        records_to_process = []
        if record_id:
            record = crm_db_manager.get_record(record_id)
            if record and record["status"] == "active": records_to_process.append(record)
        else:
            records_to_process = crm_db_manager.list_records(status="active")

        if not records_to_process:
            return json.dumps({"message": "No active CRM records found to standardize."})

        standardized_count = 0
        for record in records_to_process:
            updates = {}
            
            if "phone_numbers" in standardization_rules and record.get("phone"):
                phone = str(record["phone"])
                phone = re.sub(r'\D', '', phone) # Remove non-digits
                if len(phone) == 10: # Assume US numbers
                    updates["phone"] = f"+1 ({phone[:3]}) {phone[3:6]}-{phone[6:]}"
                elif len(phone) == 11 and phone.startswith("1"):
                    updates["phone"] = f"+{phone[0]} ({phone[1:4]}) {phone[4:7]}-{phone[7:]}"
                else:
                    updates["phone"] = f"+{phone}" # Generic prefix
            
            if "addresses" in standardization_rules and record.get("address"):
                address = record["address"].upper()
                address = address.replace("STREET", "ST").replace("AVENUE", "AVE").replace("ROAD", "RD").replace("BOULEVARD", "BLVD")
                updates["address"] = address
            
            if "names" in standardization_rules and record.get("name"):
                updates["name"] = record["name"].strip().title()

            if updates:
                crm_db_manager.update_record(record["id"], updates)
                standardized_count += 1
        
        return json.dumps({"message": f"Standardization completed. {standardized_count} records updated.", "standardized_records_count": standardized_count}, indent=2)

class ListCRMRecordsTool(BaseTool):
    """Lists all CRM records, optionally filtered by status."""
    def __init__(self, tool_name="list_crm_records"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all CRM records, optionally filtered by status, showing their ID, name, email, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional: Filter records by status.", "enum": ["active", "inactive"], "default": None}
            },
            "required": []
        }

    def execute(self, status: Optional[str] = None, **kwargs: Any) -> str:
        records = crm_db_manager.list_records(status)
        if not records:
            return json.dumps({"message": "No CRM records found matching the criteria."})
        
        return json.dumps({"total_records": len(records), "crm_records": records}, indent=2)