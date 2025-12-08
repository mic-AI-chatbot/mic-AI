import logging
import json
import os
from typing import Dict, Any
from tools.base_tool import BaseTool

# This tool depends on the 'designed_apis' state from the 'api_design_tool'.
# In a real application, this state would be managed via a shared database or service.
# For this simulation, we will import it directly to demonstrate inter-tool functionality.
try:
    from .api_design_tool import designed_apis
except ImportError:
    # Provide a fallback if the tool is used in isolation.
    designed_apis = {}
    logging.warning("Could not import 'designed_apis' from api_design_tool. Documentation can only be generated for APIs defined in the same session.")


logger = logging.getLogger(__name__)

class GenerateMarkdownFromOpenAPITool(BaseTool):
    """
    Tool to generate Markdown API documentation from a designed API's OpenAPI specification.
    """
    def __init__(self, tool_name="generate_markdown_from_openapi"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a Markdown documentation file from the OpenAPI specification of a designed API."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_id": {"type": "string", "description": "The ID of the API design to generate documentation for."},
                "output_file_path": {"type": "string", "description": "The path to save the generated Markdown file (e.g., 'docs/api_v1.md')."}
            },
            "required": ["api_id", "output_file_path"]
        }

    def _format_schema(self, schema: Dict[str, Any], indent_level: int = 0) -> str:
        """Recursively formats a JSON schema into a readable Markdown string."""
        indent = "  " * indent_level
        md = ""
        if not isinstance(schema, dict):
            return ""

        schema_type = schema.get("type")
        if schema_type == "object" and "properties" in schema:
            for key, prop in schema["properties"].items():
                prop_type = prop.get('type', 'any')
                prop_desc = prop.get('description', '')
                md += f"{indent}- `{key}` (*{prop_type}*): {prop_desc}\n"
                if prop.get("type") == "object":
                    md += self._format_schema(prop, indent_level + 1)
        elif schema_type == "array" and "items" in schema:
            md += f"{indent}*Array of objects with the following properties:*\n"
            md += self._format_schema(schema["items"], indent_level + 1)
        return md

    def execute(self, api_id: str, output_file_path: str, **kwargs: Any) -> str:
        if not designed_apis:
             return json.dumps({"error": "No API designs are available. Please define an API using the 'define_api_endpoint' tool first."})
        if api_id not in designed_apis:
            return json.dumps({"error": f"API with ID '{api_id}' not found in the design tool's state."})

        api_spec = designed_apis[api_id]
        
        markdown_content = f"# API Documentation: {api_spec.get('info', {}).get('title', api_id)}\n\n"
        markdown_content += f"Version: {api_spec.get('info', {}).get('version', 'N/A')}\n\n"
        
        markdown_content += "## Endpoints\n\n"
        for path, path_item in api_spec.get("paths", {}).items():
            for method, endpoint in path_item.items():
                markdown_content += f"### `{method.upper()}` `{path}`\n\n"
                markdown_content += f"**Summary:** {endpoint.get('summary', 'No summary provided.')}\n\n"
                
                if "requestBody" in endpoint:
                    markdown_content += "**Request Body:**\n\n"
                    schema = endpoint["requestBody"]["content"]["application/json"]["schema"]
                    markdown_content += self._format_schema(schema) + "\n"
                    
                markdown_content += "**Responses:**\n\n"
                for status_code, response in endpoint.get("responses", {}).items():
                    markdown_content += f"- **{status_code}:** {response.get('description', '')}\n"
                    if "content" in response:
                        schema = response["content"]["application/json"]["schema"]
                        markdown_content += self._format_schema(schema, indent_level=1) + "\n"
                
                markdown_content += "---\n\n"

        try:
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_file_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            report = {
                "message": f"API documentation successfully generated and saved to '{os.path.abspath(output_file_path)}'.",
            }
        except Exception as e:
            logger.error(f"Failed to write documentation file: {e}")
            report = {"error": f"An error occurred while writing the documentation file: {e}"}
            
        return json.dumps(report, indent=2)