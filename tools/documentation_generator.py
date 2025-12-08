import logging
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DocumentationGeneratorTool(BaseTool):
    """
    A tool for simulating documentation generation for projects.
    """

    def __init__(self, tool_name: str = "documentation_generator"):
        super().__init__(tool_name)
        self.docs_file = "project_docs.json"
        self.generated_docs_dir = "generated_docs"
        self.project_docs: Dict[str, Dict[str, Any]] = self._load_docs()
        os.makedirs(self.generated_docs_dir, exist_ok=True)

    @property
    def description(self) -> str:
        return "Generates and updates project documentation in various formats (Markdown, HTML)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The documentation operation to perform.",
                    "enum": ["generate_docs", "update_docs", "list_docs", "get_doc_details"]
                },
                "project_id": {"type": "string"},
                "project_name": {"type": "string"},
                "content": {"type": "string"},
                "format_type": {"type": "string", "enum": ["markdown", "html"]},
                "output_path": {"type": "string"},
                "new_content": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_docs(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.docs_file):
            with open(self.docs_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted docs file '{self.docs_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_docs(self) -> None:
        with open(self.docs_file, 'w') as f:
            json.dump(self.project_docs, f, indent=4)

    def _get_doc_output_path(self, project_id: str, format_type: str) -> str:
        project_doc_dir = os.path.join(self.generated_docs_dir, project_id)
        os.makedirs(project_doc_dir, exist_ok=True)
        return os.path.join(project_doc_dir, f"documentation.{format_type}")

    def _ensure_dir_exists(self, file_path: str) -> None:
        output_dir = os.path.dirname(file_path)
        if output_dir: os.makedirs(output_dir, exist_ok=True)

    def _generate_docs(self, project_id: str, project_name: str, content: str, format_type: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        if not all([project_id, project_name, content, format_type]):
            raise ValueError("Project ID, name, content, and format type cannot be empty.")
        if format_type not in ["markdown", "html"]: raise ValueError(f"Unsupported format type: '{format_type}'.")

        final_output_path = output_path if output_path else self._get_doc_output_path(project_id, format_type)
        self._ensure_dir_exists(final_output_path)

        generated_content = ""
        if format_type == "markdown": generated_content = f"# {project_name} Documentation\n\n{content}"
        elif format_type == "html":
            generated_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <title>{project_name} Documentation</title>
</head>
<body>
    <h1>{project_name} Documentation</h1>
    <div>{content}</div>
</body>
</html>
"""
        with open(final_output_path, 'w', encoding='utf-8') as f: f.write(generated_content)
        
        new_doc = {
            "project_id": project_id, "project_name": project_name, "format_type": format_type,
            "generated_at": datetime.now().isoformat(), "output_path": os.path.abspath(final_output_path),
            "content_summary": content[:100] + "..."
        }
        self.project_docs[project_id] = new_doc
        self._save_docs()
        return new_doc

    def _update_docs(self, project_id: str, new_content: str) -> Dict[str, Any]:
        doc = self.project_docs.get(project_id)
        if not doc: raise ValueError(f"Documentation for project ID '{project_id}' not found.")
        
        with open(doc["output_path"], 'w', encoding='utf-8') as f:
            if doc["format_type"] == "markdown": f.write(f"# {doc['project_name']} Documentation\n\n{new_content}")
            elif doc["format_type"] == "html":
                f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <title>{doc['project_name']} Documentation</title>
</head>
<body>
    <h1>{doc['project_name']} Documentation</h1>
    <div>{new_content}</div>
</body>
</html>
"""
)
        doc["content_summary"] = new_content[:100] + "..."
        doc["generated_at"] = datetime.now().isoformat()
        self._save_docs()
        return doc

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "generate_docs":
            return self._generate_docs(kwargs.get("project_id"), kwargs.get("project_name"), kwargs.get("content"), kwargs.get("format_type"), kwargs.get("output_path"))
        elif operation == "update_docs":
            return self._update_docs(kwargs.get("project_id"), kwargs.get("new_content"))
        elif operation == "list_docs":
            return list(self.project_docs.values())
        elif operation == "get_doc_details":
            return self.project_docs.get(kwargs.get("project_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DocumentationGeneratorTool functionality...")
    tool = DocumentationGeneratorTool()
    
    output_dir = os.path.abspath("generated_docs")
    
    try:
        os.makedirs(output_dir, exist_ok=True)

        print("\n--- Generating Documentation ---")
        tool.execute(operation="generate_docs", project_id="my_app", project_name="My Application", content="This is the initial documentation.", format_type="markdown")
        
        print("\n--- Updating Documentation ---")
        tool.execute(operation="update_docs", project_id="my_app", new_content="This is the updated documentation with new features.")

        print("\n--- Listing Documentation ---")
        docs = tool.execute(operation="list_docs")
        print(json.dumps(docs, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.docs_file): os.remove(tool.docs_file)
        if os.path.exists(tool.generated_docs_dir): shutil.rmtree(tool.generated_docs_dir)
        print("\nCleanup complete.")