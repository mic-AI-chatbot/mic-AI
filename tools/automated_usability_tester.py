import logging
import json
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Automated usability testing tools will not be available.")

logger = logging.getLogger(__name__)

class UsabilityAnalysisModel:
    """Manages the text generation model for usability analysis tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UsabilityAnalysisModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for usability analysis are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for usability analysis...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

usability_model_instance = UsabilityAnalysisModel()

class TestUIUsabilityTool(BaseTool):
    """Tests the usability of a user interface for a given task using an AI model."""
    def __init__(self, tool_name="test_ui_usability"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Tests the usability of a user interface (UI) for a given task, identifying potential issues and user pain points using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ui_description": {"type": "string", "description": "A detailed description of the UI to be tested (e.g., 'a website homepage with a search bar and product listings')."},
                "task_description": {"type": "string", "description": "A description of the task a user would perform (e.g., 'find a product and add it to the cart')."}
            },
            "required": ["ui_description", "task_description"]
        }

    def execute(self, ui_description: str, task_description: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Analyze the usability of the following UI for the given task. Identify potential usability issues, user pain points, and suggest improvements. Provide a list of issues and an overall usability score (out of 100).\n\nUI Description: {ui_description}\nTask: {task_description}\n\nUsability Analysis (in JSON format with 'issues' and 'overall_score'):"
        
        generated_text = usability_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 400)
        
        # Attempt to parse the generated text as JSON
        json_start = generated_text.find('{')
        json_end = generated_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = generated_text[json_start:json_end]
            try:
                return json.dumps(json.loads(json_str), indent=2)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse generated JSON: {json_str}")
                return json.dumps({"raw_output": generated_text, "error": "Generated output was not valid JSON. Manual parsing needed."})
        else:
            return json.dumps({"raw_output": generated_text, "error": "Could not find JSON in generated output. Manual parsing needed."})

class GenerateUsabilityReportTool(BaseTool):
    """Generates a comprehensive usability report based on test results using an AI model."""
    def __init__(self, tool_name="generate_usability_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a comprehensive usability report based on test results, including findings, recommendations, and severity ratings, using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ui_identifier": {"type": "string", "description": "A unique identifier for the UI tested."},
                "task_description": {"type": "string", "description": "The description of the task tested."},
                "test_results_json": {
                    "type": "string",
                    "description": "The JSON string of test results from the TestUIUsabilityTool."
                }
            },
            "required": ["ui_identifier", "task_description", "test_results_json"]
        }

    def execute(self, ui_identifier: str, task_description: str, test_results_json: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        try:
            test_results = json.loads(test_results_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for test_results_json."})

        prompt = f"Generate a comprehensive usability report for the UI '{ui_identifier}' for the task '{task_description}'. The test results are: {json.dumps(test_results)}. The report should include an executive summary, detailed findings, recommendations with severity ratings, and an overall conclusion. Report:"
        
        generated_report_content = usability_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        report = {
            "ui_identifier": ui_identifier,
            "task_description": task_description,
            "usability_report_content": generated_report_content
        }
        return json.dumps(report, indent=2)
