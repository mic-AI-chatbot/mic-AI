import logging
import json
import random
from typing import Union, List, Dict, Any, Optional

# Deferring googletrans and transformers imports
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    Translator = None
    GOOGLETRANS_AVAILABLE = False
    logging.warning("googletrans library not found. Translation functionality will be limited. Please install it with 'pip install googletrans==4.0.0-rc1'.")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered context awareness will not be available. Please install 'transformers' and 'torch'.")

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class TranslationModel:
    """Manages translation and context-aware AI models, using a singleton pattern."""
    _translator = None
    _llm_generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationModel, cls).__new__(cls)
            if GOOGLETRANS_AVAILABLE:
                try:
                    cls._instance._translator = Translator()
                except Exception as e:
                    logger.error(f"Failed to initialize googletrans Translator: {e}")
            
            if TRANSFORMERS_AVAILABLE:
                try:
                    logger.info("Initializing text generation model (gpt2) for context awareness...")
                    cls._instance._llm_generator = pipeline("text-generation", model="gpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def translate_text(self, text: str, src: str, dest: str) -> str:
        if not self._translator:
            return json.dumps({"error": "Translation service not available. Please install 'googletrans'."})
        try:
            translation = self._translator.translate(text, src=src, dest=dest)
            return translation.text
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return json.dumps({"error": f"Translation failed: {e}"})

    def refine_translation_with_context(self, text: str, translated_text: str, context: str, src: str, dest: str) -> str:
        if not self._llm_generator:
            return translated_text # Return original translation if LLM not available
        
        prompt = f"The original text in {src} is: '{text}'. It was translated to {dest} as: '{translated_text}'. The context of this translation is: '{context}'. Refine the translation to be more accurate and context-aware. Provide only the refined translation.\n\nRefined Translation:"
        
        try:
            generated = self._llm_generator(prompt, max_length=len(prompt.split()) + 200, num_return_sequences=1, pad_token_id=self._llm_generator.tokenizer.eos_token_id)[0]['generated_text']
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"LLM refinement failed: {e}")
            return translated_text # Fallback to original translation

translation_model_instance = TranslationModel()

class TranslateTextTool(BaseTool):
    """Translates text from a source language to a target language, with optional context awareness."""
    def __init__(self, tool_name="translate_text"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Translates a text string from a source language to a target language, optionally using provided context for better accuracy."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to translate."},
                "source_language": {"type": "string", "description": "The language of the input text (e.g., 'en', 'fr')."},
                "target_language": {"type": "string", "description": "The language to translate the text into (e.g., 'es', 'de')."},
                "context": {"type": "string", "description": "Optional: Additional context to aid in translation (e.g., 'medical report', 'legal document').", "default": None}
            },
            "required": ["text", "source_language", "target_language"]
        }

    def execute(self, text: str, source_language: str, target_language: str, context: Optional[str] = None, **kwargs: Any) -> str:
        if not GOOGLETRANS_AVAILABLE:
            return json.dumps({"error": "The 'googletrans' library is not installed. Please install it with 'pip install googletrans==4.0.0-rc1'."})

        translated_text = translation_model_instance.translate_text(text, source_language, target_language)
        
        if context and TRANSFORMERS_AVAILABLE:
            refined_translation = translation_model_instance.refine_translation_with_context(text, translated_text, context, source_language, target_language)
            translated_text = refined_translation
        
        return json.dumps({
            "original_text": text,
            "source_language": source_language,
            "target_language": target_language,
            "translated_text": translated_text,
            "context_used": context
        }, indent=2)

class TranslateDocumentTool(BaseTool):
    """Translates the content of an entire document from a source language to a target language."""
    def __init__(self, tool_name="translate_document"):
        super().__init__(tool_name=tool_name)
        self.translate_text_tool = TranslateTextTool()

    @property
    def description(self) -> str:
        return "Translates the content of an entire document from a source language to a target language, optionally using provided context."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "document_content": {"type": "string", "description": "The full content of the document to translate."},
                "source_language": {"type": "string", "description": "The language of the input document (e.g., 'en', 'fr')."},
                "target_language": {"type": "string", "description": "The language to translate the document into (e.g., 'es', 'de')."},
                "context": {"type": "string", "description": "Optional: Additional context to aid in translation (e.g., 'medical report', 'legal document').", "default": None}
            },
            "required": ["document_content", "source_language", "target_language"]
        }

    def execute(self, document_content: str, source_language: str, target_language: str, context: Optional[str] = None, **kwargs: Any) -> str:
        # For simplicity, this tool will just use TranslateTextTool to translate the entire content
        # In a real scenario, document structure (paragraphs, headings) would be preserved.
        translated_report_json = self.translate_text_tool.execute(
            text=document_content,
            source_language=source_language,
            target_language=target_language,
            context=context
        )
        
        translated_report = json.loads(translated_report_json)
        
        return json.dumps({
            "original_document_preview": document_content[:100] + "...",
            "source_language": source_language,
            "target_language": target_language,
            "translated_document_content": translated_report.get("translated_text"),
            "context_used": context
        }, indent=2)