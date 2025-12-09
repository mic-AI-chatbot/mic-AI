

import logging
import os
from PIL import Image, ImageDraw, ImageFont, ImageGrab
import json
import base64
import io
from typing import Union, List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ScreenshotAnnotationTool(BaseTool):
    """
    A tool for taking screenshots and adding annotations (text, shapes).
    """

    def __init__(self, tool_name: str = "ScreenshotAnnotator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.output_dir = os.path.join(data_dir, "screenshots")
        os.makedirs(self.output_dir, exist_ok=True)

    @property
    def description(self) -> str:
        return "Takes screenshots of the screen or regions, and adds annotations (text, rectangles) to them."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["take_screenshot", "annotate_screenshot"]},
                "output_filename": {"type": "string", "description": "Filename for the output image (e.g., 'my_screenshot.png')."},
                "region": {"type": "array", "items": {"type": "integer"}, "minItems": 4, "maxItems": 4, "description": "Region to capture [x1, y1, x2, y2]."},
                "image_path": {"type": "string", "description": "Absolute path to the image file to annotate."},
                "annotation_type": {"type": "string", "enum": ["text", "rectangle"]},
                "annotation_data": {"type": "object", "description": "Data for the annotation (e.g., {'text': 'Hello', 'position': [10,10], 'color': 'red'})."}
            },
            "required": ["operation"]
        }

    def _take_screenshot(self, output_filename: str, region: Optional[List[int]] = None) -> Dict[str, Any]:
        """Takes a screenshot of the entire screen or a specific region."""
        output_path = os.path.join(self.output_dir, output_filename)
        
        screenshot = ImageGrab.grab(bbox=region)
        screenshot.save(output_path)
        
        return {"status": "success", "message": f"Screenshot saved to {output_path}.", "output_path": output_path}

    def _annotate_screenshot(self, image_path: str, annotation_type: str, annotation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adds annotations (text, shapes) to a screenshot."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found at {image_path}")
        
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)

        if annotation_type == "text":
            text = annotation_data.get("text", "")
            position = tuple(annotation_data.get("position", [10, 10]))
            font_size = annotation_data.get("font_size", 20)
            color = annotation_data.get("color", "red")
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
            draw.text(position, text, font=font, fill=color)
        elif annotation_type == "rectangle":
            xy = annotation_data.get("xy") # [x1, y1, x2, y2]
            outline = annotation_data.get("outline", "red")
            width = annotation_data.get("width", 2)
            draw.rectangle(xy, outline=outline, width=width)
        else:
            raise ValueError(f"Unsupported annotation type: {annotation_type}.")

        img.save(image_path)
        return {"status": "success", "message": f"Screenshot at {image_path} annotated with {annotation_type}.", "output_path": image_path}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "take_screenshot":
            output_filename = kwargs.get('output_filename')
            if not output_filename:
                raise ValueError("Missing 'output_filename' for 'take_screenshot' operation.")
            return self._take_screenshot(output_filename, kwargs.get('region'))
        elif operation == "annotate_screenshot":
            image_path = kwargs.get('image_path')
            annotation_type = kwargs.get('annotation_type')
            annotation_data = kwargs.get('annotation_data')
            if not all([image_path, annotation_type, annotation_data]):
                raise ValueError("Missing 'image_path', 'annotation_type', or 'annotation_data' for 'annotate_screenshot' operation.")
            return self._annotate_screenshot(image_path, annotation_type, annotation_data)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ScreenshotAnnotationTool functionality...")
    temp_dir = "temp_screenshots"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    annotator_tool = ScreenshotAnnotationTool(data_dir=temp_dir)
    
    try:
        # 1. Take a screenshot
        print("\n--- Taking a screenshot ---")
        screenshot_path = os.path.join(temp_dir, "full_screen.png")
        screenshot_result = annotator_tool.execute(operation="take_screenshot", output_filename="full_screen.png")
        print(json.dumps(screenshot_result, indent=2))

        # 2. Annotate the screenshot with text
        print("\n--- Annotating screenshot with text ---")
        text_annotation_data = {"text": "Important Area", "position": [50, 50], "color": "blue", "font_size": 30}
        annotate_text_result = annotator_tool.execute(operation="annotate_screenshot", image_path=screenshot_result["output_path"], annotation_type="text", annotation_data=text_annotation_data)
        print(json.dumps(annotate_text_result, indent=2))

        # 3. Annotate the screenshot with a rectangle
        print("\n--- Annotating screenshot with a rectangle ---")
        rect_annotation_data = {"xy": [40, 40, 200, 100], "outline": "green", "width": 3}
        annotate_rect_result = annotator_tool.execute(operation="annotate_screenshot", image_path=screenshot_result["output_path"], annotation_type="rectangle", annotation_data=rect_annotation_data)
        print(json.dumps(annotate_rect_result, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
