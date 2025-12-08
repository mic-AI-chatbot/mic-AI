import logging
import json
import requests
from typing import List, Dict, Any
from tools.base_tool import BaseTool

try:
    from jsonpath_ng import parse
    JSONPATH_AVAILABLE = True
except ImportError:
    JSONPATH_AVAILABLE = False
    logging.warning("jsonpath-ng library not found. JSONPath validation will not be available. Please install it with 'pip install jsonpath-ng'.")

logger = logging.getLogger(__name__)

class SendAPIRequestTool(BaseTool):
    """
    Tool to send an HTTP request to an API endpoint.
    """
    def __init__(self, tool_name="send_api_request"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Sends an HTTP request (GET, POST, PUT, DELETE) to a specified API endpoint and returns the full response as a JSON string."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the API endpoint."},
                "method": {"type": "string", "description": "The HTTP method.", "default": "GET"},
                "headers": {"type": "object", "description": "Optional HTTP headers."},
                "params": {"type": "object", "description": "Optional query parameters."},
                "data": {"type": "object", "description": "Optional form data for POST/PUT."},
                "json_payload": {"type": "object", "description": "Optional JSON payload for POST/PUT."}
            },
            "required": ["url"]
        }

    def execute(self, url: str, method: str = "GET", headers: dict = None, params: dict = None, data: dict = None, json_payload: dict = None, **kwargs: Any) -> str:
        try:
            response = requests.request(method.upper(), url, headers=headers, params=params, data=data, json=json_payload)
            
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }
            try:
                response_data["body"] = response.json()
            except json.JSONDecodeError:
                response_data["body"] = response.text

            return json.dumps(response_data)
        except requests.exceptions.RequestException as e:
            return json.dumps({"error": f"API request failed: {e}"})

class ValidateAPIResponseTool(BaseTool):
    """
    Tool to validate an API response against expected criteria using JSONPath.
    """
    def __init__(self, tool_name="validate_api_response"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Validates an API response against criteria like status code, headers, and body content using JSONPath for complex validation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "response_json": {"type": "string", "description": "The JSON string of the API response from SendAPIRequestTool."},
                "validations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["status_code", "header_equals", "body_contains", "jsonpath_equals"]},
                            "expected": {"type": "any", "description": "The expected value."},
                            "path_or_key": {"type": "string", "description": "The header key or JSONPath expression."}
                        },
                        "required": ["type", "expected"]
                    },
                    "description": "A list of validation checks to perform."
                }
            },
            "required": ["response_json", "validations"]
        }

    def execute(self, response_json: str, validations: List[Dict[str, Any]], **kwargs: Any) -> str:
        try:
            response = json.loads(response_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for the response."})

        results = []
        for val in validations:
            val_type = val["type"]
            expected = val["expected"]
            path_or_key = val.get("path_or_key")
            
            success = False
            actual = "N/A"
            
            try:
                if val_type == "status_code":
                    actual = response.get("status_code")
                    success = actual == expected
                elif val_type == "header_equals":
                    actual = response.get("headers", {}).get(path_or_key)
                    success = actual == expected
                elif val_type == "body_contains":
                    body_str = json.dumps(response.get("body", ""))
                    actual = body_str
                    success = str(expected) in body_str
                elif val_type == "jsonpath_equals":
                    if not JSONPATH_AVAILABLE:
                        raise ModuleNotFoundError("jsonpath-ng is not installed.")
                    jsonpath_expr = parse(path_or_key)
                    matches = [match.value for match in jsonpath_expr.find(response.get("body"))]
                    if matches:
                        actual = matches[0]
                        success = str(actual) == str(expected)
                    else:
                        actual = "No match found"
                        success = False
            except Exception as e:
                logger.error(f"Validation of type '{val_type}' failed: {e}")
                success = False
                actual = f"Error: {e}"

            results.append({"check": val_type, "path_or_key": path_or_key, "expected": expected, "actual": actual, "success": success})
            
        overall_success = all(r["success"] for r in results)
        
        return json.dumps({"overall_success": overall_success, "results": results}, indent=2)

class RunAPITestScenarioTool(BaseTool):
    """Tool to run a sequence of API tests as a scenario."""
    def __init__(self, tool_name="run_api_test_scenario"):
        super().__init__(tool_name=tool_name)
        self.request_tool = SendAPIRequestTool()
        self.validation_tool = ValidateAPIResponseTool()

    @property
    def description(self) -> str:
        return "Runs a sequence of API test steps, where each step involves sending a request and validating the response. The scenario stops on the first failure."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scenario_name": {"type": "string", "description": "A descriptive name for the test scenario."},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "step_name": {"type": "string"},
                            "request": {"type": "object", "description": "The request parameters for SendAPIRequestTool."},
                            "validations": {"type": "array", "description": "The validation rules for ValidateAPIResponseTool."}
                        },
                        "required": ["step_name", "request", "validations"]
                    }
                }
            },
            "required": ["scenario_name", "steps"]
        }

    def execute(self, scenario_name: str, steps: List[Dict[str, Any]], **kwargs: Any) -> str:
        scenario_results = []
        for i, step in enumerate(steps):
            step_name = step["step_name"]
            logger.info(f"Executing step {i+1}/{len(steps)}: {step_name}")
            
            response_json = self.request_tool.execute(**step["request"])
            validation_report_json = self.validation_tool.execute(response_json, step["validations"])
            validation_report = json.loads(validation_report_json)
            
            step_result = {
                "step_name": step_name,
                "request": step["request"],
                "response": json.loads(response_json),
                "validation_report": validation_report
            }
            scenario_results.append(step_result)
            
            if not validation_report["overall_success"]:
                logger.warning(f"Step '{step_name}' failed. Halting scenario.")
                break

        overall_success = all(r["validation_report"]["overall_success"] for r in scenario_results)
        
        final_report = {
            "scenario_name": scenario_name,
            "overall_success": overall_success,
            "steps_executed": len(scenario_results),
            "results": scenario_results
        }
        return json.dumps(final_report, indent=2)