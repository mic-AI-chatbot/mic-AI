import logging
import json
import os
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool

# Deferring black import
try:
    import black
    BLACK_AVAILABLE = True
except ImportError:
    black = None
    BLACK_AVAILABLE = False
    logging.warning("black library not found. Python code formatting tools will not be available. Please install it with 'pip install black'.")

logger = logging.getLogger(__name__)

class FormatCodeStringTool(BaseTool):
    """Formats a string of Python code using the 'black' library."""
    def __init__(self, tool_name="format_code_string"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Formats a given string of Python code using the 'black' formatter, adhering to PEP 8 style guidelines."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The Python code string to format."},
                "line_length": {"type": "integer", "description": "The maximum line length for formatting. Defaults to 88.", "default": 88}
            },
            "required": ["code"]
        }

    def execute(self, code: str, line_length: int = 88, **kwargs: Any) -> str:
        if not BLACK_AVAILABLE:
            return json.dumps({"error": "The 'black' library is not installed. Please install it with 'pip install black'."})
        try:
            mode = black.FileMode(line_length=line_length)
            formatted_code = black.format_file_contents(code, fast=False, mode=mode)
            return json.dumps({"original_code": code, "formatted_code": formatted_code}, indent=2)
        except black.InvalidInput as e:
            return json.dumps({"error": f"Invalid Python code provided. {e}"})
        except Exception as e:
            logger.error(f"An unexpected error occurred during formatting: {e}")
            return json.dumps({"error": f"An unexpected error occurred during formatting: {e}"})

class FormatCodeFileTool(BaseTool):
    """Formats a specified code file in place using the 'black' formatter."""
    def __init__(self, tool_name="format_code_file"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Formats a specified code file in place using the 'black' formatter (for Python code)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "The absolute path to the Python code file to format."},
                "line_length": {"type": "integer", "description": "The maximum line length for formatting. Defaults to 88.", "default": 88},
                "language": {"type": "string", "description": "The programming language of the code. Currently only 'python' is supported.", "default": "python"}
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str, line_length: int = 88, language: str = "python", **kwargs: Any) -> str:
        if not BLACK_AVAILABLE:
            return json.dumps({"error": "The 'black' library is not installed. Please install it with 'pip install black'."})
        
        if language.lower() != "python":
            return json.dumps({"error": f"Formatting for '{language}' is not supported. Only 'python' is supported."})

        if not os.path.isabs(file_path):
            return json.dumps({"error": "'file_path' must be an absolute path."})
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File not found at '{file_path}'."})
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            mode = black.FileMode(line_length=line_length)
            formatted_code = black.format_file_contents(code, fast=False, mode=mode)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(formatted_code)
            
            return json.dumps({"message": f"File '{os.path.abspath(file_path)}' formatted successfully using black.", "file_path": os.path.abspath(file_path)}, indent=2)
        except black.InvalidInput as e:
            return json.dumps({"error": f"Invalid Python code in '{file_path}'. {e}"})
        except Exception as e:
            logger.error(f"An unexpected error occurred during file formatting: {e}")
            return json.dumps({"error": f"An unexpected error occurred during file formatting: {e}"})