import logging
import os
import json
import random
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class StaticCodeAnalyzerSimulatorTool(BaseTool):
    """
    A tool that simulates static code analysis, identifying potential issues,
    code smells, or security vulnerabilities in code snippets.
    """

    def __init__(self, tool_name: str = "StaticCodeAnalyzerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.reports_file = os.path.join(self.data_dir, "static_analysis_reports.json")
        
        # Analysis reports: {report_id: {code: ..., language: ..., issues: []}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates static code analysis: identifies issues, code smells, or security vulnerabilities."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["analyze_code", "get_analysis_report"]},
                "analysis_id": {"type": "string"},
                "code": {"type": "string", "description": "The code to analyze."},
                "language": {"type": "string", "enum": ["python", "java", "javascript"], "default": "python"},
                "report_id": {"type": "string", "description": "ID of the analysis report to retrieve."}
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
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def analyze_code(self, analysis_id: str, code: str, language: str = "python") -> Dict[str, Any]:
        """Simulates static code analysis for a given code snippet."""
        if analysis_id in self.analysis_reports: raise ValueError(f"Analysis '{analysis_id}' already exists.")
        
        issues = []
        
        # Rule-based issue detection
        if language == "python":
            if "os.system" in code:
                issues.append({"type": "security_vulnerability", "severity": "high", "description": "Potential OS command injection via os.system."})
            if "password =" in code or "api_key =" in code:
                issues.append({"type": "security_vulnerability", "severity": "high", "description": "Hardcoded sensitive information detected."})
            if "def long_function(" in code and len(code.splitlines()) > 50:
                issues.append({"type": "code_smell", "severity": "medium", "description": "Function might be too long."})
            if re.search(r"import \w+ as \w+", code) and random.random() < 0.3:  # nosec B311
                issues.append({"type": "code_smell", "severity": "low", "description": "Unused import alias detected."})
            if "try:" in code and "except:" in code and "except Exception as e:" not in code:
                issues.append({"type": "code_smell", "severity": "medium", "description": "Broad exception catch detected."})
        elif language == "java":
            if "System.out.println" in code and random.random() < 0.2:  # nosec B311
                issues.append({"type": "code_smell", "severity": "low", "description": "Debug print statement found."})
            if "new File(" in code and random.random() < 0.3:  # nosec B311
                issues.append({"type": "security_vulnerability", "severity": "medium", "description": "Potential file path traversal."})
        
        overall_status = "no_issues"
        if any(issue["severity"] == "high" for issue in issues): overall_status = "critical_issues"
        elif issues: overall_status = "issues_found"

        report = {
            "id": analysis_id, "code_snippet": code, "language": language,
            "issues": issues, "overall_status": overall_status,
            "analyzed_at": datetime.now().isoformat()
        }
        self.analysis_reports[analysis_id] = report
        self._save_data()
        return report

    def get_analysis_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated static code analysis report."""
        report = self.analysis_reports.get(report_id)
        if not report: raise ValueError(f"Analysis report '{report_id}' not found.")
        return report

    def execute(self, operation: str, analysis_id: str, **kwargs: Any) -> Any:
        if operation == "analyze_code":
            code = kwargs.get('code')
            if not code:
                raise ValueError("Missing 'code' for 'analyze_code' operation.")
            return self.analyze_code(analysis_id, code, kwargs.get('language', 'python'))
        elif operation == "get_analysis_report":
            # No additional kwargs required for get_analysis_report
            return self.get_analysis_report(analysis_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating StaticCodeAnalyzerSimulatorTool functionality...")
    temp_dir = "temp_static_analysis_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    analyzer_tool = StaticCodeAnalyzerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Analyze a Python code snippet with potential issues
        print("\n--- Analyzing Python code with potential issues ---")
        vulnerable_python_code = """
import os
password = "mysecretpassword"
def execute_command(cmd):
    os.system(cmd)
execute_command("ls -l")
"""
        report1 = analyzer_tool.execute(operation="analyze_code", analysis_id="python_code_001", code=vulnerable_python_code, language="python")
        print(json.dumps(report1, indent=2))

        # 2. Analyze a Java code snippet
        print("\n--- Analyzing Java code ---")
        java_code = """
public class MyClass {
    public static void main(String[] args) {
        System.out.println("Hello World!");
        File f = new File("test.txt");
    }
}
"""
        report2 = analyzer_tool.execute(operation="analyze_code", analysis_id="java_code_001", code=java_code, language="java")
        print(json.dumps(report2, indent=2))

        # 3. Get analysis report
        print(f"\n--- Getting analysis report for '{report1['id']}' ---")
        retrieved_report = analyzer_tool.execute(operation="get_analysis_report", analysis_id=report1["id"])
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")