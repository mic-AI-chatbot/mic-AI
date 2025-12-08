import logging
import json
import os
import re
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logging.warning("googletrans library not found. Translation functionality will not be available. Please install it with 'pip install googletrans==4.0.0-rc1'.")

logger = logging.getLogger(__name__)

def generate_mock_code_snippet() -> str:
    """Generates a mock code snippet with translatable strings for demonstration."""
    return """
    // JavaScript example
    function renderPage() {
        const title = "Welcome to our App";
        const greeting = "Hello, user!";
        console.log(title);
        document.getElementById("header").innerText = greeting;
        const message = `You have ${count} new messages.`;
        // This is a comment, not translatable.
        const buttonText = "Click here to proceed";
    }

    # Python example
    def get_message():
        return "This is a Python message."

    # HTML example
    <p>This is a paragraph.</p>
    """

class ExtractTranslatableStringsTool(BaseTool):
    """Extracts potential translatable strings from code content."""
    def __init__(self, tool_name="extract_translatable_strings"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Extracts potential translatable strings from a given code snippet or file content using regex patterns."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"code_content": {"type": "string", "description": "The content of the code file to analyze."}},
            "required": ["code_content"]
        }

    def execute(self, code_content: str, **kwargs: Any) -> str:
        # Regex to find strings in double or single quotes, excluding comments
        # This is a simplified approach and might not catch all cases or might catch non-translatable strings.
        # It tries to ignore strings within comments (// or #)
        
        # Remove single-line comments first to avoid matching strings inside them
        cleaned_content = re.sub(r'//.*', '', code_content)
        cleaned_content = re.sub(r'#.*', '', cleaned_content)

        # Find strings in double or single quotes
        strings = re.findall(r'["\'](.*?)["\']', cleaned_content)
        
        # Filter out empty strings, very short strings, or strings that look like variable names/paths
        translatable_strings = list(set([s for s in strings if s and len(s) > 3 and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_/\.]*$', s)]))
        
        report = {
            "message": f"Found {len(translatable_strings)} potential translatable strings.",
            "translatable_strings": translatable_strings
        }
        return json.dumps(report, indent=2)

class TranslateStringsTool(BaseTool):
    """Translates a list of strings into a target language using Google Translate."""
    def __init__(self, tool_name="translate_strings"):
        super().__init__(tool_name=tool_name)
        self.translator = None
        if GOOGLETRANS_AVAILABLE:
            try:
                self.translator = Translator()
            except Exception as e:
                logger.error(f"Failed to initialize googletrans Translator: {e}")

    @property
    def description(self) -> str:
        return "Translates a list of strings into a specified target language using Google Translate."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "strings_to_translate": {"type": "array", "items": {"type": "string"}, "description": "A list of strings to translate."},
                "target_language": {"type": "string", "description": "The target language code (e.g., 'es' for Spanish, 'fr' for French)."}
            },
            "required": ["strings_to_translate", "target_language"]
        }

    def execute(self, strings_to_translate: List[str], target_language: str, **kwargs: Any) -> str:
        if not self.translator:
            return json.dumps({"error": "Translation service not available. Please ensure 'googletrans' is installed and initialized correctly."})

        translated_strings = {}
        for original_string in strings_to_translate:
            try:
                translation = self.translator.translate(original_string, dest=target_language)
                translated_strings[original_string] = translation.text
            except Exception as e:
                logger.error(f"Translation failed for '{original_string}': {e}")
                translated_strings[original_string] = f"ERROR: {e}"
        
        report = {
            "target_language": target_language,
            "translated_strings": translated_strings
        }
        return json.dumps(report, indent=2)

class GenerateLanguageResourceFileTool(BaseTool):
    """Generates a language-specific JSON resource file."""
    def __init__(self, tool_name="generate_language_resource_file"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a language-specific JSON resource file from a dictionary of translated strings."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "translated_strings_json": {"type": "string", "description": "JSON string of translated strings (original:translated key-value pairs)."},
                "language_code": {"type": "string", "description": "The language code for the resource file (e.g., 'es', 'fr')."},
                "output_path": {"type": "string", "description": "The absolute path to save the JSON resource file (e.g., 'locales/es.json')."}
            },
            "required": ["translated_strings_json", "language_code", "output_path"]
        }

    def execute(self, translated_strings_json: str, language_code: str, output_path: str, **kwargs: Any) -> str:
        try:
            translated_strings = json.loads(translated_strings_json)
            if not isinstance(translated_strings, dict):
                raise ValueError("Expected a JSON object for translated_strings.")
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for translated_strings."})
        except ValueError as e:
            return json.dumps({"error": str(e)})

        resource_content = {
            "language_code": language_code,
            "translations": translated_strings
        }
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(resource_content, f, ensure_ascii=False, indent=2)
            
            return json.dumps({"message": f"Language resource file for '{language_code}' generated and saved to '{os.path.abspath(output_path)}'."})
        except Exception as e:
            logger.error(f"Failed to generate language resource file: {e}")
            return json.dumps({"error": f"An error occurred during file generation: {e}"})
