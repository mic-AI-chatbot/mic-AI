
import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class LowCodePlatformTool(BaseTool):
    """
    A tool to simulate a low-code/no-code platform that generates simple HTML
    representations of applications from component definitions.
    """

    def __init__(self, tool_name: str = "LowCodePlatform", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.apps_file = os.path.join(self.data_dir, "lcnc_applications.json")
        self.applications: Dict[str, Dict[str, Any]] = self._load_data(self.apps_file, default={})

    @property
    def description(self) -> str:
        return "Simulates a low-code platform by building simple HTML apps from component definitions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["build_application", "deploy_solution", "list_applications", "get_application_details"]},
                "app_id": {"type": "string"}, "name": {"type": "string"},
                "template_name": {"type": "string", "default": "generic_template"},
                "components": {"type": "array", "items": {"type": "object"}},
                "environment": {"type": "string", "default": "production", "enum": ["development", "staging", "production"]}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_applications(self):
        with open(self.apps_file, 'w') as f: json.dump(self.applications, f, indent=4)

    def _render_component_to_html(self, component: Dict[str, Any]) -> str:
        """Renders a single component definition into an HTML string."""
        comp_type = component.get("type", "div")
        if comp_type == "chart":
            return f"<div style='border:1px solid #ccc; padding:10px; margin:5px;'><b>Chart:</b> {component.get('data_source', 'N/A')}</div>"
        if comp_type == "table":
            return f"<div style='border:1px solid #ccc; padding:10px; margin:5px;'><b>Table:</b> {component.get('data_source', 'N/A')}</div>"
        if comp_type == "button":
            return f"<button style='padding:8px 12px; margin:5px;'>{component.get('label', 'Button')}</button>"
        if comp_type == "header":
            return f"<h{component.get('level', 1)}>{component.get('text', 'Header')}</h{component.get('level', 1)}>"
        return f"<div>Unsupported component: {comp_type}</div>"

    def build_application(self, app_id: str, name: str, template_name: str, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Builds an application by generating an HTML file from its components."""
        if not all([app_id, name, template_name, components]):
            raise ValueError("App ID, name, template, and components are required.")
        if app_id in self.applications:
            raise ValueError(f"Application with ID '{app_id}' already exists.")

        app_dir = os.path.join(self.data_dir, app_id)
        os.makedirs(app_dir, exist_ok=True)
        
        html_body = "\n".join([self._render_component_to_html(c) for c in components])
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <style>body {{ font-family: sans-serif; }}</style>
</head>
<body>
    <h1>{name}</h1>
    {html_body}
</body>
</html>
"""
        output_path = os.path.join(app_dir, "index.html")
        with open(output_path, 'w') as f:
            f.write(html_content)

        new_app = {
            "app_id": app_id, "name": name, "template_name": template_name, "components": components,
            "status": "built", "deployment_history": [], "built_at": datetime.now().isoformat(),
            "artifact_path": output_path
        }
        self.applications[app_id] = new_app
        self._save_applications()
        self.logger.info(f"Application '{name}' ({app_id}) built successfully at '{output_path}'.")
        return new_app

    def deploy_solution(self, app_id: str, environment: str) -> Dict[str, Any]:
        """Simulates deploying the application to an environment."""
        app = self.applications.get(app_id)
        if not app: raise ValueError(f"Application with ID '{app_id}' not found.")
        
        deployment_record = {
            "deployment_id": f"DEPLOY-{app_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "environment": environment, "status": "success", "deployed_at": datetime.now().isoformat()
        }
        app["deployment_history"].append(deployment_record)
        app["status"] = "deployed"
        self._save_applications()
        self.logger.info(f"Application '{app_id}' deployed to '{environment}'.")
        return app

    def list_applications(self, template_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all built applications, with optional filtering."""
        filtered = list(self.applications.values())
        if template_name:
            filtered = [app for app in filtered if app.get("template_name") == template_name]
        return filtered

    def get_application_details(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the full details of a specific application."""
        return self.applications.get(app_id)

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "build_application": self.build_application, "deploy_solution": self.deploy_solution,
            "list_applications": self.list_applications, "get_application_details": self.get_application_details
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating LowCodePlatformTool functionality...")
    temp_dir = "temp_lcnc_data"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    platform_tool = LowCodePlatformTool(data_dir=temp_dir)
    
    try:
        # --- Build an application ---
        print("\n--- Building 'CRM Dashboard' ---")
        app1 = platform_tool.execute(
            operation="build_application", app_id="crm_dashboard", name="CRM Dashboard",
            template_name="Dashboard_template",
            components=[
                {"type": "header", "level": 2, "text": "Sales Overview"},
                {"type": "chart", "data_source": "sales_data_quarterly"},
                {"type": "button", "label": "Refresh Data"}
            ]
        )
        
        # --- Show the generated artifact ---
        artifact_path = app1.get("artifact_path")
        if artifact_path and os.path.exists(artifact_path):
            print(f"\n--- Content of generated '{artifact_path}' ---")
            with open(artifact_path, 'r') as f:
                print(f.read())
        
        # --- Deploy the application ---
        print("\n--- Deploying 'crm_dashboard' to production ---")
        deployed_app = platform_tool.execute(operation="deploy_solution", app_id="crm_dashboard", environment="production")
        print(f"Deployment history count: {len(deployed_app['deployment_history'])}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        import shutil
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
