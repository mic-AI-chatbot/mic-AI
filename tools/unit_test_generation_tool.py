import logging
import ast
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class UnitTestGenerationTool(BaseTool):
    """
    A tool to generate boilerplate unit test files for Python code.
    """
    def __init__(self, tool_name: str = "unit_test_generation_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Generates a boilerplate Python unittest file from a string of source code."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "A string containing the Python code to be tested."},
                "module_name": {
                    "type": "string", 
                    "description": "The name of the module to import from (e.g., 'my_app.utils')."
                }
            },
            "required": ["code", "module_name"]
        }

    def execute(self, code: str, module_name: str, **kwargs) -> Dict:
        """
        Parses Python code and generates a corresponding unittest file content.
        """
        if not code or not module_name:
            return {"error": "'code' and 'module_name' are required."}

        try:
            tree = ast.parse(code)
            test_file_content = self._generate_test_content(tree, module_name)
            return {
                "message": "Unit test boilerplate generated successfully.",
                "test_file_content": test_file_content
            }
        except SyntaxError as e:
            return {"error": f"Invalid Python code provided. Syntax error: {e}"}
        except Exception as e:
            logger.error(f"An error occurred in UnitTestGenerationTool: {e}")
            return {"error": str(e)}

    def _generate_test_content(self, tree: ast.AST, module_name: str) -> str:
        """
        Generates the full content of the test file as a string.
        """
        imports_to_add = set()
        test_classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # It's a standalone function
                class_name = f"Test{self._to_camel_case(node.name)}"
                imports_to_add.add(node.name)
                methods = [self._generate_test_method(node)]
                test_classes.append(self._create_test_class(class_name, methods))
            
            elif isinstance(node, ast.ClassDef):
                # It's a class
                class_name = f"Test{node.name}"
                imports_to_add.add(node.name)
                test_methods = []
                for method_node in node.body:
                    if isinstance(method_node, ast.FunctionDef) and not method_node.name.startswith('_'):
                        test_methods.append(self._generate_test_method(method_node, is_class_method=True, class_name=node.name))
                
                test_classes.append(self._create_test_class(class_name, test_methods, has_setup=True, original_class_name=node.name))

        # Assemble the final file content
        import_statements = f"from {module_name} import {', '.join(sorted(list(imports_to_add)))}"
        
        header = "import unittest\n" + import_statements + "\n\n"
        footer = '\nif __name__ == "__main__":\n    unittest.main()\n'
        
        return header + "\n\n".join(test_classes) + footer

    def _generate_test_method(self, func_node: ast.FunctionDef, is_class_method: bool = False, class_name: str = None) -> str:
        method_name = f"test_{func_node.name}"
        if is_class_method:
            return f"""    def {method_name}(self):
        # Test case for the '{func_node.name}' method of class '{class_name}'
        self.fail("Test not implemented")"""
        else:
            return f"""    def {method_name}(self):
        # Test case for the '{func_node.name}' function
        self.fail("Test not implemented")"""

    def _create_test_class(self, class_name: str, methods: List[str], has_setup: bool = False, original_class_name: str = None) -> str:
        class_def = f"class {class_name}(unittest.TestCase):\n"
        setup_method = ""
        if has_setup:
            setup_method = f"""    def setUp(self):
        # Setup for tests of class {original_class_name}
        # self.instance = {original_class_name}()
        pass\n\n"""
        
        methods_str = "\n\n".join(methods)
        return class_def + setup_method + methods_str

    def _to_camel_case(self, snake_str: str) -> str:
        return "".join(x.capitalize() for x in snake_str.lower().split("_"))
