import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CONTINUAL_LEARNING_MODELS_FILE = Path("continual_learning_models.json")

class ContinualLearningManager:
    """Manages continual learning models, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CONTINUAL_LEARNING_MODELS_FILE):
        if cls._instance is None:
            cls._instance = super(ContinualLearningManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.models: Dict[str, Any] = cls._instance._load_models()
        return cls._instance

    def _load_models(self) -> Dict[str, Any]:
        """Loads model information from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty models.")
                return {}
            except Exception as e:
                logger.error(f"Error loading models from {self.file_path}: {e}")
                return {}
        return {}

    def _save_models(self) -> None:
        """Saves model information to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.models, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving models to {self.file_path}: {e}")

    def initialize_model(self, model_id: str, initial_tasks: List[str]) -> bool:
        if model_id in self.models:
            return False
        
        initial_performance = {task: round(random.uniform(0.6, 0.8), 2) for task in initial_tasks}  # nosec B311
        self.models[model_id] = {
            "status": "initialized",
            "initial_performance": initial_performance, # Performance when first learned
            "current_performance": initial_performance.copy(), # Performance after subsequent training
            "training_history": [],
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._save_models()
        return True

    def train_incrementally(self, model_id: str, new_data_summary: Dict[str, Any]) -> Dict[str, Any]:
        if model_id not in self.models:
            return {"error": f"Model '{model_id}' not found."}
        
        model = self.models[model_id]
        task_id = new_data_summary.get("task_id", "new_task_" + str(random.randint(1, 100)))  # nosec B311
        improvement_factor = new_data_summary.get("improvement_factor", random.uniform(0.01, 0.1))  # nosec B311

        # Improve performance on the new task
        if task_id not in model["current_performance"]:
            model["current_performance"][task_id] = 0.5 # New task starts with baseline
            model["initial_performance"][task_id] = 0.5 # Record initial for new task
        
        model["current_performance"][task_id] = min(1.0, model["current_performance"][task_id] + improvement_factor)

        # Simulate slight forgetting on other tasks
        for old_task in model["current_performance"]:
            if old_task != task_id:
                forgetting_factor = random.uniform(0.001, 0.005)  # nosec B311
                model["current_performance"][old_task] = max(0.0, model["current_performance"][old_task] - forgetting_factor)

        model["training_history"].append({
            "timestamp": datetime.now().isoformat() + "Z",
            "action": "incremental_train",
            "new_data_summary": new_data_summary,
            "updated_performance": model["current_performance"]
        })
        model["status"] = "trained_incrementally"
        self._save_models()
        return model["current_performance"]

    def get_model_performance(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self.models.get(model_id)

continual_learning_manager = ContinualLearningManager()

class InitializeContinualLearningModelTool(BaseTool):
    """Initializes a new continual learning model."""
    def __init__(self, tool_name="initialize_cl_model"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Initializes a new continual learning model with a unique ID and a list of initial tasks it can perform."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "A unique ID for the new continual learning model."},
                "initial_tasks": {"type": "array", "items": {"type": "string"}, "description": "A list of initial tasks the model is trained on.", "default": ["task_A", "task_B"]}
            },
            "required": ["model_id"]
        }

    def execute(self, model_id: str, initial_tasks: List[str] = None, **kwargs: Any) -> str:
        if initial_tasks is None: initial_tasks = ["task_A", "task_B"]
        success = continual_learning_manager.initialize_model(model_id, initial_tasks)
        if success:
            report = {"message": f"Continual learning model '{model_id}' initialized successfully with initial tasks: {initial_tasks}."}
        else:
            report = {"error": f"Model '{model_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class TrainIncrementallyTool(BaseTool):
    """Simulates training a model incrementally on new data without forgetting old knowledge."""
    def __init__(self, tool_name="train_incrementally"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates incrementally training an AI model on new data, aiming to incorporate new knowledge without significantly forgetting previously learned information."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "The ID of the model to train incrementally."},
                "new_data_summary": {
                    "type": "object",
                    "description": "A dictionary representing the new data for incremental training (e.g., {'samples': 100, 'task_id': 'new_task_A', 'improvement_factor': 0.05})."
                }
            },
            "required": ["model_id", "new_data_summary"]
        }

    def execute(self, model_id: str, new_data_summary: Dict[str, Any], **kwargs: Any) -> str:
        current_performance = continual_learning_manager.train_incrementally(model_id, new_data_summary)
        if "error" in current_performance:
            return json.dumps(current_performance)
        
        report = {
            "model_id": model_id,
            "status": "success",
            "message": f"Model '{model_id}' trained incrementally on new data for task '{new_data_summary.get('task_id', 'unknown_task')}'." if new_data_summary.get('task_id') else f"Model '{model_id}' trained incrementally on new data.",
            "current_performance": current_performance
        }
        return json.dumps(report, indent=2)

class EvaluateForgettingTool(BaseTool):
    """Evaluates a model for catastrophic forgetting on old tasks."""
    def __init__(self, tool_name="evaluate_forgetting"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Evaluates an AI model to quantify how much it has forgotten previously learned tasks after incremental training."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "The ID of the model to evaluate for forgetting."},
                "old_task_id": {"type": "string", "description": "The ID of the old task to evaluate forgetting for."}
            },
            "required": ["model_id", "old_task_id"]
        }

    def execute(self, model_id: str, old_task_id: str, **kwargs: Any) -> str:
        model_data = continual_learning_manager.get_model_performance(model_id)
        if not model_data:
            return json.dumps({"error": f"Model '{model_id}' not found."})
        
        initial_performance = model_data["initial_performance"].get(old_task_id, 0.0)
        current_performance = model_data["current_performance"].get(old_task_id, 0.0)

        forgetting_score = max(0.0, initial_performance - current_performance)
        
        forgetting_severity = "Low"
        if forgetting_score > 0.2: forgetting_severity = "High"
        elif forgetting_score > 0.1: forgetting_severity = "Medium"

        return json.dumps({
            "model_id": model_id,
            "old_task_id": old_task_id,
            "initial_performance_on_task": initial_performance,
            "current_performance_on_task": current_performance,
            "forgetting_score": round(forgetting_score, 2),
            "forgetting_severity": forgetting_severity,
            "message": f"Evaluation for model '{model_id}' on task '{old_task_id}' completed."
        }, indent=2)

class GetModelPerformanceTool(BaseTool):
    """Retrieves the current performance of a continual learning model on all tasks."""
    def __init__(self, tool_name="get_model_performance"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current performance of a continual learning model on all tasks it has been trained on."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"model_id": {"type": "string", "description": "The ID of the continual learning model."}},
            "required": ["model_id"]
        }

    def execute(self, model_id: str, **kwargs: Any) -> str:
        model_data = continual_learning_manager.get_model_performance(model_id)
        if not model_data:
            return json.dumps({"error": f"Model '{model_id}' not found."})
            
        return json.dumps({
            "model_id": model_id,
            "status": model_data["status"],
            "current_performance": model_data["current_performance"],
            "initial_performance": model_data["initial_performance"]
        }, indent=2)