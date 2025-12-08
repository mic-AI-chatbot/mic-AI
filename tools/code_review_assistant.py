import logging
import json
import random
import re
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Code review tools will not be fully functional.")

logger = logging.getLogger(__name__)

class CodeReviewModel:
    """Manages the text generation model for code review tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CodeReviewModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for code review are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for code review...")
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

code_review_model_instance = CodeReviewModel()

class ReviewCodeTool(BaseTool):
    """Identifies code smells and suggests improvements in a code snippet using an AI model."""
    def __init__(self, tool_name="review_code"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Identifies common code smells (e.g., missing docstrings, long lines, complex logic) and suggests improvements within a code snippet using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "The code snippet to analyze for code smells."},
                "language": {"type": "string", "description": "The programming language of the code.", "default": "python"}
            },
            "required": ["code_snippet"]
        }

    def execute(self, code_snippet: str, language: str = "python", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Review the following {language} code snippet and identify any common code smells (e.g., Long Method, Complex Conditional, Duplicate Code, Missing Docstrings, Magic Numbers). For each identified finding, provide its type, severity (low, medium, high), and a suggestion for improvement. Provide the output in JSON format with a key 'review_findings' which is a list of objects, each with 'type', 'severity', and 'suggestion' keys.\n\nCode:\n```\n{code_snippet}\n```\n\nJSON Output:"
        
        llm_response = code_review_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class PrioritizeReviewFindingsTool(BaseTool):
    """Prioritizes code review findings based on their severity and potential impact using an AI model."""
    def __init__(self, tool_name="prioritize_review_findings"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Prioritizes code review findings based on their severity and potential impact, providing a ranked list of issues to address using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "review_findings_json": {
                    "type": "string",
                    "description": "The JSON report of identified code review findings (e.g., from ReviewCodeTool)."
                },
                "context": {"type": "string", "description": "Optional: Additional context about the project or priorities to aid prioritization."}
            },
            "required": ["review_findings_json"]
        }

    def execute(self, review_findings_json: str, context: str = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        try:
            review_findings = json.loads(review_findings_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for review_findings_json."})

        prompt = f"Prioritize the following code review findings based on their severity and potential impact. Provide a ranked list of issues to address, along with a brief justification for the prioritization. Provide the output in JSON format with a key 'prioritized_findings' which is a list of objects, each with 'type', 'severity', 'suggestion', and 'priority_rank' keys.\n\nReview Findings: {json.dumps(review_findings)}\n"
        if context:
            prompt += f"Context: {context}\n"
        prompt += "\nJSON Output:"
        
        llm_response = code_review_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})