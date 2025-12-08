import logging
import json
from typing import Dict, Any
from tools.base_tool import BaseTool

# These are imported inside the _initialize method to avoid import-time crashes
# from transformers import pipeline
# import spacy

logger = logging.getLogger(__name__)

class AnalyzeAndCorrectTextTool(BaseTool):
    """
    A tool for advanced grammar correction and writing style analysis.
    Models are loaded lazily on first use to prevent startup crashes.
    """

    def __init__(self, tool_name: str = "analyze_and_correct_text"):
        super().__init__(tool_name=tool_name)
        self.grammar_corrector = None
        self.nlp = None
        self._initialized = False

    def _initialize(self):
        """
        Lazily initializes the models to prevent startup crashes.
        This method is called on the first execution.
        """
        if self._initialized:
            return

        logger.info("Performing first-time initialization for AnalyzeAndCorrectTextTool...")
        
        # Import necessary libraries here
        try:
            from transformers import pipeline
            import spacy
        except ImportError as e:
            logger.error(f"Failed to import necessary libraries: {e}")
            self._initialized = True # Mark as initialized to prevent retries
            return

        # 1. Load grammar correction model
        try:
            logger.info("Loading grammar correction model (pszemraj/flan-t5-large-grammar-synthesis)...")
            self.grammar_corrector = pipeline("text2text-generation", model="pszemraj/flan-t5-large-grammar-synthesis")
            logger.info("Grammar correction model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load grammar correction model: {e}", exc_info=True)
            logger.warning("Grammar correction functionality will be unavailable.")

        # 2. Load spaCy model for style analysis
        try:
            logger.info("Loading spaCy model (en_core_web_sm)...")
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully.")
        except OSError:
            logger.warning("Spacy model 'en_core_web_sm' not found. Attempting to download...")
            try:
                from spacy.cli import download
                download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model downloaded and loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to download or load spaCy model: {e}", exc_info=True)
                logger.warning("Style analysis functionality will be unavailable.")
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading spaCy model: {e}", exc_info=True)
            logger.warning("Style analysis functionality will be unavailable.")

        self._initialized = True

    @property
    def description(self) -> str:
        return "Corrects grammar and analyzes the writing style of a text, providing suggestions for improvement."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The input text to analyze and correct."}
            },
            "required": ["text"]
        }

    def _check_passive_voice(self, doc) -> list:
        passive_sentences = []
        for sent in doc.sents:
            if any(token.dep_ == "nsubjpass" for token in sent):
                passive_sentences.append(sent.text)
        return passive_sentences

    def _calculate_readability(self, doc) -> dict:
        num_words = len([token for token in doc if not token.is_punct])
        num_sentences = len(list(doc.sents))
        if num_sentences == 0 or num_words == 0:
            return {"error": "Could not calculate readability for empty or very short text."}
        
        avg_sentence_length = num_words / num_sentences
        
        readability_score = "good"
        if avg_sentence_length > 25:
            readability_score = "hard_to_read"
        elif avg_sentence_length > 18:
            readability_score = "medium"
            
        return {
            "average_sentence_length": round(avg_sentence_length, 2),
            "estimated_readability": readability_score
        }

    def execute(self, text: str, **kwargs: Any) -> str:
        # Ensure models are loaded before proceeding
        try:
            self._initialize()
        except Exception as e:
            # If initialization itself crashes, report a critical failure.
            logger.critical(f"CRITICAL: Model initialization for {self.tool_name} failed unexpectedly: {e}", exc_info=True)
            return json.dumps({"error": "A critical error occurred during model initialization. Check server logs."})

        if not text:
            return json.dumps({"error": "Input text cannot be empty."})

        # --- Grammar Correction ---
        corrected_text = "Grammar correction model not available."
        if self.grammar_corrector:
            try:
                prompt = f"grammatical correction: {text}"
                # Adjust max_length to be more generous
                corrected_text = self.grammar_corrector(prompt, max_length=int(len(text.split()) * 1.5) + 50)[0]['generated_text']
            except Exception as e:
                logger.error(f"Grammar correction failed during execution: {e}")
                corrected_text = f"Error during grammar correction. The model may have failed."
        
        # --- Style Analysis ---
        style_analysis_report = {"error": "Style analysis model not available."}
        if self.nlp:
            try:
                doc = self.nlp(text)
                style_suggestions = []
                
                passive_sentences = self._check_passive_voice(doc)
                if passive_sentences:
                    style_suggestions.append(f"Consider rewriting sentences in active voice for more directness: {passive_sentences[:2]}")

                readability = self._calculate_readability(doc)
                if readability.get("estimated_readability") == "hard_to_read":
                    style_suggestions.append("Text has long sentences, making it hard to read. Try to shorten or split them.")
                elif readability.get("estimated_readability") == "medium":
                    style_suggestions.append("Sentences are moderately long. Consider simplifying some for clarity.")

                style_analysis_report = {
                    "suggestions": style_suggestions if style_suggestions else ["The writing style seems generally good."],
                    "readability": readability,
                }
            except Exception as e:
                logger.error(f"Style analysis failed during execution: {e}")
                style_analysis_report = {"error": "An error occurred during style analysis."}

        report = {
            "original_text": text,
            "corrected_text": corrected_text,
            "style_analysis": style_analysis_report
        }
        
        return json.dumps(report, indent=2)
