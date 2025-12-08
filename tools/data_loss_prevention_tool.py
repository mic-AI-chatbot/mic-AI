import logging
import os
import re
import shutil
import json
from datetime import datetime
from typing import List, Dict, Any, Union, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataLossPreventionTool(BaseTool):
    """
    A tool for identifying, redacting, and quarantining sensitive information
    to prevent data loss.
    """

    def __init__(self, tool_name: str = "data_loss_prevention_tool"):
        super().__init__(tool_name)
        self.patterns_file = "dlp_patterns.json"
        self.default_quarantine_dir = "quarantine_dlp"
        self.sensitive_patterns: Dict[str, Dict[str, str]] = self._load_patterns()
        if not self.sensitive_patterns:
            self._initialize_default_patterns()
            self._save_patterns()

    @property
    def description(self) -> str:
        return "Identifies, redacts, and quarantines sensitive data based on configurable patterns to prevent data loss."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The DLP operation to perform.",
                    "enum": ["define_pattern", "scan_content", "redact_content", "quarantine_file", "process_file", "list_patterns"]
                },
                "pattern_id": {"type": "string"},
                "regex": {"type": "string"},
                "description": {"type": "string"},
                "content": {"type": "string"},
                "replacement_char": {"type": "string", "default": "*"},
                "file_path": {"type": "string"},
                "action": {"type": "string", "enum": ["scan", "redact", "quarantine"]},
                "quarantine_dir": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_patterns(self) -> Dict[str, Dict[str, str]]:
        if os.path.exists(self.patterns_file):
            with open(self.patterns_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted patterns file '{self.patterns_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_patterns(self) -> None:
        with open(self.patterns_file, 'w') as f:
            json.dump(self.sensitive_patterns, f, indent=4)

    def _initialize_default_patterns(self) -> None:
        self.sensitive_patterns = {
            "credit_card": {"regex": r"\b(?:\d[ -]*?){13,16}\b", "description": "Common credit card number formats"},
            "email_address": {"regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "description": "Standard email address format"},
            "phone_number": {"regex": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "description": "Common US phone number formats"},
        }
        logger.info("Default sensitive patterns initialized.")

    def _define_pattern(self, pattern_id: str, regex: str, description: str) -> Dict[str, Any]:
        if not all([pattern_id, regex]):
            raise ValueError("Pattern ID and regex cannot be empty.")
        try: re.compile(regex)
        except re.error as e: raise ValueError(f"Invalid regex for '{pattern_id}': {e}")
        self.sensitive_patterns[pattern_id] = {"regex": regex, "description": description}
        self._save_patterns()
        return self.sensitive_patterns[pattern_id]

    def _scan_content(self, content: str) -> Dict[str, Any]:
        if not isinstance(content, str): raise TypeError("Content to scan must be a string.")
        found_sensitive_data = {}
        for pattern_id, pattern_info in self.sensitive_patterns.items():
            matches = re.findall(pattern_info["regex"], content)
            if matches: found_sensitive_data[pattern_id] = matches
        return found_sensitive_data

    def _redact_content(self, content: str, replacement_char: str = "*") -> str:
        if not isinstance(content, str): raise TypeError("Content to redact must be a string.")
        redacted_text = content
        for pattern_id, pattern_info in self.sensitive_patterns.items():
            redacted_text = re.sub(pattern_info["regex"], lambda m: replacement_char * len(m.group(0)), redacted_text)
        return redacted_text

    def _quarantine_file(self, file_path: str, quarantine_dir: str) -> str:
        if not os.path.isabs(file_path): raise ValueError("File path must be an absolute path.")
        if not os.path.exists(file_path) or not os.path.isfile(file_path): raise FileNotFoundError(f"File not found at '{file_path}'.")
        os.makedirs(quarantine_dir, exist_ok=True)
        destination_path = os.path.join(quarantine_dir, os.path.basename(file_path))
        shutil.move(file_path, destination_path)
        return f"File quarantined to '{destination_path}'."

    def _process_file(self, file_path: str, action: str, redact_char: str, quarantine_dir: str) -> Dict[str, Any]:
        if not os.path.isabs(file_path): raise ValueError("File path must be an absolute path.")
        if not os.path.exists(file_path) or not os.path.isfile(file_path): raise FileNotFoundError(f"File not found at '{file_path}'.")

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
        scan_results = self._scan_content(content)
        has_sensitive_data = bool(scan_results)
        
        result: Dict[str, Any] = {"file_path": file_path, "has_sensitive_data": has_sensitive_data, "scan_results": scan_results, "action_performed": action, "status": "completed"}

        if has_sensitive_data:
            if action == "redact":
                redacted_content = self._redact_content(content, redact_char)
                with open(file_path, 'w', encoding='utf-8') as f: f.write(redacted_content)
                result["message"] = f"Sensitive data redacted in '{file_path}'."
            elif action == "quarantine":
                quarantine_message = self._quarantine_file(file_path, quarantine_dir)
                result["message"] = f"File quarantined: {quarantine_message}"
            elif action == "scan":
                result["message"] = "Sensitive data detected. No action taken (scan only)."
            else:
                result["status"] = "failed"; result["message"] = f"Unsupported action '{action}'."
        else:
            result["message"] = "No sensitive data detected."
        return result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_pattern":
            return self._define_pattern(kwargs.get("pattern_id"), kwargs.get("regex"), kwargs.get("description"))
        elif operation == "scan_content":
            return self._scan_content(kwargs.get("content"))
        elif operation == "redact_content":
            return self._redact_content(kwargs.get("content"), kwargs.get("replacement_char", "*"))
        elif operation == "quarantine_file":
            return self._quarantine_file(kwargs.get("file_path"), kwargs.get("quarantine_dir", self.default_quarantine_dir))
        elif operation == "process_file":
            return self._process_file(kwargs.get("file_path"), kwargs.get("action", "scan"), kwargs.get("redact_char", "*"), kwargs.get("quarantine_dir", self.default_quarantine_dir))
        elif operation == "list_patterns":
            return [{"pattern_id": pid, **info} for pid, info in self.sensitive_patterns.items()]
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataLossPreventionTool functionality...")
    tool = DataLossPreventionTool()
    
    sensitive_file = os.path.abspath("sensitive_doc.txt")
    
    try:
        with open(sensitive_file, "w") as f:
            f.write("My credit card is 1234-5678-9012-3456. Email me at test@example.com.")

        print("\n--- Scanning Content ---")
        scan_result = tool.execute(operation="scan_content", content=open(sensitive_file).read())
        print(json.dumps(scan_result, indent=2))

        print("\n--- Processing File (Redact) ---")
        redact_file = os.path.abspath("redact_doc.txt")
        shutil.copy(sensitive_file, redact_file)
        redact_result = tool.execute(operation="process_file", file_path=redact_file, action="redact")
        print(json.dumps(redact_result, indent=2))
        print(f"Redacted content: {open(redact_file).read()}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.patterns_file): os.remove(tool.patterns_file)
        if os.path.exists(tool.default_quarantine_dir): shutil.rmtree(tool.default_quarantine_dir)
        if os.path.exists(sensitive_file): os.remove(sensitive_file)
        if os.path.exists(redact_file): os.remove(redact_file)
        print("\nCleanup complete.")
