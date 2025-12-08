import logging
import json
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for API designs, structured for OpenAPI compatibility
designed_apis: Dict[str, Dict[str, Any]] = {}

def generate_sample_from_schema(schema: Dict[str, Any]) -> Any:
    """Generates a sample data object from a JSON schema."""
    if not isinstance(schema, dict) or "type" not in schema:
        return "Invalid schema: must be a dictionary with a 'type' key."
    
    schema_type = schema["type"]
    if schema_type == "object":
        sample = {}
        if "properties" in schema:
            for key, prop_schema in schema["properties"].items():
                sample[key] = generate_sample_from_schema(prop_schema)
        return sample
    elif schema_type == "array":
        if "items" in schema:
            return [generate_sample_from_schema(schema["items"])]
        else:
            return []
    elif schema_type == "string":
        return schema.get("example", "string_example")
    elif schema_type == "integer":
        return schema.get("example", random.randint(1, 100))  # nosec B311
    elif schema_type == "number":
        return schema.get("example", round(random.uniform(1.0, 100.0), 2))  # nosec B311
    elif schema_type == "boolean":
        return schema.get("example", random.choice([True, False]))  # nosec B311
    else:
        return None

class DefineAPIEndpointTool(BaseTool):
    """Tool to define a new API endpoint for an API design, compatible with OpenAPI."""
    def __init__(self, tool_name="define_api_endpoint"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Defines a new API endpoint with its path, method, and request/response JSON schemas, preparing it for OpenAPI specification generation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_id": {"type": "string", "description": "A unique identifier for the API design (e.g., 'user_service_api')."},
                "path": {"type": "string", "description": "The URL path for the endpoint (e.g., '/users/{id}')."},
                "method": {"type": "string", "description": "The HTTP method (e.g., 'GET', 'POST')."},
                "summary": {"type": "string", "description": "A brief summary of the endpoint's function."},
                "request_schema": {"type": "object", "description": "Optional: A JSON schema for the request body."},
                "response_schema": {"type": "object", "description": "A JSON schema for the 200 OK response body."}
            },
            "required": ["api_id", "path", "method", "summary", "response_schema"]
        }

    def execute(self, api_id: str, path: str, method: str, summary: str, response_schema: Dict[str, Any], request_schema: Dict[str, Any] = None, **kwargs: Any) -> str:
        if api_id not in designed_apis:
            designed_apis[api_id] = {"info": {"title": api_id, "version": "1.0.0"}, "paths": {}}
        
        path_item = designed_apis[api_id]["paths"].get(path, {})
        
        endpoint_def = {
            "summary": summary,
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {"application/json": {"schema": response_schema}}
                }
            }
        }
        if request_schema:
            endpoint_def["requestBody"] = {
                "content": {"application/json": {"schema": request_schema}}
            }
            
        path_item[method.lower()] = endpoint_def
        designed_apis[api_id]["paths"][path] = path_item
        
        report = {
            "message": f"Endpoint '{method.upper()} {path}' added to API '{api_id}'.",
            "api_id": api_id
        }
        return json.dumps(report, indent=2)

class GenerateOpenAPISpecTool(BaseTool):
    """Tool to generate a full OpenAPI 3.0 specification for a designed API."""
    def __init__(self, tool_name="generate_openapi_spec"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a full OpenAPI 3.0 specification in JSON format for all endpoints defined for a given API ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_id": {"type": "string", "description": "The ID of the API to generate the spec for."}
            },
            "required": ["api_id"]
        }

    def execute(self, api_id: str, **kwargs: Any) -> str:
        if api_id not in designed_apis:
            return json.dumps({"error": f"API with ID '{api_id}' not found."}, indent=2)
            
        openapi_spec = {
            "openapi": "3.0.0",
            "info": designed_apis[api_id].get("info", {"title": api_id, "version": "1.0.0"}),
            "paths": designed_apis[api_id].get("paths", {})
        }
        
        return json.dumps(openapi_spec, indent=2)

class ModelAPIRequestResponseTool(BaseTool):
    """Tool to generate sample request and response data from an endpoint's schema."""
    def __init__(self, tool_name="model_api_request_response"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates sample request and response data based on the JSON schemas of a defined API endpoint."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_id": {"type": "string", "description": "The ID of the API design."},
                "path": {"type": "string", "description": "The path of the endpoint."},
                "method": {"type": "string", "description": "The HTTP method of the endpoint."}
            },
            "required": ["api_id", "path", "method"]
        }

    def execute(self, api_id: str, path: str, method: str, **kwargs: Any) -> str:
        if api_id not in designed_apis:
            return json.dumps({"error": f"API with ID '{api_id}' not found."}, indent=2)
        
        endpoint = designed_apis[api_id].get("paths", {}).get(path, {}).get(method.lower())
        if not endpoint:
            return json.dumps({"error": f"Endpoint '{method.upper()} {path}' not found for API '{api_id}'."}, indent=2)
            
        sample_request = "Not applicable for this method."
        if "requestBody" in endpoint:
            request_schema = endpoint["requestBody"]["content"]["application/json"]["schema"]
            sample_request = generate_sample_from_schema(request_schema)

        sample_response = "No response schema defined."
        if "200" in endpoint.get("responses", {}):
            response_schema = endpoint["responses"]["200"]["content"]["application/json"]["schema"]
            sample_response = generate_sample_from_schema(response_schema)
        
        report = {
            "endpoint": f"{method.upper()} {path}",
            "sample_request": sample_request,
            "sample_response": sample_response
        }
        return json.dumps(report, indent=2)