import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalizedLearningCurriculumGeneratorTool(BaseTool):
    """
    A tool for generating personalized learning curricula, suggesting resources,
    and tracking progress based on learning styles and desired depth.
    """

    def __init__(self, tool_name: str = "PersonalizedLearningCurriculumGenerator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.curricula_file = os.path.join(self.data_dir, "learning_curricula.json")
        # Curricula structure: {curriculum_id: {topic: ..., learning_style: ..., desired_depth: ..., items: []}}
        self.curricula: Dict[str, Dict[str, Any]] = self._load_data(self.curricula_file, default={})
        self.available_learning_styles = ["visual", "auditory", "reading/writing", "kinesthetic"]
        self.available_resources = {
            "visual": ["video lectures", "infographics", "diagrams"],
            "auditory": ["podcasts", "audiobooks", "lectures"],
            "reading/writing": ["textbooks", "articles", "research papers", "writing exercises"],
            "kinesthetic": ["hands-on projects", "simulations", "experiments"]
        }

    @property
    def description(self) -> str:
        return "Generates personalized learning curricula, suggests resources, and tracks progress."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_curriculum", "suggest_resources", "track_progress"]},
                "curriculum_id": {"type": "string"},
                "topic": {"type": "string"},
                "learning_style": {"type": "string", "enum": ["visual", "auditory", "reading/writing", "kinesthetic"]},
                "desired_depth": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                "item_title": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]}
            },
            "required": ["operation", "curriculum_id"]
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
        with open(self.curricula_file, 'w') as f: json.dump(self.curricula, f, indent=2)

    def generate_curriculum(self, curriculum_id: str, topic: str, learning_style: str, desired_depth: str = "intermediate") -> Dict[str, Any]:
        """Generates a personalized learning curriculum."""
        if curriculum_id in self.curricula: raise ValueError(f"Curriculum '{curriculum_id}' already exists.")
        if learning_style not in self.available_learning_styles: raise ValueError(f"Unsupported learning style: {learning_style}.")
        if desired_depth not in ["beginner", "intermediate", "advanced"]: raise ValueError("Desired depth must be 'beginner', 'intermediate', or 'advanced'.")

        curriculum_items = []
        if desired_depth == "beginner":
            curriculum_items.append({"title": f"Introduction to {topic}", "status": "pending"})
            curriculum_items.append({"title": f"Basic Concepts of {topic}", "status": "pending"})
        elif desired_depth == "intermediate":
            curriculum_items.append({"title": f"Advanced Concepts in {topic}", "status": "pending"})
            curriculum_items.append({"title": f"Practical Applications of {topic}", "status": "pending"})
        elif desired_depth == "advanced":
            curriculum_items.append({"title": f"Research Frontiers in {topic}", "status": "pending"})
            curriculum_items.append({"title": f"Case Studies in {topic}", "status": "pending"})
        
        new_curriculum = {
            "id": curriculum_id, "topic": topic, "learning_style": learning_style,
            "desired_depth": desired_depth, "items": curriculum_items,
            "generated_at": datetime.now().isoformat()
        }
        self.curricula[curriculum_id] = new_curriculum
        self._save_data()
        return new_curriculum

    def suggest_resources(self, curriculum_id: str, item_title: str) -> Dict[str, Any]:
        """Suggests learning resources for a specific curriculum item based on learning style."""
        curriculum = self.curricula.get(curriculum_id)
        if not curriculum: raise ValueError(f"Curriculum '{curriculum_id}' not found. Generate it first.")
        
        item_found = False
        for item in curriculum["items"]:
            if item["title"] == item_title:
                item_found = True
                break
        
        if not item_found: raise ValueError(f"Curriculum item '{item_title}' not found in curriculum '{curriculum_id}'.")
        
        style = curriculum["learning_style"]
        resources = self.available_resources.get(style, [])
        
        if not resources:
            return {"status": "info", "message": f"No specific resources found for '{item_title}' with '{style}' learning style."}
        
        return {"status": "success", "item_title": item_title, "suggested_resources": resources}

    def track_progress(self, curriculum_id: str, item_title: str, status: str) -> Dict[str, Any]:
        """Tracks a learner's progress through the curriculum."""
        curriculum = self.curricula.get(curriculum_id)
        if not curriculum: raise ValueError(f"Curriculum '{curriculum_id}' not found. Generate it first.")
        
        item_updated = False
        for item in curriculum["items"]:
            if item["title"] == item_title:
                item["status"] = status
                item_updated = True
                break
        
        if not item_updated: raise ValueError(f"Curriculum item '{item_title}' not found in curriculum '{curriculum_id}'.")
        
        self._save_data()
        return {"status": "success", "message": f"Progress for '{item_title}' in curriculum '{curriculum_id}' updated to '{status}'."}

    def execute(self, operation: str, curriculum_id: str, **kwargs: Any) -> Any:
        if operation == "generate_curriculum":
            topic = kwargs.get('topic')
            learning_style = kwargs.get('learning_style')
            if not all([topic, learning_style]):
                raise ValueError("Missing 'topic' or 'learning_style' for 'generate_curriculum' operation.")
            return self.generate_curriculum(curriculum_id, topic, learning_style, kwargs.get('desired_depth', 'intermediate'))
        elif operation == "suggest_resources":
            item_title = kwargs.get('item_title')
            if not item_title:
                raise ValueError("Missing 'item_title' for 'suggest_resources' operation.")
            return self.suggest_resources(curriculum_id, item_title)
        elif operation == "track_progress":
            item_title = kwargs.get('item_title')
            status = kwargs.get('status')
            if not all([item_title, status]):
                raise ValueError("Missing 'item_title' or 'status' for 'track_progress' operation.")
            return self.track_progress(curriculum_id, item_title, status)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PersonalizedLearningCurriculumGeneratorTool functionality...")
    temp_dir = "temp_curriculum_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    curriculum_tool = PersonalizedLearningCurriculumGeneratorTool(data_dir=temp_dir)
    
    try:
        # 1. Generate a curriculum
        print("\n--- Generating curriculum 'math_beginner_visual' ---")
        curriculum_tool.execute(operation="generate_curriculum", curriculum_id="math_beginner_visual", topic="Math", learning_style="visual", desired_depth="beginner")
        print("Curriculum generated.")

        # 2. Suggest resources for an item
        print("\n--- Suggesting resources for 'Introduction to Math' ---")
        resources = curriculum_tool.execute(operation="suggest_resources", curriculum_id="math_beginner_visual", item_title="Introduction to Math")
        print(json.dumps(resources, indent=2))

        # 3. Track progress
        print("\n--- Tracking progress for 'Introduction to Math' to 'completed' ---")
        progress_update = curriculum_tool.execute(operation="track_progress", curriculum_id="math_beginner_visual", item_title="Introduction to Math", status="completed")
        print(json.dumps(progress_update, indent=2))

        # 4. Generate another curriculum
        print("\n--- Generating curriculum 'science_advanced_kinesthetic' ---")
        curriculum_tool.execute(operation="generate_curriculum", curriculum_id="science_advanced_kinesthetic", topic="Science", learning_style="kinesthetic", desired_depth="advanced")
        print("Curriculum generated.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")