import logging
import random
import json
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PPTDesignCreatorTool(BaseTool):
    """
    A tool that generates PowerPoint (PPT) design suggestions and a basic
    presentation outline based on topic, number of slides, and design style.
    """

    def __init__(self, tool_name: str = "PPTDesignCreator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates PowerPoint (PPT) design suggestions and a basic presentation outline based on topic, slides, and style."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "presentation_topic": {"type": "string", "description": "The main topic of the presentation."},
                "num_slides": {"type": "integer", "minimum": 5, "maximum": 20, "default": 10, "description": "The desired number of slides."},
                "design_style": {"type": "string", "enum": ["professional", "minimalist", "creative", "modern"], "default": "professional", "description": "The desired design style."}
            },
            "required": ["presentation_topic"]
        }

    def execute(self, presentation_topic: str, num_slides: int = 10, design_style: str = "professional", **kwargs: Any) -> Dict[str, Any]:
        """
        Generates a presentation outline and design suggestions.
        """
        if num_slides < 5 or num_slides > 20:
            raise ValueError("Number of slides must be between 5 and 20.")

        outline = self._generate_outline(presentation_topic, num_slides)
        design_suggestions = self._generate_design_suggestions(design_style)

        return {
            "status": "success",
            "presentation_topic": presentation_topic,
            "num_slides": num_slides,
            "design_style": design_style,
            "outline": outline,
            "design_suggestions": design_suggestions
        }

    def _generate_outline(self, topic: str, num_slides: int) -> List[Dict[str, str]]:
        """Generates a rule-based presentation outline."""
        outline = []
        
        # Standard slides
        outline.append({"slide_number": 1, "title": f"Title Slide: {topic.title()}", "content": f"Presented by [Your Name/Team]"})
        outline.append({"slide_number": 2, "title": "Introduction", "content": f"Overview of {topic} and presentation objectives."})
        
        # Dynamic key points based on num_slides
        key_points_count = max(1, num_slides - 4) # Leave room for title, intro, conclusion, Q&A
        for i in range(key_points_count):
            outline.append({"slide_number": i + 3, "title": f"Key Point {i+1}: [Specific Aspect of {topic}]", "content": f"Detailed discussion of a key aspect related to {topic}."})
        
        outline.append({"slide_number": num_slides - 1, "title": "Conclusion", "content": "Summary of key takeaways and final thoughts."})
        outline.append({"slide_number": num_slides, "title": "Q&A / Thank You", "content": "Open for questions and contact information."})
        
        return outline

    def _generate_design_suggestions(self, design_style: str) -> Dict[str, Any]:
        """Generates rule-based design suggestions based on style."""
        suggestions = {
            "color_palette": [],
            "typography": {"header_font": "", "body_font": ""},
            "visual_elements": [],
            "animation_ideas": []
        }

        if design_style == "professional":
            suggestions["color_palette"] = ["#003366", "#6699CC", "#FFFFFF", "#F0F0F0"] # Dark Blue, Light Blue, White, Light Gray
            suggestions["typography"] = {"header_font": "Arial Bold", "body_font": "Arial Regular"}
            suggestions["visual_elements"] = ["Clean, crisp icons", "High-quality stock photos", "Minimalist charts"]
            suggestions["animation_ideas"] = ["Subtle fades", "Wipes"]
        elif design_style == "minimalist":
            suggestions["color_palette"] = ["#FFFFFF", "#000000", "#CCCCCC", "#666666"] # White, Black, Light Gray, Dark Gray
            suggestions["typography"] = {"header_font": "Helvetica Neue Light", "body_font": "Open Sans Light"}
            suggestions["visual_elements"] = ["Plenty of white space", "Line icons", "Simple geometric shapes"]
            suggestions["animation_ideas"] = ["Instant transitions", "No animations"]
        elif design_style == "creative":
            suggestions["color_palette"] = ["#FF6B6B", "#FFE66D", "#4ECDC4", "#C70039"] # Vibrant, contrasting colors
            suggestions["typography"] = {"header_font": "Montserrat Bold", "body_font": "Lato Regular"}
            suggestions["visual_elements"] = ["Custom illustrations", "Dynamic data visualizations", "Hand-drawn elements"]
            suggestions["animation_ideas"] = ["Playful bounces", "Zoom effects", "Morph transitions"]
        elif design_style == "modern":
            suggestions["color_palette"] = ["#2C3E50", "#3498DB", "#ECF0F1", "#95A5A6"] # Dark Blue, Bright Blue, Light Gray, Gray
            suggestions["typography"] = {"header_font": "Roboto Slab Bold", "body_font": "Roboto Regular"}
            suggestions["visual_elements"] = ["Geometric patterns", "Gradient overlays", "Full-bleed images"]
            suggestions["animation_ideas"] = ["Smooth slides", "Parallax scrolling"]
        
        return suggestions

if __name__ == '__main__':
    print("Demonstrating PPTDesignCreatorTool functionality...")
    
    ppt_creator = PPTDesignCreatorTool()
    
    try:
        # 1. Generate a professional presentation outline and design suggestions
        print("\n--- Generating Professional PPT for 'Quarterly Business Review' (10 slides) ---")
        result1 = ppt_creator.execute(presentation_topic="Quarterly Business Review", num_slides=10, design_style="professional")
        print(json.dumps(result1, indent=2))

        # 2. Generate a creative presentation outline and design suggestions
        print("\n--- Generating Creative PPT for 'Future of AI' (15 slides) ---")
        result2 = ppt_creator.execute(presentation_topic="Future of AI", num_slides=15, design_style="creative")
        print(json.dumps(result2, indent=2))
        
        # 3. Generate a minimalist presentation outline and design suggestions
        print("\n--- Generating Minimalist PPT for 'Product Launch Strategy' (7 slides) ---")
        result3 = ppt_creator.execute(presentation_topic="Product Launch Strategy", num_slides=7, design_style="minimalist")
        print(json.dumps(result3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")