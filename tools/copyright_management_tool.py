import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

# Deferring transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered infringement detection will not be available.")

logger = logging.getLogger(__name__)

COPYRIGHTS_FILE = Path("copyrights.json")

class CopyrightManager:
    """Manages copyright information, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = COPYRIGHTS_FILE):
        if cls._instance is None:
            cls._instance = super(CopyrightManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.copyrights: Dict[str, Any] = cls._instance._load_copyrights()
        return cls._instance

    def _load_copyrights(self) -> Dict[str, Any]:
        """Loads copyright information from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty copyrights.")
                return {}
            except Exception as e:
                logger.error(f"Error loading copyrights from {self.file_path}: {e}")
                return {}
        return {}

    def _save_copyrights(self) -> None:
        """Saves copyright information to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.copyrights, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving copyrights to {self.file_path}: {e}")

    def register_copyright(self, copyright_id: str, work_title: str, author: str, date_created: str) -> bool:
        if copyright_id in self.copyrights:
            return False
        self.copyrights[copyright_id] = {
            "work_title": work_title,
            "author": author,
            "date_created": date_created,
            "date_registered": datetime.now().isoformat() + "Z",
            "status": "registered"
        }
        self._save_copyrights()
        return True

    def get_copyright(self, copyright_id: str) -> Optional[Dict[str, Any]]:
        return self.copyrights.get(copyright_id)

    def list_copyrights(self) -> List[Dict[str, Any]]:
        return [{"copyright_id": c_id, "work_title": details['work_title'], "author": details['author'], "status": details['status'], "date_registered": details['date_registered']} for c_id, details in self.copyrights.items()]

copyright_manager = CopyrightManager()

class InfringementDetectionModel:
    """Manages the text generation model for simulating infringement detection, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InfringementDetectionModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for infringement detection are not installed.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for infringement detection...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if self._generator is None:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

infringement_detection_model_instance = InfringementDetectionModel()

class RegisterCopyrightTool(BaseTool):
    """Registers a new copyright for a creative work."""
    def __init__(self, tool_name="register_copyright"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Registers a new copyright for a creative work, assigning it a unique copyright ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "copyright_id": {"type": "string", "description": "A unique ID for the copyright."},
                "work_title": {"type": "string", "description": "The title of the creative work."},
                "author": {"type": "string", "description": "The author or creator of the work."},
                "date_created": {"type": "string", "description": "The date the work was created (YYYY-MM-DD)."}
            },
            "required": ["copyright_id", "work_title", "author", "date_created"]
        }

    def execute(self, copyright_id: str, work_title: str, author: str, date_created: str, **kwargs: Any) -> str:
        success = copyright_manager.register_copyright(copyright_id, work_title, author, date_created)
        if success:
            report = {"message": f"Copyright for '{work_title}' by '{author}' registered successfully with ID '{copyright_id}'. Status: registered."}
        else:
            report = {"error": f"Copyright with ID '{copyright_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class MonitorCopyrightInfringementTool(BaseTool):
    """Monitors for copyright infringement of a registered work using an AI model."""
    def __init__(self, tool_name="monitor_copyright_infringement"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Monitors for potential copyright infringement of a registered work, returning a report of detected infringements using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "copyright_id": {"type": "string", "description": "The ID of the copyright to monitor."},
                "search_scope": {"type": "string", "description": "The scope of monitoring.", "enum": ["web", "social_media", "all"], "default": "web"}
            },
            "required": ["copyright_id"]
        }

    def execute(self, copyright_id: str, search_scope: str = "web", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered infringement detection."})

        copyright_details = copyright_manager.get_copyright(copyright_id)
        if not copyright_details:
            return json.dumps({"error": f"Copyright with ID '{copyright_id}' not found."})
        
        prompt = f"Simulate monitoring for copyright infringement of the work '{copyright_details['work_title']}' by '{copyright_details['author']}' (ID: {copyright_id}) across the {search_scope}. Identify 1-3 potential infringements, including type (e.g., direct_copy, derivative_work), source, and details. Provide the output in JSON format with a key 'infringements_detected' which is a list of objects, each with 'type', 'source', and 'details' keys.\n\nJSON Output:"
        
        llm_response = infringement_detection_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class GetCopyrightDetailsTool(BaseTool):
    """Retrieves details of a specific copyright."""
    def __init__(self, tool_name="get_copyright_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves details of a specific copyright, including its title, author, dates, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"copyright_id": {"type": "string", "description": "The ID of the copyright to retrieve."}},
            "required": ["copyright_id"]
        }

    def execute(self, copyright_id: str, **kwargs: Any) -> str:
        copyright_details = copyright_manager.get_copyright(copyright_id)
        if not copyright_details:
            return json.dumps({"error": f"Copyright with ID '{copyright_id}' not found."})
            
        return json.dumps(copyright_details, indent=2)

class ListCopyrightsTool(BaseTool):
    """Lists all registered copyrights."""
    def __init__(self, tool_name="list_copyrights"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all registered copyrights, showing their ID, title, author, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        copyrights = copyright_manager.list_copyrights()
        if not copyrights:
            return json.dumps({"message": "No copyrights found."})
        
        return json.dumps({"total_copyrights": len(copyrights), "copyrights": copyrights}, indent=2)