import logging
import json
import os
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool

# Deferring radon imports to handle cases where it might not be installed
try:
    from radon.visitors import ComplexityVisitor
    from radon.raw import analyze
    from radon.metrics import h_visit
    RADON_AVAILABLE = True
except ImportError:
    ComplexityVisitor = None
    analyze = None
    h_visit = None
    RADON_AVAILABLE = False
    logging.warning("radon library not found. Code complexity analysis tools will not be available. Please install it with 'pip install radon'.")

logger = logging.getLogger(__name__)

class AnalyzePythonCodeComplexityTool(BaseTool):
    """
    Analyzes the complexity of a Python code snippet or file, providing detailed metrics and a summary.
    """
    def __init__(self, tool_name="analyze_python_code_complexity"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes the cyclomatic complexity, Halstead metrics, and raw metrics of a given Python code string or file, providing a detailed report and summary."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_string": {"type": "string", "description": "The Python code string to analyze."},
                "file_path": {"type": "string", "description": "The absolute path to the Python code file to analyze."}
            },
            "required": [] # Either code_string or file_path must be provided
        }

    def execute(self, code_string: str = None, file_path: str = None, **kwargs: Any) -> str:
        if not RADON_AVAILABLE:
            return json.dumps({"error": "The 'radon' library is not installed. Please install it with 'pip install radon'."})
        
        if code_string is None and file_path is None:
            return json.dumps({"error": "Either 'code_string' or 'file_path' must be provided."})

        code = ""
        source_identifier = "code_string"
        if file_path:
            if not os.path.isabs(file_path):
                return json.dumps({"error": "file_path must be an absolute path."})
            if not os.path.exists(file_path):
                return json.dumps({"error": f"File not found at '{file_path}'."})
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                source_identifier = os.path.abspath(file_path)
            except Exception as e:
                return json.dumps({"error": f"Error reading file '{file_path}': {e}"})
        elif code_string:
            code = code_string
        
        if not code.strip():
            return json.dumps({"error": "No code provided for analysis."})

        try:
            # Cyclomatic Complexity
            complexity_results = ComplexityVisitor.from_code(code)
            cc_scores = [{"name": f.name, "complexity": f.complexity, "lineno": f.lineno} for f in complexity_results.functions]
            
            # Raw Metrics
            raw_metrics = analyze(code)
            
            # Halstead Metrics
            halstead_metrics = h_visit(code)

            # Summary and Interpretation
            overall_cc = sum(f.complexity for f in complexity_results.functions) if complexity_results.functions else 0
            cc_assessment = "Low"
            if overall_cc > 50: cc_assessment = "Very High"
            elif overall_cc > 20: cc_assessment = "High"
            elif overall_cc > 10: cc_assessment = "Medium"

            halstead_assessment = "Good"
            if halstead_metrics.bugs > 0.5: halstead_assessment = "Potentially problematic (high estimated bugs)"
            elif halstead_metrics.effort > 10000: halstead_assessment = "High (significant effort required)"

            report = {
                "source": source_identifier,
                "summary": {
                    "overall_cyclomatic_complexity": overall_cc,
                    "complexity_assessment": f"Overall code complexity is {cc_assessment}.",
                    "estimated_halstead_bugs": round(halstead_metrics.bugs, 2),
                    "halstead_assessment": f"Halstead metrics suggest {halstead_assessment} code quality."
                },
                "cyclomatic_complexity_details": cc_scores,
                "raw_metrics": {
                    "loc": raw_metrics.loc,
                    "lloc": raw_metrics.lloc,
                    "sloc": raw_metrics.sloc,
                    "comments": raw_metrics.comments,
                    "multi_line_comments": raw_metrics.multi_line_comments,
                    "blank": raw_metrics.blank
                },
                "halstead_metrics": {
                    "h1_unique_operators": halstead_metrics.h1,
                    "h2_unique_operands": halstead_metrics.h2,
                    "N1_total_operators": halstead_metrics.N1,
                    "N2_total_operands": halstead_metrics.N2,
                    "vocabulary": halstead_metrics.vocabulary,
                    "length": halstead_metrics.length,
                    "calculated_length": halstead_metrics.calculated_length,
                    "volume": halstead_metrics.volume,
                    "difficulty": halstead_metrics.difficulty,
                    "effort": halstead_metrics.effort,
                    "time_to_implement_seconds": halstead_metrics.time,
                    "estimated_bugs": halstead_metrics.bugs
                }
            }
            return json.dumps(report, indent=2)
        except Exception as e:
            logger.error(f"An error occurred during code complexity analysis: {e}")
            return json.dumps({"error": f"An error occurred during code complexity analysis: {e}"})