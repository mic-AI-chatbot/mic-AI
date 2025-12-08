import io
import sys
import contextlib
import json
import logging
import os
import tempfile
import subprocess  # nosec B404
import asyncio
import difflib
import re # Import re for parsing LLM output
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool
from mic.llm_loader import get_llm

logger = logging.getLogger(__name__)

class LLMCodeReviewer:
    """Manages the LLM instance for code review tasks."""
    _llm = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMCodeReviewer, cls).__new__(cls)
            cls._instance._llm = get_llm()
            if cls._instance._llm is None:
                logger.error("LLM not initialized. Code review tools will not be fully functional.")
        return cls._instance

    async def generate_response(self, prompt: str) -> str:
        if self._llm is None:
            return json.dumps({"error": "LLM not available. Please ensure it is configured correctly."})
        
        response_content = []
        try:
            async for chunk in self._llm.stream_response(prompt):
                if chunk.get("type") == "token" and chunk.get("content"):
                    response_content.append(chunk["content"])
                elif chunk.get("type") == "error":
                    logger.error(f"Error from LLM stream: {chunk.get('content')}")
                    return json.dumps({"error": f"Error generating response: {chunk.get('content')}"})
            return "".join(response_content)
        except Exception as e:
            logger.error(f"LLM stream generation failed: {e}")
            return json.dumps({"error": f"LLM stream generation failed: {e}"})

llm_code_reviewer_instance = LLMCodeReviewer()

class RunStaticCodeAnalysisTool(BaseTool):
    """Performs static code analysis on Python code using Flake8."""
    def __init__(self, tool_name="run_static_code_analysis"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Performs static code analysis on Python code (string or file) using Flake8 to identify style guide violations, programming errors, and complexity issues. Returns a structured JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Optional: The Python code string to analyze.", "default": None},
                "file_path": {"type": "string", "description": "Optional: The absolute path to the Python file to analyze.", "default": None}
            },
            "required": [] # Either code or file_path must be provided
        }

    def execute(self, code: str = None, file_path: str = None, **kwargs: Any) -> str:
        if not code and not file_path:
            return json.dumps({"error": "No code or file_path provided for analysis."})

        scan_path = file_path
        temp_file_created = False
        if code:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(code)
                scan_path = tmp.name
            temp_file_created = True

        try:
            # Use sys.executable to ensure flake8 is run with the correct Python environment
            command = [sys.executable, '-m', 'flake8', '--isolated', '--format=json', scan_path]
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8')  # nosec B603
            
            output = process.stdout
            error = process.stderr

            if process.returncode == 0:
                return json.dumps({"issues": [], "message": "No static analysis issues found."}, indent=2)
            else:
                try:
                    issues = json.loads(output)
                    return json.dumps({"issues": issues, "message": f"Found {len(issues)} static analysis issues."}, indent=2)
                except json.JSONDecodeError:
                    return json.dumps({"error": f"Flake8 ran, but output was not valid JSON. Raw output:\n{output}\nError:\n{error}"})

        except FileNotFoundError: # flake8 command itself not found
            return json.dumps({"error": "Flake8 is not installed or not found in PATH. Please install it (e.g., pip install flake8)."})
        except Exception as e:
            logger.error(f"An error occurred during Flake8 analysis: {e}")
            return json.dumps({"error": f"An error occurred during Flake8 analysis: {e}"})
        finally:
            if temp_file_created and os.path.exists(scan_path):
                os.remove(scan_path)

class SuggestCodeImprovementsLLMTool(BaseTool):
    """Suggests improvements for code using an LLM."""
    def __init__(self, tool_name="suggest_code_improvements_llm"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Suggests improvements for a given code snippet using an LLM, focusing on quality, style, and potential issues. Can incorporate static analysis findings. Returns a structured JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The code snippet to review for improvements."},
                "language": {"type": "string", "description": "The programming language of the code.", "default": "python"},
                "static_analysis_report_json": {"type": "string", "description": "Optional: JSON report from static analysis (e.g., from RunStaticCodeAnalysisTool).", "default": None}
            },
            "required": ["code"]
        }

    def execute(self, code: str, language: str = "python", static_analysis_report_json: str = None, **kwargs: Any) -> str:
        prompt = f"Review the following {language} code for quality, style, and potential issues. Provide actionable suggestions for improvement. "
        if static_analysis_report_json:
            try:
                static_analysis_report = json.loads(static_analysis_report_json)
                if static_analysis_report.get("issues"):
                    prompt += f"Consider these static analysis findings: {json.dumps(static_analysis_report['issues'])}. "
            except json.JSONDecodeError:
                logger.warning("Invalid static_analysis_report_json provided. Ignoring.")
        
        prompt += f"Provide the suggestions in JSON format with a key 'improvements' which is a list of objects, each with 'category', 'description', and 'severity' keys.\n\nCode:\n```\n{code}\n```\n\nJSON Output:"
        
        llm_response = asyncio.run(llm_code_reviewer_instance.generate_response(prompt))
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class CompareCodeVersionsTool(BaseTool):
    """Compares two versions of code and highlights differences in terms of quality metrics or identified issues."""
    def __init__(self, tool_name="compare_code_versions"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Compares two versions of code to highlight differences in quality metrics, identified issues, or structural changes. Returns a structured JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_version1": {"type": "string", "description": "The first version of the code to compare."},
                "code_version2": {"type": "string", "description": "The second version of the code to compare."},
                "language": {"type": "string", "description": "The programming language of the code.", "default": "python"}
            },
            "required": ["code_version1", "code_version2"]
        }

    def execute(self, code_version1: str, code_version2: str, language: str = "python", **kwargs: Any) -> str:
        diff_lines = list(difflib.unified_diff(code_version1.splitlines(keepends=True), code_version2.splitlines(keepends=True), fromfile='version1', tofile='version2'))

        if not diff_lines:
            return json.dumps({"message": "No differences found between the two code versions."})

        prompt = f"Analyze the following code changes in {language} and summarize the potential impact on quality, style, and functionality. Highlight any new issues introduced or resolved. Provide the summary in JSON format with keys 'diff_summary' and 'impact_analysis'.\n\nDiff:\n```diff\n{''.join(diff_lines)}\n```\n\nJSON Output:"

        llm_response = asyncio.run(llm_code_reviewer_instance.generate_response(prompt))
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})