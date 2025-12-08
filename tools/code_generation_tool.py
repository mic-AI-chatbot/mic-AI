import logging
import json
import os
import re # Import re for extracting code blocks
from typing import Dict, Any, List
from tools.base_tool import BaseTool
from mic.llm_loader import get_llm # Import the shared LLM instance

logger = logging.getLogger(__name__)

class LLMCodeAssistant:
    """Manages the LLM instance for code generation and manipulation tasks, using a singleton pattern."""
    _llm = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMCodeAssistant, cls).__new__(cls)
            cls._instance._llm = get_llm()
            if cls._instance._llm is None:
                logger.error("LLM not initialized. Code generation tools will not be fully functional.")
        return cls._instance

    def generate_response(self, prompt: str) -> str:
        if self._llm is None:
            return json.dumps({"error": "LLM not available. Please ensure it is configured correctly."})
        try:
            return self._llm.generate_response(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return json.dumps({"error": f"LLM generation failed: {e}"})

llm_code_assistant_instance = LLMCodeAssistant()

class GenerateCodeTool(BaseTool):
    """Generates code in a specified language based on a prompt using an LLM."""
    def __init__(self, tool_name="generate_code"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates code in a specified programming language based on a prompt, optionally using provided libraries and context. Returns the generated code within a JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The natural language prompt describing the code to generate."},
                "language": {"type": "string", "description": "The programming language for the generated code (e.g., 'python', 'javascript').", "default": "python"},
                "libraries": {"type": "array", "items": {"type": "string"}, "description": "Optional: A list of libraries to use in the generated code.", "default": []},
                "context": {"type": "string", "description": "Optional: Additional code or text context to guide the generation.", "default": None}
            },
            "required": ["prompt"]
        }

    def execute(self, prompt: str, language: str = "python", libraries: List[str] = None, context: str = None, **kwargs: Any) -> str:
        context_prompt = ""
        if context:
            context_prompt = f"Use the following code as context:\n\n```\n{context}\n```\n"

        library_prompt = ""
        if libraries:
            library_prompt = f" Use the following libraries: {', '.join(libraries)}."

        system_prompt = f"You are a code generation assistant. Generate only the requested {language} code.{library_prompt} Do not include explanations, comments, or extra text outside the code block. Provide the generated code in a code block."
        
        full_prompt = f"{system_prompt}\n\n{context_prompt}User: {prompt}\nAssistant:"
        llm_response = llm_code_assistant_instance.generate_response(full_prompt)
        
        # Extract code block from LLM response
        code_match = re.search(r"```(?:\w+)?\n(.*?)```", llm_response, re.DOTALL)
        generated_code = code_match.group(1).strip() if code_match else llm_response.strip()

        return json.dumps({"prompt": prompt, "generated_code": generated_code}, indent=2)

class GenerateUnitTestTool(BaseTool):
    """Generates a unit test for a given piece of code using an LLM."""
    def __init__(self, tool_name="generate_unit_test"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a unit test for a given code snippet in a specified language and testing framework. Returns the generated test code within a JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The code for which to generate a unit test."},
                "language": {"type": "string", "description": "The programming language of the code (e.g., 'python', 'javascript').", "default": "python"}
            },
            "required": ["code"]
        }

    def execute(self, code: str, language: str = "python", **kwargs: Any) -> str:
        framework = "unittest"
        if language.lower() == "javascript":
            framework = "Jest"

        system_prompt = f"You are a unit test generation assistant. Generate a unit test for the following {language} code using the {framework} framework. Provide only the test code in a code block."
        
        full_prompt = f"{system_prompt}\n\nCode:\n\n```\n{code}\n```\n\nTest:"
        llm_response = llm_code_assistant_instance.generate_response(full_prompt)
        
        code_match = re.search(r"```(?:\w+)?\n(.*?)```", llm_response, re.DOTALL)
        generated_test_code = code_match.group(1).strip() if code_match else llm_response.strip()

        return json.dumps({"code": code, "generated_test_code": generated_test_code}, indent=2)

class ExplainCodeTool(BaseTool):
    """Explains a given code snippet in natural language using an LLM."""
    def __init__(self, tool_name="explain_code"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Explains a given code snippet in natural language, detailing its functionality, logic, and purpose. Returns the explanation within a JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "The code snippet to explain."}},
            "required": ["code"]
        }

    def execute(self, code: str, **kwargs: Any) -> str:
        system_prompt = "You are a code explanation assistant. Explain the user's code clearly and concisely."
        full_prompt = f"{system_prompt}\n\nUser: Explain the following code:\n\n```\n{code}\n```\nAssistant:"
        llm_response = llm_code_assistant_instance.generate_response(full_prompt)
        
        return json.dumps({"code": code, "explanation": llm_response.strip()}, indent=2)

class RefactorCodeTool(BaseTool):
    """Refactors a given code snippet based on a specified goal using an LLM."""
    def __init__(self, tool_name="refactor_code"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Refactors a given code snippet based on a specified goal (e.g., 'improve readability', 'optimize performance'), using an LLM. Returns the refactored code within a JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The code snippet to refactor."},
                "goal": {"type": "string", "description": "The goal for refactoring (e.g., 'improve readability', 'optimize performance', 'reduce complexity').", "default": "improve readability"}
            },
            "required": ["code"]
        }

    def execute(self, code: str, goal: str = "improve readability", **kwargs: Any) -> str:
        system_prompt = "You are a code refactoring assistant. Refactor the user's code based on their goal. Provide only the refactored code in a code block."
        full_prompt = f"{system_prompt}\n\nUser: Refactor the following code to {goal}:\n\n```\n{code}\n```\nAssistant:"
        llm_response = llm_code_assistant_instance.generate_response(full_prompt)
        
        code_match = re.search(r"```(?:\w+)?\n(.*?)```", llm_response, re.DOTALL)
        refactored_code = code_match.group(1).strip() if code_match else llm_response.strip()

        return json.dumps({"original_code": code, "refactoring_goal": goal, "refactored_code": refactored_code}, indent=2)

class GenerateCodeDocumentationTool(BaseTool):
    """Generates documentation for a given piece of code using an LLM."""
    def __init__(self, tool_name="generate_code_documentation"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates documentation for a given code snippet in a specified programming language, detailing its functionality and usage. Returns the generated documentation within a JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The code snippet for which to generate documentation."},
                "language": {"type": "string", "description": "The programming language of the code (e.g., 'python', 'java').", "default": "python"}
            },
            "required": ["code"]
        }

    def execute(self, code: str, language: str = "python", **kwargs: Any) -> str:
        system_prompt = f"You are a documentation generation assistant. Generate documentation for the following {language} code. Provide only the documentation."
        
        full_prompt = f"{system_prompt}\n\nCode:\n\n```\n{code}\n```\n\nDocumentation:"
        llm_response = llm_code_assistant_instance.generate_response(full_prompt)
        
        return json.dumps({"code": code, "generated_documentation": llm_response.strip()}, indent=2)