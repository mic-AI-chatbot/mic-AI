import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import DataWarehouse, WarehouseData
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class CreateDataWarehouseTool(BaseTool):
    """Creates a new cloud data warehouse in the persistent database."""
    def __init__(self, tool_name="create_data_warehouse"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new cloud data warehouse on a specified platform with initial storage and compute resources."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warehouse_name": {"type": "string", "description": "A unique name for the new data warehouse."},
                "platform": {"type": "string", "description": "The cloud data warehouse platform.", "enum": ["snowflake", "bigquery", "redshift"], "default": "snowflake"},
                "storage_gb": {"type": "integer", "description": "Initial storage capacity in GB.", "default": 1024},
                "compute_units": {"type": "integer", "description": "Initial compute units allocated.", "default": 10}
            },
            "required": ["warehouse_name"]
        }

    def execute(self, warehouse_name: str, platform: str = "snowflake", storage_gb: int = 1024, compute_units: int = 10, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            now = datetime.now().isoformat() + "Z"
            new_warehouse = DataWarehouse(
                warehouse_name=warehouse_name,
                platform=platform,
                status="active",
                storage_gb=storage_gb,
                compute_units=compute_units,
                created_at=now
            )
            db.add(new_warehouse)
            db.commit()
            db.refresh(new_warehouse)
            report = {"message": f"Cloud data warehouse '{warehouse_name}' created successfully on '{platform}'."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Data warehouse '{warehouse_name}' already exists. Please choose a unique name."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating data warehouse: {e}")
            report = {"error": f"Failed to create data warehouse: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class DeleteDataWarehouseTool(BaseTool):
    """Deletes an existing cloud data warehouse from the persistent database."""
    def __init__(self, tool_name="delete_data_warehouse"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deletes an existing cloud data warehouse, removing all its associated data and metadata."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"warehouse_name": {"type": "string", "description": "The name of the data warehouse to delete."}},
            "required": ["warehouse_name"]
        }

    def execute(self, warehouse_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            warehouse = db.query(DataWarehouse).filter(DataWarehouse.warehouse_name == warehouse_name).first()
            if warehouse:
                # Delete associated data first
                db.query(WarehouseData).filter(WarehouseData.warehouse_name == warehouse_name).delete()
                db.delete(warehouse)
                db.commit()
                report = {"message": f"Cloud data warehouse '{warehouse_name}' deleted successfully."}
            else:
                report = {"error": f"Data warehouse '{warehouse_name}' not found."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting data warehouse: {e}")
            report = {"error": f"Failed to delete data warehouse: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class LoadDataIntoWarehouseTool(BaseTool):
    """Simulates loading data into a data warehouse."""
    def __init__(self, tool_name="load_data_into_warehouse"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates loading data into a specified table within a data warehouse, recording the row count."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warehouse_name": {"type": "string", "description": "The name of the data warehouse."},
                "table_name": {"type": "string", "description": "The name of the table to load data into."},
                "row_count": {"type": "integer", "description": "The number of rows to simulate loading.", "default": 10000}
            },
            "required": ["warehouse_name", "table_name"]
        }

    def execute(self, warehouse_name: str, table_name: str, row_count: int = 10000, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            warehouse = db.query(DataWarehouse).filter(DataWarehouse.warehouse_name == warehouse_name).first()
            if not warehouse:
                return json.dumps({"error": f"Data warehouse '{warehouse_name}' not found. Please create it first."})
            
            now = datetime.now().isoformat() + "Z"
            new_warehouse_data = WarehouseData(
                warehouse_name=warehouse_name,
                table_name=table_name,
                row_count=row_count,
                loaded_at=now
            )
            db.add(new_warehouse_data)
            db.commit()
            db.refresh(new_warehouse_data)
            report = {"message": f"Simulated loading of {row_count} rows into table '{table_name}' in warehouse '{warehouse_name}'. Data ID: {new_warehouse_data.id}."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error loading data into warehouse: {e}")
            report = {"error": f"Failed to load data into warehouse: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class QueryDataWarehouseTool(BaseTool):
    """Simulates querying data from a data warehouse."""
    def __init__(self, tool_name="query_data_warehouse"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates querying data from a specified data warehouse using a given SQL query, returning mock results."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "warehouse_name": {"type": "string", "description": "The name of the data warehouse."},
                "sql_query": {"type": "string", "description": "The SQL query to simulate (e.g., 'SELECT COUNT(*) FROM sales_data')."}
            },
            "required": ["warehouse_name", "sql_query"]
        }

    def execute(self, warehouse_name: str, sql_query: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            warehouse = db.query(DataWarehouse).filter(DataWarehouse.warehouse_name == warehouse_name).first()
            if not warehouse:
                return json.dumps({"error": f"Data warehouse '{warehouse_name}' not found. Please create it first."})
            
            # Simulate query execution and results
            mock_results = {
                "query": sql_query,
                "rows_returned": random.randint(10, 1000),  # nosec B311
                "execution_time_ms": random.randint(500, 5000),  # nosec B311
                "sample_data": [{"col1": "value1", "col2": "value2"}] # Generic sample
            }
            report = {"message": f"Simulated query executed on '{warehouse_name}'.", "query_results": mock_results}
        except Exception as e:
            logger.error(f"Error querying data warehouse: {e}")
            report = {"error": f"Failed to query data warehouse: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetDataWarehouseDetailsTool(BaseTool):
    """Retrieves details of a specific data warehouse."""
    def __init__(self, tool_name="get_data_warehouse_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves details of a specific data warehouse, including its platform, status, storage, compute, and loaded data summary."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"warehouse_name": {"type": "string", "description": "The name of the data warehouse to retrieve details for."}},
            "required": ["warehouse_name"]
        }

    def execute(self, warehouse_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            warehouse = db.query(DataWarehouse).options(joinedload(DataWarehouse.warehouse_data)).filter(DataWarehouse.warehouse_name == warehouse_name).first()
            if not warehouse:
                return json.dumps({"error": f"Data warehouse '{warehouse_name}' not found."})
            
            data_summary_list = [{
                "id": wd.id,
                "table_name": wd.table_name,
                "row_count": wd.row_count,
                "loaded_at": wd.loaded_at
            } for wd in warehouse.warehouse_data]
            
            report = {
                "warehouse_details": {
                    "warehouse_name": warehouse.warehouse_name,
                    "platform": warehouse.platform,
                    "status": warehouse.status,
                    "storage_gb": warehouse.storage_gb,
                    "compute_units": warehouse.compute_units,
                    "created_at": warehouse.created_at
                },
                "loaded_data_summary": data_summary_list
            }
        except Exception as e:
            logger.error(f"Error getting data warehouse details: {e}")
            report = {"error": f"Failed to get data warehouse details: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
