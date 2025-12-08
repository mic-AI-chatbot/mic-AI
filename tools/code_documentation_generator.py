import logging
import json
import os
import asyncio
from typing import Union, Dict, Any
from mic.llm_loader import get_llm
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class LLMDocGenerator:
    """Manages the LLM instance for documentation generation tasks, using a singleton pattern."""
    _llm = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMDocGenerator, cls).__new__(cls)
            cls._instance._llm = get_llm()
            if cls._instance._llm is None:
                logger.error("LLM not initialized. Documentation generation tools will not be fully functional.")
        return cls._instance

    async def generate_from_stream(self, prompt: str) -> str:
        if self._llm is None:
            return json.dumps({"error": "LLM not available. Please ensure it is configured correctly."})
        
        response_content = []
        try:
            async for chunk in self._llm.stream_response(prompt):
                if chunk.get("type") == "token" and chunk.get("content"):
                    response_content.append(chunk["content"])
                elif chunk.get("type") == "error":
                    logger.error(f"Error from LLM stream: {chunk.get('content')}")
                    return json.dumps({"error": f"Error generating response: {chunk.get('content')}"})
            return "".join(response_content)
        except Exception as e:
            logger.error(f"LLM stream generation failed: {e}")
            return json.dumps({"error": f"LLM stream generation failed: {e}"})

llm_doc_generator_instance = LLMDocGenerator()

class GenerateDocstringsTool(BaseTool):
    """Generates docstrings for functions or classes in a code snippet using an LLM."""
    def __init__(self, tool_name="generate_docstrings"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates docstrings for Python functions or classes within a given code snippet, providing a structured explanation of their purpose, arguments, and return values."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "The Python code snippet for which to generate docstrings."},
                "language": {"type": "string", "description": "The programming language of the code.", "default": "python"}
            },
            "required": ["code_snippet"]
        }

    def execute(self, code_snippet: str, language: str = "python", **kwargs: Any) -> str:
        if language.lower() != "python":
            return json.dumps({"error": "Docstring generation is currently only supported for Python."})

        prompt = f"Generate a comprehensive docstring for the following Python code snippet. The docstring should be in Google Python Style Guide format and include a description, arguments, and what it returns. Provide only the docstring content.\n\n```python\n{code_snippet}\n```\n\nDocstring:"

        try:
            docstring_content = asyncio.run(llm_doc_generator_instance.generate_from_stream(prompt))
            return json.dumps({"code_snippet": code_snippet, "generated_docstring": docstring_content}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error generating docstring: {e}"})

class GenerateInlineCommentsTool(BaseTool):
    """Generates inline comments for complex code sections using an LLM."""
    def __init__(self, tool_name="generate_inline_comments"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates inline comments for complex or critical sections within a code snippet to improve readability and understanding."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_snippet": {"type": "string", "description": "The code snippet for which to generate inline comments."},
                "language": {"type": "string", "description": "The programming language of the code.", "default": "python"}
            },
            "required": ["code_snippet"]
        }

    def execute(self, code_snippet: str, language: str = "python", **kwargs: Any) -> str:
        if language.lower() != "python":
            return json.dumps({"error": "Inline comment generation is currently only supported for Python."})

        prompt = f"Add inline comments to the following Python code snippet to explain complex or important parts of the code. Only add comments where necessary to improve clarity. Provide the commented code.\n\n```python\n{code_snippet}\n```\n\nCommented Code:"

        try:
            commented_code = asyncio.run(llm_doc_generator_instance.generate_from_stream(prompt))
            return json.dumps({"original_code": code_snippet, "commented_code": commented_code}, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Error generating inline comments: {e}"})

class GenerateMarkdownDocsTool(BaseTool):
    """Generates a Markdown documentation file from a code base using an LLM."""
    def __init__(self, tool_name="generate_markdown_docs"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a Markdown documentation file from a specified code base, summarizing its structure and key components."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code_base_path": {"type": "string", "description": "The absolute path to the code base to generate documentation from."},
                "output_file_path": {"type": "string", "description": "The absolute path where the generated Markdown file will be saved."}
            },
            "required": ["code_base_path", "output_file_path"]
        }

    def execute(self, code_base_path: str, output_file_path: str, **kwargs: Any) -> str:
        if not os.path.isabs(code_base_path):
            return json.dumps({"error": "code_base_path must be an absolute path."})
        if not os.path.exists(code_base_path):
            return json.dumps({"error": f"Code base path not found at '{code_base_path}'."})
        if not os.path.isdir(code_base_path):
            return json.dumps({"error": "code_base_path must be a directory."})

        try:
            files_to_document = []
            for item in os.listdir(code_base_path):
                item_path = os.path.join(code_base_path, item)
                if os.path.isfile(item_path) and item.endswith(".py"): # Currently only supports Python files
                    with open(item_path, "r") as f:
                        files_to_document.append({"filename": item, "content": f.read()})

            if not files_to_document:
                return json.dumps({"error": "No Python files found to document in the specified path."})

            prompt = f"Generate a Markdown documentation file for the following Python files:\n\n"
            for file_info in files_to_document:
                prompt += f"**File: {file_info['filename']}**\n\n```python\n{file_info['content']}\n```\n\n"
            
            prompt += "The documentation should include a summary of each file, and details about the classes and functions within them."

            response = asyncio.run(llm_doc_generator_instance.generate_from_stream(prompt))

            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, "w") as f:
                f.write(response)

            return json.dumps({"message": f"Markdown documentation generated and saved to '{os.path.abspath(output_file_path)}'.", "file_path": os.path.abspath(output_file_path)}, indent=2)
        except Exception as e:
            logger.error(f"Error generating Markdown documentation: {e}")
            return json.dumps({"error": f"Error generating Markdown documentation: {e}"})