import io
import sys
import contextlib
import json
import logging
import re # Import re for potential parsing of LLM output
from typing import Dict, Any, Union
from tools.base_tool import BaseTool
from mic.llm_loader import get_llm # Import the shared LLM instance

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def capture_output():
    """
    Context manager to capture stdout and stderr.
    """
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    new_stdout = io.StringIO()
    new_stderr = io.StringIO()
    sys.stdout = new_stdout
    sys.stderr = new_stderr
    try:
        yield new_stdout, new_stderr
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

class LLMDebugger:
    """Manages the LLM instance for debugging tasks, using a singleton pattern."""
    _llm = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMDebugger, cls).__new__(cls)
            cls._instance._llm = get_llm()
            if cls._instance._llm is None:
                logger.error("LLM not initialized. Debugging tools will not be fully functional.")
        return cls._instance

    def generate_response(self, prompt: str) -> str:
        if self._llm is None:
            return json.dumps({"error": "LLM not available. Please ensure it is configured correctly."})
        try:
            return self._llm.generate_response(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return json.dumps({"error": f"LLM generation failed: {e}"})

llm_debugger_instance = LLMDebugger()

class ExecuteCodeSnippetTool(BaseTool):
    """Executes a Python code snippet and captures its stdout, stderr, and any exceptions."""
    def __init__(self, tool_name="execute_code_snippet"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Executes a Python code snippet in a sandboxed environment and captures its stdout, stderr, and any exceptions. NOTE: Direct code execution is currently DISABLED for security reasons. This tool will only simulate execution until a secure sandbox is implemented."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"code_snippet": {"type": "string", "description": "The Python code snippet to execute."}},
            "required": ["code_snippet"]
        }

    def execute(self, code_snippet: str, **kwargs: Any) -> str:
        # For security reasons, direct execution of arbitrary code is disabled.
        # A secure sandboxed environment is required for this functionality.
        return json.dumps({
            "stdout": "",
            "stderr": "Error: Direct code execution is currently disabled for security reasons. A secure sandbox is required.",
            "exception": "SecurityError: Direct code execution disabled."
        }, indent=2)

class DebugCodeWithLLMTool(BaseTool):
    """Identifies and suggests fixes for bugs in a code snippet using an LLM."""
    def __init__(self, tool_name="debug_code_with_llm"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Identifies and suggests fixes for bugs in a code snippet using an LLM, optionally considering an error message and traceback. Returns a structured JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "The code snippet to analyze for bugs."},
                "error_message": {"type": "string", "description": "Optional: The error message that occurred.", "default": None},
                "traceback_str": {"type": "string", "description": "Optional: The traceback string associated with the error.", "default": None},
                "language": {"type": "string", "description": "The programming language of the code (e.g., 'python', 'java').", "default": "python"}
            },
            "required": ["code_snippet"]
        }

    def execute(self, code_snippet: str, error_message: str = None, traceback_str: str = None, language: str = "python", **kwargs: Any) -> str:
        prompt = f"Analyze the following {language} code for bugs. "
        if error_message:
            prompt += f"The following error occurred: {error_message}. "
        if traceback_str:
            prompt += f"Here is the traceback: {traceback_str}. "
        prompt += f"Suggest fixes and explain the reasoning. Provide the bug explanation and corrected code in JSON format with keys 'bug_explanation' and 'corrected_code'.\n\nCode:\n```\n{code_snippet}\n```\n\nJSON Output:"
        
        llm_response = llm_debugger_instance.generate_response(prompt)
        
        try:
            # Attempt to parse the LLM's response as JSON
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            # If LLM doesn't return perfect JSON, return raw response with an error
            return json.dumps({"error": "LLM response was not valid JSON. Manual parsing needed.", "raw_llm_response": llm_response})

class ExplainErrorWithLLMTool(BaseTool):
    """Explains an error message or traceback using an LLM."""
    def __init__(self, tool_name="explain_error_with_llm"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Explains a given error message or traceback using an LLM, providing insights into its cause and potential solutions. Returns a structured JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "error_message": {"type": "string", "description": "The error message to explain."},
                "traceback_str": {"type": "string", "description": "Optional: The traceback string associated with the error.", "default": None},
                "language": {"type": "string", "description": "The programming language of the error (e.g., 'python', 'java').", "default": "python"}
            },
            "required": ["error_message"]
        }

    def execute(self, error_message: str, traceback_str: str = None, language: str = "python", **kwargs: Any) -> str:
        prompt = f"Explain the following {language} error message. "
        if traceback_str:
            prompt += f"Here is the traceback: {traceback_str}. "
        prompt += f"Error: {error_message}. Provide a clear explanation and potential solutions in JSON format with keys 'explanation' and 'solutions'.\n\nJSON Output:"
        
        llm_response = llm_debugger_instance.generate_response(prompt)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class SuggestTestCasesWithLLMTool(BaseTool):
    """Suggests comprehensive test cases for a given code snippet using an LLM."""
    def __init__(self, tool_name="suggest_test_cases_with_llm"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Suggests comprehensive test cases for a given code snippet to ensure its correctness and expose potential bugs, using an LLM. Returns a structured JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "The code snippet for which to suggest test cases."},
                "language": {"type": "string", "description": "The programming language of the code (e.g., 'python', 'java').", "default": "python"}
            },
            "required": ["code_snippet"]
        }

    def execute(self, code_snippet: str, language: str = "python", **kwargs: Any) -> str:
        prompt = f"Suggest comprehensive test cases for the following {language} code to ensure its correctness and expose potential bugs. Provide the test cases (input, expected output) in JSON format with a key 'test_cases' which is a list of objects, each with 'input' and 'expected_output' keys.\n\nCode:\n```\n{code_snippet}\n```\n\nJSON Output:"
        
        llm_response = llm_debugger_instance.generate_response(prompt)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})