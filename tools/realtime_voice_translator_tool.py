
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simple rule-based translation dictionary
TRANSLATION_RULES = {
    "en": {
        "hello": {"es": "Hola", "fr": "Bonjour", "de": "Hallo"},
        "how are you?": {"es": "¿Cómo estás?", "fr": "Comment allez-vous?", "de": "Wie geht es dir?"},
        "thank you": {"es": "Gracias", "fr": "Merci", "de": "Danke schön"},
        "goodbye": {"es": "Adiós", "fr": "Au revoir", "de": "Auf Wiedersehen"}
    }
}

class RealtimeVoiceTranslatorSimulatorTool(BaseTool):
    """
    A tool that simulates a real-time voice translator, translating text input
    between specified source and target languages using rule-based translations.
    """

    def __init__(self, tool_name: str = "RealtimeVoiceTranslatorSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.logs_file = os.path.join(self.data_dir, "translation_logs.json")
        
        # Translation logs: [{timestamp: ..., source_text: ..., translated_text: ..., source_language: ..., target_language: ...}]
        self.translation_logs: List[Dict[str, Any]] = self._load_data(self.logs_file, default=[])

    @property
    def description(self) -> str:
        return "Simulates real-time voice translation: translates text input between source and target languages."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["translate_voice_input", "get_translation_history"]},
                "text_input": {"type": "string", "description": "The text input simulating transcribed voice."},
                "source_language": {"type": "string", "enum": ["en", "es", "fr", "de"], "default": "en"},
                "target_language": {"type": "string", "enum": ["en", "es", "fr", "de"], "default": "es"}
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

    def _save_data(self):
        with open(self.logs_file, 'w') as f: json.dump(self.translation_logs, f, indent=2)

    def translate_voice_input(self, text_input: str, source_language: str = "en", target_language: str = "es") -> Dict[str, Any]:
        """Simulates translating text input between specified languages."""
        translated_text = ""
        
        if source_language == target_language:
            translated_text = text_input
        elif source_language in TRANSLATION_RULES and text_input.lower() in TRANSLATION_RULES[source_language]:
            translated_text = TRANSLATION_RULES[source_language][text_input.lower()].get(target_language, f"Simulated: No direct translation for '{text_input}' to '{target_language}'.")
        else:
            translated_text = f"Simulated: Translated '{text_input}' from '{source_language}' to '{target_language}'."
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source_text": text_input,
            "translated_text": translated_text,
            "source_language": source_language,
            "target_language": target_language
        }
        self.translation_logs.append(log_entry)
        self._save_data()
        return {"status": "success", "source_text": text_input, "translated_text": translated_text, "source_language": source_language, "target_language": target_language}

    def get_translation_history(self) -> List[Dict[str, Any]]:
        """Retrieves the history of simulated translations."""
        return self.translation_logs

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "translate_voice_input":
            return self.translate_voice_input(kwargs['text_input'], kwargs.get('source_language', 'en'), kwargs.get('target_language', 'es'))
        elif operation == "get_translation_history":
            return self.get_translation_history()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RealtimeVoiceTranslatorSimulatorTool functionality...")
    temp_dir = "temp_translator_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    translator_tool = RealtimeVoiceTranslatorSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Translate "Hello" from English to Spanish
        print("\n--- Translating 'Hello' (en to es) ---")
        result1 = translator_tool.execute(operation="translate_voice_input", text_input="Hello", source_language="en", target_language="es")
        print(json.dumps(result1, indent=2))

        # 2. Translate "How are you?" from English to German
        print("\n--- Translating 'How are you?' (en to de) ---")
        result2 = translator_tool.execute(operation="translate_voice_input", text_input="How are you?", source_language="en", target_language="de")
        print(json.dumps(result2, indent=2))

        # 3. Translate an unknown phrase
        print("\n--- Translating 'What is your name?' (en to fr) ---")
        result3 = translator_tool.execute(operation="translate_voice_input", text_input="What is your name?", source_language="en", target_language="fr")
        print(json.dumps(result3, indent=2))

        # 4. Get translation history
        print("\n--- Getting translation history ---")
        history = translator_tool.execute(operation="get_translation_history")
        print(json.dumps(history, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
