import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalizedLearningPathCreatorTool(BaseTool):
    """
    A tool that creates personalized learning paths for students, suggesting
    modules and tracking progress.
    """

    def __init__(self, tool_name: str = "PersonalizedLearningPathCreator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.paths_file = os.path.join(self.data_dir, "learning_paths.json")
        # Learning paths structure: {learner_name: {subject: {path_id: ..., modules: []}}}
        self.learning_paths: Dict[str, Dict[str, Dict[str, Any]]] = self._load_data(self.paths_file, default={})

    @property
    def description(self) -> str:
        return "Creates personalized learning paths for students, suggesting modules and tracking progress."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_path", "update_progress", "get_path_status"]},
                "learner_name": {"type": "string"},
                "subject": {"type": "string", "enum": ["Math", "Science", "History", "English"]},
                "goals": {"type": "array", "items": {"type": "string"}, "description": "List of learning goals."},
                "module_name": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}
            },
            "required": ["operation", "learner_name"]
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
        with open(self.paths_file, 'w') as f: json.dump(self.learning_paths, f, indent=2)

    def create_path(self, learner_name: str, subject: str, goals: List[str]) -> Dict[str, Any]:
        """Creates a personalized learning path for a learner."""
        if learner_name not in self.learning_paths: self.learning_paths[learner_name] = {}
        if subject in self.learning_paths[learner_name]: raise ValueError(f"Learning path for '{learner_name}' in '{subject}' already exists.")
        
        path_id = f"path_{learner_name}_{subject}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        modules = []
        # Rule-based module generation based on subject and goals
        if subject == "Math":
            modules.append({"name": "Algebra Fundamentals", "status": "pending", "resources": ["textbook", "practice problems"]})
            if "calculus" in [g.lower() for g in goals]:
                modules.append({"name": "Introduction to Calculus", "status": "pending", "resources": ["video lectures"]})
        elif subject == "Science":
            modules.append({"name": "Biology Basics", "status": "pending", "resources": ["online course"]})
            if "chemistry" in [g.lower() for g in goals]:
                modules.append({"name": "Chemical Reactions", "status": "pending", "resources": ["lab simulations"]})
        
        new_path = {
            "path_id": path_id, "learner_name": learner_name, "subject": subject, "goals": goals,
            "modules": modules, "created_at": datetime.now().isoformat()
        }
        self.learning_paths[learner_name][subject] = new_path
        self._save_data()
        return new_path

    def update_progress(self, learner_name: str, subject: str, module_name: str, status: str) -> Dict[str, Any]:
        """Updates the progress of a module in a learning path."""
        if learner_name not in self.learning_paths or subject not in self.learning_paths[learner_name]:
            raise ValueError(f"Learning path for '{learner_name}' in '{subject}' not found.")
        
        path = self.learning_paths[learner_name][subject]
        module_found = False
        for module in path["modules"]:
            if module["name"] == module_name:
                module["status"] = status
                module_found = True
                break
        
        if not module_found: raise ValueError(f"Module '{module_name}' not found in path for '{learner_name}' in '{subject}'.")
        
        self._save_data()
        return {"status": "success", "message": f"Progress for module '{module_name}' updated to '{status}'."}

    def get_path_status(self, learner_name: str, subject: str) -> Dict[str, Any]:
        """Retrieves the status of a learning path."""
        if learner_name not in self.learning_paths or subject not in self.learning_paths[learner_name]:
            raise ValueError(f"Learning path for '{learner_name}' in '{subject}' not found.")
        
        path = self.learning_paths[learner_name][subject]
        total_modules = len(path["modules"])
        completed_modules = sum(1 for module in path["modules"] if module["status"] == "completed")
        
        completion_percentage = round((completed_modules / total_modules) * 100, 2) if total_modules > 0 else 0
        
        return {
            "learner_name": learner_name, "subject": subject,
            "completion_percentage": completion_percentage,
            "modules": path["modules"]
        }

    def execute(self, operation: str, learner_name: str, **kwargs: Any) -> Any:
        if operation == "create_path":
            subject = kwargs.get('subject')
            goals = kwargs.get('goals')
            if not all([subject, goals]):
                raise ValueError("Missing 'subject' or 'goals' for 'create_path' operation.")
            return self.create_path(learner_name, subject, goals)
        elif operation == "update_progress":
            subject = kwargs.get('subject')
            module_name = kwargs.get('module_name')
            status = kwargs.get('status')
            if not all([subject, module_name, status]):
                raise ValueError("Missing 'subject', 'module_name', or 'status' for 'update_progress' operation.")
            return self.update_progress(learner_name, subject, module_name, status)
        elif operation == "get_path_status":
            subject = kwargs.get('subject')
            if not subject:
                raise ValueError("Missing 'subject' for 'get_path_status' operation.")
            return self.get_path_status(learner_name, subject)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PersonalizedLearningPathCreatorTool functionality...")
    temp_dir = "temp_learning_path_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    path_creator = PersonalizedLearningPathCreatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a learning path for Alice in Math
        print("\n--- Creating learning path for 'Alice' in 'Math' ---")
        path_creator.execute(operation="create_path", learner_name="Alice", subject="Math", goals=["master algebra", "understand calculus"])
        print("Path created for Alice in Math.")

        # 2. Update progress for a module
        print("\n--- Updating progress for 'Algebra Fundamentals' to 'completed' ---")
        path_creator.execute(operation="update_progress", learner_name="Alice", subject="Math", module_name="Algebra Fundamentals", status="completed")
        print("Progress updated.")

        # 3. Get path status
        print("\n--- Getting path status for 'Alice' in 'Math' ---")
        path_status = path_creator.execute(operation="get_path_status", learner_name="Alice", subject="Math")
        print(json.dumps(path_status, indent=2))

        # 4. Create a learning path for Bob in Science
        print("\n--- Creating learning path for 'Bob' in 'Science' ---")
        path_creator.execute(operation="create_path", learner_name="Bob", subject="Science", goals=["learn biology", "explore chemistry"])
        print("Path created for Bob in Science.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")