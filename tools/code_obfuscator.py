import logging
import json
import random
import os
import re
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class Obfuscator:
    """Implements simple code obfuscation techniques for Python."""
    def obfuscate_code(self, code: str, obfuscation_level: str = "medium") -> str:
        obfuscated_code = code
        
        # Simple variable renaming
        if obfuscation_level in ["medium", "high"]:
            # Find all identifiers (potential variable names)
            identifiers = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
            
            # Filter out common keywords and built-ins
            keywords = {'self', 'cls', 'True', 'False', 'None', 'and', 'or', 'not', 'if', 'else', 'elif', 'for', 'while', 'def', 'class', 'import', 'from', 'as', 'return', 'yield', 'try', 'except', 'finally', 'with', 'pass', 'break', 'continue', 'in', 'is', 'lambda', 'global', 'nonlocal', 'del', 'assert', 'async', 'await'}
            
            obfuscatable_vars = [var for var in identifiers if var not in keywords and not var.startswith('__')]
            
            # Obfuscate a random subset of variables
            num_vars_to_obfuscate = min(len(obfuscatable_vars), random.randint(5, 15) if obfuscation_level == "high" else random.randint(2, 7))  # nosec B311
            vars_to_obfuscate = random.sample(obfuscatable_vars, num_vars_to_obfuscate)  # nosec B311

            for var in vars_to_obfuscate:
                new_var = ''.join(random.choice('lI0O') for _ in range(random.randint(5, 10)))  # nosec B311
                obfuscated_code = re.sub(r'\b' + re.escape(var) + r'\b', new_var, obfuscated_code)
        
        # Add dummy code/lines
        if obfuscation_level == "high":
            lines = obfuscated_code.split('\n')
            for _ in range(random.randint(5, 10)):  # nosec B311
                insert_line = random.randint(0, len(lines))  # nosec B311
                lines.insert(insert_line, f"    # Dummy line {random.randint(1, 1000)}: pass # {random.choice(['do_nothing', 'check_status', 'update_counter'])}()")  # nosec B311
            obfuscated_code = "\n".join(lines)

        return obfuscated_code

class ObfuscationManager:
    """Manages obfuscation jobs, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ObfuscationManager, cls).__new__(cls)
            cls._instance.obfuscation_jobs: Dict[str, Any] = {}
        return cls._instance

    def add_job(self, job_id: str, original_source: str, obfuscated_path: str, obfuscation_level: str, original_code: str, obfuscated_code: str):
        self.obfuscation_jobs[job_id] = {
            "original_source": original_source, # Can be file path or "code_string"
            "obfuscated_path": obfuscated_path,
            "obfuscation_level": obfuscation_level,
            "original_code_sample": original_code[:200] + "..." if len(original_code) > 200 else original_code,
            "obfuscated_code_sample": obfuscated_code[:200] + "..." if len(obfuscated_code) > 200 else obfuscated_code,
            "status": "completed",
            "timestamp": datetime.now().isoformat() + "Z"
        }

    def get_job(self, job_id: str) -> Dict[str, Any]:
        return self.obfuscation_jobs.get(job_id)

obfuscation_manager = ObfuscationManager()
obfuscator = Obfuscator()

class ObfuscateCodeTool(BaseTool):
    """Obfuscates Python code from a file or string and saves the obfuscated version."""
    def __init__(self, tool_name="obfuscate_code"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Obfuscates Python code from a file or string to make it harder to understand, and saves the obfuscated version to a new file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_path": {"type": "string", "description": "The absolute path to the code file to obfuscate (mutually exclusive with code_string)."},
                "code_string": {"type": "string", "description": "The code string to obfuscate (mutually exclusive with code_path)."},
                "output_path": {"type": "string", "description": "The absolute path to save the obfuscated code."},
                "obfuscation_level": {"type": "string", "description": "The desired obfuscation level.", "enum": ["low", "medium", "high"], "default": "medium"}
            },
            "required": ["output_path"]
        }

    def execute(self, output_path: str, code_path: str = None, code_string: str = None, obfuscation_level: str = "medium", **kwargs: Any) -> str:
        if code_path is None and code_string is None:
            return json.dumps({"error": "Either 'code_path' or 'code_string' must be provided."})
        if code_path and code_string:
            return json.dumps({"error": "Only one of 'code_path' or 'code_string' can be provided."})
        
        original_code = ""
        original_source_identifier = "code_string_input"
        if code_path:
            if not os.path.isabs(code_path):
                return json.dumps({"error": "code_path must be an absolute path."})
            if not os.path.exists(code_path):
                return json.dumps({"error": f"File not found at '{code_path}'."})
            with open(code_path, "r", encoding="utf-8") as f:
                original_code = f.read()
            original_source_identifier = os.path.abspath(code_path)
        elif code_string:
            original_code = code_string
        
        if not original_code.strip():
            return json.dumps({"error": "No code provided for obfuscation."})

        obfuscated_code = obfuscator.obfuscate_code(original_code, obfuscation_level)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(obfuscated_code)
        
        job_id = f"obf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}"  # nosec B311
        obfuscation_manager.add_job(job_id, original_source_identifier, os.path.abspath(output_path), obfuscation_level, original_code, obfuscated_code)
        
        report = {
            "message": f"Code obfuscated with '{obfuscation_level}' level. Output saved to '{os.path.abspath(output_path)}'.",
            "obfuscation_job_id": job_id,
            "output_file_path": os.path.abspath(output_path)
        }
        return json.dumps(report, indent=2)

class GetObfuscationStatusTool(BaseTool):
    """Retrieves the status and details of a code obfuscation job."""
    def __init__(self, tool_name="get_obfuscation_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the status and details of a previously initiated code obfuscation job using its unique ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"obfuscation_id": {"type": "string", "description": "The ID of the obfuscation job to retrieve status for."}},
            "required": ["obfuscation_id"]
        }

    def execute(self, obfuscation_id: str, **kwargs: Any) -> str:
        job = obfuscation_manager.get_job(obfuscation_id)
        if not job:
            return json.dumps({"error": f"Obfuscation job with ID '{obfuscation_id}' not found."})
            
        return json.dumps(job, indent=2)

class ViewObfuscatedCodeTool(BaseTool):
    """Retrieves and displays the obfuscated code from a completed job."""
    def __init__(self, tool_name="view_obfuscated_code"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves and displays the obfuscated code from a completed obfuscation job."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"obfuscation_id": {"type": "string", "description": "The ID of the obfuscation job to retrieve the code for."}},
            "required": ["obfuscation_id"]
        }

    def execute(self, obfuscation_id: str, **kwargs: Any) -> str:
        job = obfuscation_manager.get_job(obfuscation_id)
        if not job:
            return json.dumps({"error": f"Obfuscation job with ID '{obfuscation_id}' not found."})
        
        if not os.path.exists(job["obfuscated_path"]):
            return json.dumps({"error": f"Obfuscated file not found at '{job['obfuscated_path']}'. It might have been deleted."})

        with open(job["obfuscated_path"], "r", encoding="utf-8") as f:
            obfuscated_code = f.read()
        
        report = {
            "obfuscation_id": obfuscation_id,
            "obfuscated_code": obfuscated_code
        }
        return json.dumps(report, indent=2)