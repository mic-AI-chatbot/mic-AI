
import logging
import os
import json
import random
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class StaticCodeSecurityAnalyzerTool(BaseTool):
    """
    A tool that simulates static code security analysis, identifying potential
    security vulnerabilities in code snippets based on predefined patterns.
    """

    def __init__(self, tool_name: str = "StaticCodeSecurityAnalyzer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.reports_file = os.path.join(self.data_dir, "security_analysis_reports.json")
        
        # Analysis reports: {report_id: {code: ..., language: ..., vulnerabilities: []}}
        self.security_analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates static code security analysis: identifies vulnerabilities in code snippets."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["analyze_code_for_security", "get_security_report"]},
                "analysis_id": {"type": "string"},
                "code": {"type": "string", "description": "The code to analyze for security vulnerabilities."},
                "language": {"type": "string", "enum": ["python", "java", "javascript"], "default": "python"},
                "report_id": {"type": "string", "description": "ID of the security analysis report to retrieve."}
            },
            "required": ["operation", "analysis_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.reports_file, 'w') as f: json.dump(self.security_analysis_reports, f, indent=2)

    def analyze_code_for_security(self, analysis_id: str, code: str, language: str = "python") -> Dict[str, Any]:
        """Simulates static code security analysis for a given code snippet."""
        if analysis_id in self.security_analysis_reports: raise ValueError(f"Analysis '{analysis_id}' already exists.")
        
        vulnerabilities = []
        
        # Rule-based vulnerability detection
        if language == "python":
            if "os.system(" in code or "subprocess.call(" in code and "shell=True" in code:
                vulnerabilities.append({"type": "OS Command Injection", "severity": "critical", "description": "Direct use of os.system or shell=True in subprocess.call can lead to command injection."})
            if re.search(r"password\s*=\s*['\"].*?['\"]", code) or re.search(r"api_key\s*=\s*['\"].*?['\"]", code):
                vulnerabilities.append({"type": "Hardcoded Credentials", "severity": "high", "description": "Sensitive information (password/API key) found hardcoded in the code."})
            if "pickle.load(" in code:
                vulnerabilities.append({"type": "Insecure Deserialization", "severity": "high", "description": "Deserializing untrusted data with pickle can lead to arbitrary code execution."})
            if "eval(" in code:
                vulnerabilities.append({"type": "Code Injection (eval)", "severity": "high", "description": "Use of eval() with untrusted input can lead to code injection."})
        elif language == "java":
            if "new ProcessBuilder(" in code and random.random() < 0.3:  # nosec B311
                vulnerabilities.append({"type": "OS Command Injection", "severity": "high", "description": "Potential OS command injection via ProcessBuilder."})
            if "System.getenv(" in code and random.random() < 0.2:  # nosec B311
                vulnerabilities.append({"type": "Information Disclosure", "severity": "medium", "description": "Accessing environment variables directly might expose sensitive info."})
        elif language == "javascript":
            if "innerHTML" in code and random.random() < 0.4:  # nosec B311
                vulnerabilities.append({"type": "Cross-Site Scripting (XSS)", "severity": "high", "description": "Direct assignment to innerHTML can lead to XSS if input is not sanitized."})
            if "eval(" in code:
                vulnerabilities.append({"type": "Code Injection (eval)", "severity": "high", "description": "Use of eval() with untrusted input can lead to code injection."})
        
        overall_status = "secure"
        if any(vuln["severity"] == "critical" for vuln in vulnerabilities): overall_status = "critical_vulnerabilities"
        elif vulnerabilities: overall_status = "vulnerabilities_found"

        report = {
            "id": analysis_id, "code_snippet": code, "language": language,
            "vulnerabilities": vulnerabilities, "overall_status": overall_status,
            "analyzed_at": datetime.now().isoformat()
        }
        self.security_analysis_reports[analysis_id] = report
        self._save_data()
        return report

    def get_security_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated static code security analysis report."""
        report = self.security_analysis_reports.get(report_id)
        if not report: raise ValueError(f"Security analysis report '{report_id}' not found.")
        return report

    def execute(self, operation: str, analysis_id: str, **kwargs: Any) -> Any:
        if operation == "analyze_code_for_security":
            return self.analyze_code_for_security(analysis_id, kwargs['code'], kwargs.get('language', 'python'))
        elif operation == "get_security_report":
            return self.get_security_report(analysis_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating StaticCodeSecurityAnalyzerTool functionality...")
    temp_dir = "temp_static_security_analysis_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    security_analyzer = StaticCodeSecurityAnalyzerTool(data_dir=temp_dir)
    
    try:
        # 1. Analyze Python code with OS command injection
        print("\n--- Analyzing Python code with OS command injection ---")
        code1 = """
import os
user_input = "ls -l"
os.system(user_input)
"""
        report1 = security_analyzer.execute(operation="analyze_code_for_security", analysis_id="py_vuln_001", code=code1, language="python")
        print(json.dumps(report1, indent=2))

        # 2. Analyze Python code with hardcoded API key
        print("\n--- Analyzing Python code with hardcoded API key ---")
        code2 = """
api_key = "sk_live_xxxxxxxxxxxxxxxxxxxx"
def make_api_call():
    pass
"""
        report2 = security_analyzer.execute(operation="analyze_code_for_security", analysis_id="py_vuln_002", code=code2, language="python")
        print(json.dumps(report2, indent=2))

        # 3. Analyze JavaScript code with XSS vulnerability
        print("\n--- Analyzing JavaScript code with XSS vulnerability ---")
        code3 = """
document.getElementById("output").innerHTML = user_input;
"""
        report3 = security_analyzer.execute(operation="analyze_code_for_security", analysis_id="js_vuln_001", code=code3, language="javascript")
        print(json.dumps(report3, indent=2))

        # 4. Get security report
        print(f"\n--- Getting security report for '{report1['id']}' ---")
        retrieved_report = security_analyzer.execute(operation="get_security_report", analysis_id=report1["id"])
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
