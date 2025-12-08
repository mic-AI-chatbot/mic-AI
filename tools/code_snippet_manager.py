import json
import os
import logging
import re
from datetime import datetime
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

SNIPPET_FILE_PATH = 'code_snippets.json'

class SnippetManager:
    """Manages code snippets, including loading, saving, and CRUD operations."""
    _instance = None

    def __new__(cls, file_path: str = SNIPPET_FILE_PATH):
        if cls._instance is None:
            cls._instance = super(SnippetManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.snippets: Dict[str, Any] = cls._instance._load_snippets()
        return cls._instance

    def _load_snippets(self) -> Dict[str, Any]:
        """Loads snippets from the JSON file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty snippets.")
                return {}
            except Exception as e:
                logger.error(f"Error loading snippets from {self.file_path}: {e}")
                return {}
        return {}

    def _save_snippets(self) -> None:
        """Saves snippets to the JSON file."""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.snippets, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving snippets to {self.file_path}: {e}")

    def add_snippet(self, name: str, code: str, tags: List[str], language: str, description: str) -> bool:
        if name in self.snippets:
            return False
        self.snippets[name] = {
            "code": code,
            "tags": tags,
            "language": language,
            "description": description,
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z"
        }
        self._save_snippets()
        return True

    def get_snippet(self, name: str) -> Dict[str, Any]:
        return self.snippets.get(name)

    def update_snippet(self, name: str, code: str = None, tags: List[str] = None, language: str = None, description: str = None) -> bool:
        if name not in self.snippets:
            return False
        
        if code is not None: self.snippets[name]["code"] = code
        if tags is not None: self.snippets[name]["tags"] = tags
        if language is not None: self.snippets[name]["language"] = language
        if description is not None: self.snippets[name]["description"] = description
        
        self.snippets[name]["updated_at"] = datetime.now().isoformat() + "Z"
        self._save_snippets()
        return True

    def delete_snippet(self, name: str) -> bool:
        if name in self.snippets:
            del self.snippets[name]
            self._save_snippets()
            return True
        return False

    def list_snippets(self, tags: List[str] = None) -> List[Dict[str, Any]]:
        if not tags:
            return [{"name": name, "tags": details['tags'], "language": details['language'], "description": details['description']} for name, details in self.snippets.items()]
        
        filtered_list = []
        for name, details in self.snippets.items():
            if any(tag in details['tags'] for tag in tags):
                filtered_list.append({"name": name, "tags": details['tags'], "language": details['language'], "description": details['description']})
        return filtered_list

    def search_snippets_by_content(self, query: str) -> List[Dict[str, Any]]:
        found_snippets = []
        try:
            search_pattern = re.compile(query, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern provided: {e}")

        for snip_name, snip_details in self.snippets.items():
            if search_pattern.search(snip_details["code"]):
                found_snippets.append({
                    "name": snip_name,
                    "code_preview": snip_details["code"][:100] + "..." if len(snip_details["code"]) > 100 else snip_details["code"],
                    "tags": snip_details["tags"],
                    "language": snip_details["language"],
                    "description": snip_details["description"]
                })
        return found_snippets

snippet_manager = SnippetManager()

class AddCodeSnippetTool(BaseTool):
    """Adds a new code snippet to the manager."""
    def __init__(self, tool_name="add_code_snippet"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new code snippet to the manager with a unique name, the code content, and optional tags, language, and description."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "A unique name for the code snippet."},
                "code": {"type": "string", "description": "The actual code content of the snippet."},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional: A list of tags for the snippet.", "default": []},
                "language": {"type": "string", "description": "The programming language of the snippet.", "default": "python"},
                "description": {"type": "string", "description": "A brief description of the snippet.", "default": ""}
            },
            "required": ["name", "code"]
        }

    def execute(self, name: str, code: str, tags: List[str] = None, language: str = "python", description: str = "", **kwargs: Any) -> str:
        if tags is None: tags = []
        success = snippet_manager.add_snippet(name, code, tags, language, description)
        if success:
            report = {"message": f"Snippet '{name}' added successfully."}
        else:
            report = {"error": f"Snippet '{name}' already exists. Use 'update_code_snippet' to modify it."}
        return json.dumps(report, indent=2)

class GetCodeSnippetTool(BaseTool):
    """Retrieves a code snippet by name."""
    def __init__(self, tool_name="get_code_snippet"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves a specific code snippet by its unique name."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "The unique name of the code snippet to retrieve."}},
            "required": ["name"]
        }

    def execute(self, name: str, **kwargs: Any) -> str:
        snippet = snippet_manager.get_snippet(name)
        if snippet:
            return json.dumps(snippet, indent=2)
        else:
            return json.dumps({"error": f"Snippet '{name}' not found."})

class UpdateCodeSnippetTool(BaseTool):
    """Updates an existing code snippet."""
    def __init__(self, tool_name="update_code_snippet"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Updates the code content, tags, language, or description of an existing code snippet identified by its name."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the code snippet to update."},
                "code": {"type": "string", "description": "Optional: The new code content for the snippet.", "default": None},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional: New tags for the snippet.", "default": None},
                "language": {"type": "string", "description": "Optional: The new programming language of the snippet.", "default": None},
                "description": {"type": "string", "description": "Optional: A new brief description of the snippet.", "default": None}
            },
            "required": ["name"]
        }

    def execute(self, name: str, code: str = None, tags: List[str] = None, language: str = None, description: str = None, **kwargs: Any) -> str:
        success = snippet_manager.update_snippet(name, code, tags, language, description)
        if success:
            report = {"message": f"Snippet '{name}' updated successfully."}
        else:
            report = {"error": f"Snippet '{name}' not found."}
        return json.dumps(report, indent=2)

class DeleteCodeSnippetTool(BaseTool):
    """Deletes a code snippet."""
    def __init__(self, tool_name="delete_code_snippet"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deletes a code snippet from the manager using its unique name."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "The name of the code snippet to delete."}},
            "required": ["name"]
        }

    def execute(self, name: str, **kwargs: Any) -> str:
        success = snippet_manager.delete_snippet(name)
        if success:
            report = {"message": f"Snippet '{name}' deleted successfully."}
        else:
            report = {"error": f"Snippet '{name}' not found."}
        return json.dumps(report, indent=2)

class ListCodeSnippetsTool(BaseTool):
    """Lists all stored code snippets, optionally filtered by tags."""
    def __init__(self, tool_name="list_code_snippets"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all stored code snippets, optionally filtered by tags, returning their names, tags, language, and description."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional: A list of tags to filter snippets by.", "default": []}
            },
            "required": []
        }

    def execute(self, tags: List[str] = None, **kwargs: Any) -> str:
        if tags is None: tags = []
        snippets = snippet_manager.list_snippets(tags)
        if not snippets:
            return json.dumps({"message": "No snippets found matching the criteria."})
        
        return json.dumps({"total_snippets": len(snippets), "snippets": snippets}, indent=2)

class SearchCodeSnippetsByContentTool(BaseTool):
    """Searches for code snippets based on keywords or patterns within their code content."""
    def __init__(self, tool_name="search_code_snippets_by_content"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Searches for code snippets based on keywords or regex patterns within their code content, returning matching snippets with a code preview."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The keyword or regex pattern to search for within snippet content."}
            },
            "required": ["query"]
        }

    def execute(self, query: str, **kwargs: Any) -> str:
        if not query:
            return json.dumps({"error": "'query' is required for content search."})
        
        found_snippets = snippet_manager.search_snippets_by_content(query)
        if not found_snippets:
            return json.dumps({"message": f"No snippets found matching content query: '{query}'."})
        
        return json.dumps({"total_snippets": len(found_snippets), "snippets": found_snippets}, indent=2)