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
    logging.warning("transformers library not found. Code refactoring tools will not be fully functional.")

logger = logging.getLogger(__name__)

class RefactoringModel:
    """Manages the text generation model for code refactoring tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RefactoringModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for refactoring are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for refactoring...")
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

refactoring_model_instance = RefactoringModel()

class IdentifyCodeSmellsTool(BaseTool):
    """Identifies common code smells in a code snippet using an AI model."""
    def __init__(self, tool_name="identify_code_smells"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Identifies common code smells (e.g., long methods, complex conditionals, duplicate code, Feature Envy, Large Class) within a given code snippet using an AI model."

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

        prompt = f"Analyze the following {language} code snippet and identify any common code smells (e.g., Long Method, Complex Conditional, Duplicate Code, Feature Envy, Large Class). For each identified smell, provide its type, a brief description, and the approximate line numbers. Provide the output in JSON format with a key 'code_smells' which is a list of objects, each with 'type', 'description', and 'line_numbers' keys.\n\nCode:\n```\n{code_snippet}\n```\n\nJSON Output:"
        
        llm_response = refactoring_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON. Manual parsing needed.", "raw_llm_response": llm_response})

class SuggestRefactoringPatternsTool(BaseTool):
    """Suggests refactoring patterns for identified code smells using an AI model."""
    def __init__(self, tool_name="suggest_refactoring_patterns"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Suggests appropriate refactoring patterns (e.g., 'Extract Method', 'Replace Conditional with Polymorphism') for identified code smells using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_smells_report_json": {
                    "type": "string",
                    "description": "The JSON report of identified code smells (e.g., from IdentifyCodeSmellsTool)."
                },
                "language": {"type": "string", "description": "The programming language of the code.", "default": "python"}
            },
            "required": ["code_smells_report_json"]
        }

    def execute(self, code_smells_report_json: str, language: str = "python", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        try:
            code_smells_report = json.loads(code_smells_report_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for code_smells_report_json."})

        prompt = f"Based on the following identified code smells in a {language} codebase: {json.dumps(code_smells_report)}. Suggest appropriate refactoring patterns (e.g., Extract Method, Replace Conditional with Polymorphism) for each smell. Provide the suggestions in JSON format with a key 'refactoring_suggestions' which is a list of objects, each with 'smell_type', 'pattern', and 'description' keys.\n\nJSON Output:"
        
        llm_response = refactoring_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON. Manual parsing needed.", "raw_llm_response": llm_response})

class GenerateRefactoredCodeTool(BaseTool):
    """Generates refactored code based on a code snippet and a refactoring goal using an AI model."""
    def __init__(self, tool_name="generate_refactored_code"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates refactored code based on a code snippet and a refactoring goal (e.g., 'extract method', 'simplify conditional') using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "The code snippet to refactor."},
                "refactoring_goal": {"type": "string", "description": "The specific refactoring goal (e.g., 'extract method for calculating total', 'simplify nested if statements')."},
                "language": {"type": "string", "description": "The programming language of the code.", "default": "python"}
            },
            "required": ["code_snippet", "refactoring_goal"]
        }

    def execute(self, code_snippet: str, refactoring_goal: str, language: str = "python", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Refactor the following {language} code snippet with the goal of '{refactoring_goal}'. Provide only the refactored code in a code block.\n\nOriginal Code:\n```\n{code_snippet}\n```\n\nRefactored Code:"
        
        llm_response = refactoring_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        code_match = re.search(r"```(?:\w+)?\n(.*?)```", llm_response, re.DOTALL)
        refactored_code = code_match.group(1).strip() if code_match else llm_response.strip()

        return json.dumps({"original_code": code_snippet, "refactoring_goal": refactoring_goal, "refactored_code": refactored_code}, indent=2)