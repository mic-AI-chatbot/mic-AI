import logging
import json
import re
from typing import Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Automated debugging tools will not be available.")

logger = logging.getLogger(__name__)

class DebuggingModel:
    """Manages the text generation model for debugging tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DebuggingModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for debugging are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for debugging...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            # Generate a response that attempts to be JSON
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

debugging_model_instance = DebuggingModel()

class AnalyzeErrorTool(BaseTool):
    """Analyzes an error message or traceback to identify root cause and suggest a fix using an AI model."""
    def __init__(self, tool_name="analyze_error"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes an error message and optional traceback to identify the root cause and suggest a potential fix using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "error_message": {"type": "string", "description": "The error message to analyze."},
                "traceback": {"type": "string", "description": "Optional: The full traceback associated with the error."}
            },
            "required": ["error_message"]
        }

    def execute(self, error_message: str, traceback: str = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Analyze the following error message and traceback to identify the root cause and suggest a fix. Provide the root cause and suggested fix in a structured format.\n\nError Message: {error_message}\n"
        if traceback:
            prompt += f"Traceback:\n{traceback}\n"
        prompt += "Root Cause: "

        generated_text = debugging_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 200)
        
        # Attempt to parse the generated text. This is a heuristic.
        root_cause_match = re.search(r"Root Cause: (.*?)Suggested Fix:", generated_text, re.DOTALL)
        suggested_fix_match = re.search(r"Suggested Fix: (.*)", generated_text, re.DOTALL)

        root_cause = root_cause_match.group(1).strip() if root_cause_match else "Could not extract from AI response."
        suggested_fix = suggested_fix_match.group(1).strip() if suggested_fix_match else "Could not extract from AI response."

        report = {
            "error_message": error_message,
            "traceback": traceback,
            "analysis": {
                "root_cause": root_cause,
                "suggested_fix": suggested_fix
            }
        }
        return json.dumps(report, indent=2)

class DebugCodeTool(BaseTool):
    """Debugs a code snippet, identifies logical errors, and proposes corrected code using an AI model."""
    def __init__(self, tool_name="debug_code"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Debugs a given code snippet, identifies logical errors or bugs, and proposes corrected code using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "The code snippet to debug."},
                "context": {"type": "string", "description": "Optional: Additional context about the code or expected behavior."}
            },
            "required": ["code_snippet"]
        }

    def execute(self, code_snippet: str, context: str = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Debug the following code snippet. Identify any bugs or logical errors and provide the corrected code. Explain the bug and the correction.\n\nCode:\n{code_snippet}\n"
        if context:
            prompt += f"Context: {context}\n"
        prompt += "Bug identified: "

        generated_text = debugging_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 300)
        
        # Attempt to parse the generated text. This is a heuristic.
        bug_identified_match = re.search(r"Bug identified: (.*?)Explanation:", generated_text, re.DOTALL)
        explanation_match = re.search(r"Explanation: (.*?)Corrected Code:", generated_text, re.DOTALL)
        corrected_code_match = re.search(r"Corrected Code:\s*```python\n(.*?)```", generated_text, re.DOTALL)

        bug_identified = bug_identified_match.group(1).strip() if bug_identified_match else "Could not extract from AI response."
        explanation = explanation_match.group(1).strip() if explanation_match else "Could not extract from AI response."
        corrected_code = corrected_code_match.group(1).strip() if corrected_code_match else "Could not extract from AI response."

        report = {
            "code_snippet": code_snippet,
            "context": context,
            "debugging_results": {
                "bug_identified": bug_identified,
                "explanation": explanation,
                "corrected_code": corrected_code
            }
        }
        return json.dumps(report, indent=2)