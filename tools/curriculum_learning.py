import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CURRICULUMS_FILE = Path("curriculums.json")

class CurriculumManager:
    """Manages learning curriculums, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CURRICULUMS_FILE):
        if cls._instance is None:
            cls._instance = super(CurriculumManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.curriculums: Dict[str, Any] = cls._instance._load_curriculums()
        return cls._instance

    def _load_curriculums(self) -> Dict[str, Any]:
        """Loads curriculum information from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty curriculums.")
                return {}
            except Exception as e:
                logger.error(f"Error loading curriculums from {self.file_path}: {e}")
                return {}
        return {}

    def _save_curriculums(self) -> None:
        """Saves curriculum information to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.curriculums, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving curriculums to {self.file_path}: {e}")

    def design_curriculum(self, curriculum_name: str, tasks: List[Dict[str, Any]]) -> Union[bool, Dict[str, Any]]:
        if curriculum_name in self.curriculums:
            return False
        
        # Validate tasks: ensure difficulty is ordered (simple simulation)
        difficulty_order = {"easy": 1, "medium": 2, "hard": 3}
        for i in range(len(tasks) - 1):
            current_task_difficulty = difficulty_order.get(tasks[i]["difficulty"], 0)
            next_task_difficulty = difficulty_order.get(tasks[i+1]["difficulty"], 0)
            if current_task_difficulty > next_task_difficulty:
                return {"error": f"Tasks in curriculum '{curriculum_name}' are not ordered by increasing difficulty. Task '{tasks[i]['task_id']}' (difficulty: {tasks[i]['difficulty']}) is harder than '{tasks[i+1]['task_id']}' (difficulty: {tasks[i+1]['difficulty']})."}

        self.curriculums[curriculum_name] = {
            "tasks": tasks,
            "status": "designed",
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._save_curriculums()
        return True

    def get_curriculum(self, curriculum_name: str) -> Optional[Dict[str, Any]]:
        return self.curriculums.get(curriculum_name)

    def list_curriculums(self) -> List[Dict[str, Any]]:
        return [{"name": name, "status": details['status'], "tasks_count": len(details['tasks']), "created_at": details['created_at']} for name, details in self.curriculums.items()]

curriculum_manager = CurriculumManager()

class LearningModel:
    """Simulates an AI model's learning process."""
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.performance = 0.0 # Initial performance
        self.training_history = []

    def train_on_task(self, task_id: str, difficulty: str) -> float:
        # Simulate performance gain based on difficulty
        performance_gain = 0.0
        if difficulty == "easy":
            performance_gain = random.uniform(0.1, 0.2)  # nosec B311
        elif difficulty == "medium":
            performance_gain = random.uniform(0.05, 0.15)  # nosec B311
        else: # hard
            performance_gain = random.uniform(0.01, 0.05)  # nosec B311
        
        self.performance = min(1.0, self.performance + performance_gain)
        self.training_history.append({"task_id": task_id, "difficulty": difficulty, "performance_after_task": round(self.performance, 2)})
        return self.performance

class DesignCurriculumTool(BaseTool):
    """Designs a learning curriculum for an AI model."""
    def __init__(self, tool_name="design_curriculum"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Designs a new learning curriculum for an AI model, defining a sequence of tasks to be learned, ordered by increasing difficulty."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "curriculum_name": {"type": "string", "description": "A unique name for the curriculum."},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string", "description": "A unique ID for the task."},
                            "difficulty": {"type": "string", "description": "The difficulty level of the task.", "enum": ["easy", "medium", "hard"]}
                        },
                        "required": ["task_id", "difficulty"]
                    },
                    "description": "A list of tasks in the curriculum, each with an ID and difficulty level. Must be ordered by increasing difficulty."
                }
            },
            "required": ["curriculum_name", "tasks"]
        }

    def execute(self, curriculum_name: str, tasks: List[Dict[str, Any]], **kwargs: Any) -> str:
        result = curriculum_manager.design_curriculum(curriculum_name, tasks)
        if isinstance(result, dict) and "error" in result: # Check if validation returned an error dict
            return json.dumps(result)
        if result:
            report = {"message": f"Curriculum '{curriculum_name}' designed successfully with {len(tasks)} tasks."}
        else:
            report = {"error": f"Curriculum '{curriculum_name}' already exists. Please choose a unique name."}
        return json.dumps(report, indent=2)

class TrainWithCurriculumTool(BaseTool):
    """Simulates training an AI model using a designed curriculum."""
    def __init__(self, tool_name="train_with_curriculum"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates training an AI model using a predefined learning curriculum, progressing through tasks of increasing difficulty."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "The ID of the AI model to train."},
                "curriculum_name": {"type": "string", "description": "The name of the curriculum to use for training."}
            },
            "required": ["model_id", "curriculum_name"]
        }

    def execute(self, model_id: str, curriculum_name: str, **kwargs: Any) -> str:
        curriculum = curriculum_manager.get_curriculum(curriculum_name)
        if not curriculum:
            return json.dumps({"error": f"Curriculum '{curriculum_name}' not found. Please design it first."})
        
        model = LearningModel(model_id) # Initialize a new model for this training run
        training_logs = []
        
        for task in curriculum["tasks"]:
            performance = model.train_on_task(task["task_id"], task["difficulty"])
            training_logs.append(f"Trained on task '{task['task_id']}' (difficulty: {task['difficulty']}). Model performance: {performance:.2f}.")
        
        return json.dumps({
            "model_id": model_id,
            "curriculum_name": curriculum_name,
            "final_simulated_performance": round(model.performance, 2),
            "training_logs": training_logs,
            "message": f"Model '{model_id}' successfully trained with curriculum '{curriculum_name}'."
        }, indent=2)

class GetCurriculumDetailsTool(BaseTool):
    """Retrieves the details of a specific learning curriculum."""
    def __init__(self, tool_name="get_curriculum_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the details of a specific learning curriculum, including its tasks and their difficulty levels."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"curriculum_name": {"type": "string", "description": "The name of the curriculum to retrieve details for."}},
            "required": ["curriculum_name"]
        }

    def execute(self, curriculum_name: str, **kwargs: Any) -> str:
        curriculum = curriculum_manager.get_curriculum(curriculum_name)
        if not curriculum:
            return json.dumps({"error": f"Curriculum '{curriculum_name}' not found."})
            
        return json.dumps(curriculum, indent=2)

class ListCurriculumsTool(BaseTool):
    """Lists all designed learning curriculums."""
    def __init__(self, tool_name="list_curriculums"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all designed learning curriculums, showing their name, status, and number of tasks."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        curriculums = curriculum_manager.list_curriculums()
        if not curriculums:
            return json.dumps({"message": "No learning curriculums found."})
        
        return json.dumps({"total_curriculums": len(curriculums), "curriculums": curriculums}, indent=2)