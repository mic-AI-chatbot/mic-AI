

import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class StoryboardGeneratorTool(BaseTool):
    """
    A tool for generating detailed storyboards with customizable scenes and
    visual descriptions, and managing them with persistence.
    """

    def __init__(self, tool_name: str = "StoryboardGenerator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.storyboards_file = os.path.join(self.data_dir, "storyboards.json")
        # Storyboards structure: {storyboard_id: {topic: ..., scenes: []}}
        self.storyboards: Dict[str, Dict[str, Any]] = self._load_data(self.storyboards_file, default={})

    @property
    def description(self) -> str:
        return "Generates storyboards with customizable scenes and visual descriptions, and manages them with persistence."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_storyboard", "add_visual_description", "get_storyboard_content"]},
                "storyboard_id": {"type": "string"},
                "topic": {"type": "string"},
                "scenes": {"type": "array", "items": {"type": "string"}, "description": "List of scene descriptions."},
                "scene_number": {"type": "integer", "minimum": 1},
                "visual_description": {"type": "string"}
            },
            "required": ["operation", "storyboard_id"]
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
        with open(self.storyboards_file, 'w') as f: json.dump(self.storyboards, f, indent=2)

    def create_storyboard(self, storyboard_id: str, topic: str, scenes: List[str]) -> Dict[str, Any]:
        """Generates a storyboard with a given topic and a list of scenes."""
        if storyboard_id in self.storyboards: raise ValueError(f"Storyboard '{storyboard_id}' already exists.")
        if not scenes: raise ValueError("'scenes' must be a non-empty list of strings.")
        
        new_storyboard = {
            "id": storyboard_id, "topic": topic,
            "scenes": [{"description": scene, "visuals": None} for scene in scenes],
            "created_at": datetime.now().isoformat()
        }
        self.storyboards[storyboard_id] = new_storyboard
        self._save_data()
        return new_storyboard

    def add_visual_description(self, storyboard_id: str, scene_number: int, visual_description: str) -> Dict[str, Any]:
        """Adds a visual description to a specific scene of the storyboard."""
        storyboard = self.storyboards.get(storyboard_id)
        if not storyboard: raise ValueError(f"Storyboard '{storyboard_id}' not found. Create one first.")
        if not (1 <= scene_number <= len(storyboard["scenes"])):
            raise ValueError(f"Invalid scene number. Storyboard has {len(storyboard['scenes'])} scenes.")
        
        storyboard["scenes"][scene_number - 1]["visuals"] = visual_description
        self._save_data()
        return {"status": "success", "message": f"Visual description added to Scene {scene_number} of storyboard '{storyboard_id}'."}

    def get_storyboard_content(self, storyboard_id: str) -> Dict[str, Any]:
        """Returns the full content of the storyboard, including scene descriptions and visual details."""
        storyboard = self.storyboards.get(storyboard_id)
        if not storyboard: raise ValueError(f"Storyboard '{storyboard_id}' not found.")
        
        full_content = f"--- Storyboard: {storyboard['topic']} ---\n\n"
        for i, scene_data in enumerate(storyboard["scenes"]):
            full_content += f"Scene {i+1}: {scene_data['description']}\n"
            if scene_data['visuals']:
                full_content += f"  Visuals: {scene_data['visuals']}\n"
            full_content += "\n"
        full_content += "--- End of Storyboard ---"
        
        return {"status": "success", "storyboard_id": storyboard_id, "content": full_content}

    def execute(self, operation: str, storyboard_id: str, **kwargs: Any) -> Any:
        if operation == "create_storyboard":
            topic = kwargs.get('topic')
            scenes = kwargs.get('scenes')
            if not all([topic, scenes]):
                raise ValueError("Missing 'topic' or 'scenes' for 'create_storyboard' operation.")
            return self.create_storyboard(storyboard_id, topic, scenes)
        elif operation == "add_visual_description":
            scene_number = kwargs.get('scene_number')
            visual_description = kwargs.get('visual_description')
            if not all([scene_number, visual_description]):
                raise ValueError("Missing 'scene_number' or 'visual_description' for 'add_visual_description' operation.")
            return self.add_visual_description(storyboard_id, scene_number, visual_description)
        elif operation == "get_storyboard_content":
            # No additional kwargs required for get_storyboard_content
            return self.get_storyboard_content(storyboard_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating StoryboardGeneratorTool functionality...")
    temp_dir = "temp_storyboard_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    storyboard_tool = StoryboardGeneratorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a storyboard
        print("\n--- Creating storyboard 'Project_Alpha_Promo' ---")
        scenes = [
            "Opening shot: A bustling city at dawn.",
            "Scene 2: A lone developer coding intensely.",
            "Scene 3: The team collaborating seamlessly.",
            "Scene 4: Product launch with cheering crowd."
        ]
        storyboard_tool.execute(operation="create_storyboard", storyboard_id="Project_Alpha_Promo", topic="Project Alpha Promotion", scenes=scenes)
        print("Storyboard created.")

        # 2. Add visual description to a scene
        print("\n--- Adding visual description to Scene 2 ---")
        storyboard_tool.execute(operation="add_visual_description", storyboard_id="Project_Alpha_Promo", scene_number=2, visual_description="Close-up on developer's face, screen glowing with code, coffee cup nearby.")
        print("Visual description added.")

        # 3. Get storyboard content
        print("\n--- Getting storyboard content for 'Project_Alpha_Promo' ---")
        content = storyboard_tool.execute(operation="get_storyboard_content", storyboard_id="Project_Alpha_Promo")
        print(json.dumps(content, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
