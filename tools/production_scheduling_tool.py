import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ProductionSchedulingSimulatorTool(BaseTool):
    """
    A tool that simulates production scheduling, allowing for creating schedules,
    optimizing production, and tracking progress.
    """

    def __init__(self, tool_name: str = "ProductionSchedulingSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.schedules_file = os.path.join(self.data_dir, "production_schedules.json")
        # Schedules structure: {schedule_id: {product_id: ..., quantity: ..., status: ..., progress_percent: ...}}
        self.production_schedules: Dict[str, Dict[str, Any]] = self._load_data(self.schedules_file, default={})

    @property
    def description(self) -> str:
        return "Simulates production scheduling: create, optimize, and track progress of production schedules."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_schedule", "optimize_production", "track_progress", "get_schedule_details", "list_schedules"]},
                "schedule_id": {"type": "string"},
                "product_id": {"type": "string"},
                "quantity": {"type": "integer", "minimum": 1},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "due_date": {"type": "string", "description": "YYYY-MM-DD"},
                "progress_percent": {"type": "number", "minimum": 0, "maximum": 100},
                "filter_status": {"type": "string", "enum": ["planned", "in_progress", "completed", "delayed"]}
            },
            "required": ["operation", "schedule_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.schedules_file, 'w') as f: json.dump(self.production_schedules, f, indent=2)

    def create_schedule(self, schedule_id: str, product_id: str, quantity: int, start_date: str, due_date: str) -> Dict[str, Any]:
        """Creates a new production schedule."""
        if schedule_id in self.production_schedules: raise ValueError(f"Schedule '{schedule_id}' already exists.")
        
        new_schedule = {
            "id": schedule_id, "product_id": product_id, "quantity": quantity,
            "start_date": start_date, "due_date": due_date, "status": "planned",
            "progress_percent": 0, "created_at": datetime.now().isoformat()
        }
        self.production_schedules[schedule_id] = new_schedule
        self._save_data()
        return new_schedule

    def optimize_production(self, schedule_id: str) -> Dict[str, Any]:
        """Simulates optimizing the production process for a schedule."""
        schedule = self.production_schedules.get(schedule_id)
        if not schedule: raise ValueError(f"Schedule '{schedule_id}' not found.")
        
        original_duration_days = (datetime.fromisoformat(schedule["due_date"]) - datetime.fromisoformat(schedule["start_date"])).days
        optimized_duration_days = max(1, round(original_duration_days * random.uniform(0.8, 0.95))) # 5-20% reduction  # nosec B311
        cost_reduction_percent = round(random.uniform(5.0, 15.0), 2)  # nosec B311
        
        schedule["optimized_duration_days"] = optimized_duration_days
        schedule["cost_reduction_percent"] = cost_reduction_percent
        schedule["last_optimized_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Schedule '{schedule_id}' optimized.", "optimized_duration_days": optimized_duration_days, "cost_reduction_percent": cost_reduction_percent}

    def track_progress(self, schedule_id: str, progress_percent: float) -> Dict[str, Any]:
        """Tracks the progress of a production schedule."""
        schedule = self.production_schedules.get(schedule_id)
        if not schedule: raise ValueError(f"Schedule '{schedule_id}' not found.")
        
        schedule["progress_percent"] = max(0, min(100, progress_percent))
        if progress_percent >= 100: schedule["status"] = "completed"
        elif progress_percent > 0: schedule["status"] = "in_progress"
        schedule["last_updated_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Schedule '{schedule_id}' progress updated to {progress_percent}%."}

    def get_schedule_details(self, schedule_id: str) -> Dict[str, Any]:
        """Retrieves the full details of a production schedule."""
        schedule = self.production_schedules.get(schedule_id)
        if not schedule: raise ValueError(f"Schedule '{schedule_id}' not found.")
        return schedule

    def list_schedules(self, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all production schedules, optionally filtered by status."""
        filtered_list = list(self.production_schedules.values())
        if filter_status:
            filtered_list = [s for s in filtered_list if s["status"] == filter_status]
        return filtered_list

    def execute(self, operation: str, schedule_id: str, **kwargs: Any) -> Any:
        if operation == "create_schedule":
            product_id = kwargs.get('product_id')
            quantity = kwargs.get('quantity')
            start_date = kwargs.get('start_date')
            due_date = kwargs.get('due_date')
            if not all([product_id, quantity, start_date, due_date]):
                raise ValueError("Missing 'product_id', 'quantity', 'start_date', or 'due_date' for 'create_schedule' operation.")
            return self.create_schedule(schedule_id, product_id, quantity, start_date, due_date)
        elif operation == "optimize_production":
            # No additional kwargs required for optimize_production
            return self.optimize_production(schedule_id)
        elif operation == "track_progress":
            progress_percent = kwargs.get('progress_percent')
            if progress_percent is None: # Check for None specifically as 0 is a valid float
                raise ValueError("Missing 'progress_percent' for 'track_progress' operation.")
            return self.track_progress(schedule_id, progress_percent)
        elif operation == "get_schedule_details":
            # No additional kwargs required for get_schedule_details
            return self.get_schedule_details(schedule_id)
        elif operation == "list_schedules":
            # filter_status is optional, so no strict check needed here
            return self.list_schedules(kwargs.get('filter_status'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ProductionSchedulingSimulatorTool functionality...")
    temp_dir = "temp_prod_schedule_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    scheduler_tool = ProductionSchedulingSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a new production schedule
        print("\n--- Creating schedule 'SCH-001' for 'Widget X' ---")
        scheduler_tool.execute(operation="create_schedule", schedule_id="SCH-001", product_id="Widget X", quantity=1000, start_date="2025-11-01", due_date="2025-11-30")
        print("Schedule created.")

        # 2. Optimize production
        print("\n--- Optimizing production for 'SCH-001' ---")
        optimization_result = scheduler_tool.execute(operation="optimize_production", schedule_id="SCH-001")
        print(json.dumps(optimization_result, indent=2))

        # 3. Track progress
        print("\n--- Tracking progress for 'SCH-001' to 50% ---")
        scheduler_tool.execute(operation="track_progress", schedule_id="SCH-001", progress_percent=50)
        print("Progress updated.")

        # 4. Get schedule details
        print("\n--- Getting details for 'SCH-001' ---")
        details = scheduler_tool.execute(operation="get_schedule_details", schedule_id="SCH-001")
        print(json.dumps(details, indent=2))

        # 5. List all schedules
        print("\n--- Listing all schedules ---")
        all_schedules = scheduler_tool.execute(operation="list_schedules", schedule_id="any") # schedule_id is not used for list_schedules
        print(json.dumps(all_schedules, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")