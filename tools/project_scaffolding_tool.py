import logging
import os
import json
from typing import Union, List, Dict, Any, Optional

from tools.base_tool import BaseTool
from cookiecutter.main import cookiecutter

logger = logging.getLogger(__name__)

class ProjectScaffoldingTool(BaseTool):
    """
    A tool for generating projects from templates using Cookiecutter,
    allowing for project creation, template listing, and validation.
    """

    def __init__(self, tool_name: str = "ProjectScaffolding", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates projects from templates using Cookiecutter: create, list, and validate templates."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_project", "list_templates", "validate_template"]},
                "template_url": {"type": "string", "description": "URL or local path to the Cookiecutter template."},
                "output_dir": {"type": "string", "description": "Absolute path to the output directory for the new project.", "default": "."},
                "no_input": {"type": "boolean", "description": "If true, do not prompt for parameters and use defaults.", "default": False},
                "extra_context": {"type": "object", "description": "Extra context to pass to the template (key-value pairs)."},
                "source_path": {"type": "string", "description": "Absolute path to a local directory containing templates (for 'list_templates')."}
            },
            "required": ["operation"]
        }

    def _generate_project(self, template_url: str, output_dir: str = ".", no_input: bool = False, extra_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates a project from a Cookiecutter template."""
        if not template_url: raise ValueError("'template_url' is required.")
        if not os.path.isabs(output_dir): output_dir = os.path.abspath(output_dir)

        try:
            cookiecutter(
                template_url,
                output_dir=output_dir,
                no_input=no_input,
                extra_context=extra_context
            )
            return {"status": "success", "message": f"Successfully generated project from template '{template_url}' in '{output_dir}'."}
        except Exception as e:
            raise Exception(f"An error occurred during project generation: {e}")

    def _list_templates(self, source_path: str) -> List[str]:
        """Lists available templates from a given local source path."""
        if not os.path.isdir(source_path): raise ValueError(f"Source path '{source_path}' is not a valid directory.")
        
        templates = []
        for item in os.listdir(source_path):
            item_path = os.path.join(source_path, item)
            if os.path.isdir(item_path) and "cookiecutter.json" in os.listdir(item_path):
                templates.append(item)
        return templates

    def _validate_template(self, template_url: str) -> Dict[str, Any]:
        """Validates a Cookiecutter template by attempting to load its cookiecutter.json."""
        try:
            if os.path.isdir(template_url) and "cookiecutter.json" in os.listdir(template_url):
                with open(os.path.join(template_url, "cookiecutter.json"), 'r') as f:
                    json.load(f) # Just try to load it to check if it's valid JSON
                return {"status": "success", "message": f"Template '{template_url}' appears to be valid."}
            elif template_url.startswith(("http://", "https://", "git@")):
                return {"status": "info", "message": f"Template '{template_url}' is a remote template. Basic URL check passed. Full validation occurs during generation."}
            else:
                raise ValueError(f"Invalid template URL or path: {template_url}")
        except Exception as e:
            raise Exception(f"Template validation failed: {e}")

    def execute(self, operation: str, **kwargs: Any) -> Any:
        try:
            if operation == "generate_project":
                template_url = kwargs.get('template_url')
                if not template_url:
                    raise ValueError("Missing 'template_url' for 'generate_project' operation.")
                return self._generate_project(template_url, kwargs.get('output_dir', '.'), kwargs.get('no_input', False), kwargs.get('extra_context'))
            elif operation == "list_templates":
                source_path = kwargs.get('source_path')
                if not source_path:
                    raise ValueError("Missing 'source_path' for 'list_templates' operation.")
                return self._list_templates(source_path)
            elif operation == "validate_template":
                template_url = kwargs.get('template_url')
                if not template_url:
                    raise ValueError("Missing 'template_url' for 'validate_template' operation.")
                return self._validate_template(template_url)
            else:
                raise ValueError(f"Invalid operation '{operation}'.")
        except Exception as e:
            self.logger.error(f"An error occurred during project scaffolding: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    print("Demonstrating ProjectScaffoldingTool functionality...")
    temp_dir = "temp_scaffolding_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    scaffolding_tool = ProjectScaffoldingTool()
    
    # Create a dummy template directory for local testing
    dummy_template_path = os.path.join(temp_dir, "my_dummy_template")
    os.makedirs(dummy_template_path, exist_ok=True)
    with open(os.path.join(dummy_template_path, "cookiecutter.json"), 'w') as f:
        json.dump({"project_name": "My Project", "repo_name": "{{ cookiecutter.project_name.lower().replace(' ', '_') }}"}, f)
    os.makedirs(os.path.join(dummy_template_path, "{{cookiecutter.repo_name}}"), exist_ok=True)
    with open(os.path.join(dummy_template_path, "{{cookiecutter.repo_name}}", "README.md"), 'w') as f:
        f.write("# {{cookiecutter.project_name}}")
    print(f"Dummy template created at: {dummy_template_path}")

    try:
        # 1. Generate a project from the dummy template
        print("\n--- Generating project from dummy template ---")
        output_project_dir = os.path.join(temp_dir, "my_new_project")
        generate_result = scaffolding_tool.execute(operation="generate_project", template_url=dummy_template_path, output_dir=output_project_dir, no_input=True, extra_context={"project_name": "Test Project"})
        print(json.dumps(generate_result, indent=2))

        # 2. List templates from the dummy template directory
        print("\n--- Listing templates from dummy directory ---")
        list_result = scaffolding_tool.execute(operation="list_templates", source_path=temp_dir)
        print(json.dumps(list_result, indent=2))

        # 3. Validate the dummy template
        print("\n--- Validating the dummy template ---")
        validate_result = scaffolding_tool.execute(operation="validate_template", template_url=dummy_template_path)
        print(json.dumps(validate_result, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")