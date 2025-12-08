
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PresentationContentGeneratorTool(BaseTool):
    """
    A tool that generates structured presentation content (slides data)
    based on a topic, target audience, and desired number of slides.
    """

    def __init__(self, tool_name: str = "PresentationContentGenerator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.presentations_file = os.path.join(self.data_dir, "generated_presentations.json")
        # Presentations structure: {presentation_id: {topic: ..., audience: ..., slides_data: []}}
        self.generated_presentations: Dict[str, Dict[str, Any]] = self._load_data(self.presentations_file, default={})

    @property
    def description(self) -> str:
        return "Generates structured presentation content (slides data) based on topic, audience, and number of slides."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_slides_content", "get_generated_content"]},
                "presentation_id": {"type": "string"},
                "topic": {"type": "string"},
                "audience": {"type": "string", "enum": ["general", "technical", "executive"], "default": "general"},
                "num_slides": {"type": "integer", "minimum": 5, "maximum": 20, "default": 10}
            },
            "required": ["operation", "presentation_id"]
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
        with open(self.presentations_file, 'w') as f: json.dump(self.generated_presentations, f, indent=2)

    def generate_slides_content(self, presentation_id: str, topic: str, audience: str = "general", num_slides: int = 10) -> Dict[str, Any]:
        """Generates structured slides data for a presentation."""
        if presentation_id in self.generated_presentations: raise ValueError(f"Presentation '{presentation_id}' already exists.")
        if num_slides < 5 or num_slides > 20: raise ValueError("Number of slides must be between 5 and 20.")

        slides_data = []
        
        # Title Slide
        slides_data.append({"title": f"{topic.title()}: An Overview", "content": f"Presented to {audience.title()} Audience"})

        # Introduction
        slides_data.append({"title": "Introduction", "content": f"This presentation will cover key aspects of {topic.lower()}."})

        # Key Points (dynamic based on num_slides)
        key_points_count = max(1, num_slides - 4) # Reserve for title, intro, conclusion, Q&A
        for i in range(key_points_count):
            content_detail = f"Detailed information about a specific aspect of {topic.lower()}."
            if audience == "technical":
                content_detail = f"In-depth analysis of technical specifications and implementation details for {topic.lower()}."
            elif audience == "executive":
                content_detail = f"Strategic implications and business value of {topic.lower()}."
            slides_data.append({"title": f"Key Point {i+1}: [Aspect of {topic}]", "content": content_detail})

        # Conclusion
        slides_data.append({"title": "Conclusion", "content": f"Summary of main takeaways and future outlook for {topic.lower()}."})

        # Q&A
        slides_data.append({"title": "Q&A / Discussion", "content": "Thank you for your attention. Questions?"})
        
        new_presentation = {
            "id": presentation_id, "topic": topic, "audience": audience, "num_slides": num_slides,
            "slides_data": slides_data, "generated_at": datetime.now().isoformat()
        }
        self.generated_presentations[presentation_id] = new_presentation
        self._save_data()
        return new_presentation

    def get_generated_content(self, presentation_id: str) -> Dict[str, Any]:
        """Retrieves previously generated presentation content."""
        presentation = self.generated_presentations.get(presentation_id)
        if not presentation: raise ValueError(f"Presentation '{presentation_id}' not found.")
        return presentation

    def execute(self, operation: str, presentation_id: str, **kwargs: Any) -> Any:
        if operation == "generate_slides_content":
            return self.generate_slides_content(presentation_id, kwargs['topic'], kwargs.get('audience', 'general'), kwargs.get('num_slides', 10))
        elif operation == "get_generated_content":
            return self.get_generated_content(presentation_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PresentationContentGeneratorTool functionality...")
    temp_dir = "temp_presentation_content_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    content_generator = PresentationContentGeneratorTool(data_dir=temp_dir)
    
    try:
        # 1. Generate content for a technical presentation
        print("\n--- Generating content for 'AI in Healthcare' (technical audience, 12 slides) ---")
        tech_presentation = content_generator.execute(operation="generate_slides_content", presentation_id="AI_Healthcare_Tech", topic="AI in Healthcare", audience="technical", num_slides=12)
        print(json.dumps(tech_presentation, indent=2))

        # 2. Generate content for a general audience presentation
        print("\n--- Generating content for 'Climate Change Impact' (general audience, 8 slides) ---")
        general_presentation = content_generator.execute(operation="generate_slides_content", presentation_id="Climate_Change_General", topic="Climate Change Impact", audience="general", num_slides=8)
        print(json.dumps(general_presentation, indent=2))

        # 3. Retrieve generated content
        print("\n--- Retrieving content for 'AI_Healthcare_Tech' ---")
        retrieved_content = content_generator.execute(operation="get_generated_content", presentation_id="AI_Healthcare_Tech")
        print(json.dumps(retrieved_content, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
