import logging
import json
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    import spacy
    from textblob import TextBlob
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers, spacy, or textblob not found. Automated essay scoring tools will not be available.")

logger = logging.getLogger(__name__)

class EssayAnalysisModel:
    """Manages NLP models for essay analysis, using a singleton pattern."""
    _generator = None
    _nlp = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EssayAnalysisModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for essay scoring are not installed. Please install 'transformers', 'spacy', and 'textblob'.")
                return cls._instance # Return instance without models
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for essay scoring...")
                    cls._generator = pipeline("text-generation", model="gpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
            
            if cls._nlp is None:
                try:
                    logger.info("Initializing spaCy model for essay analysis...")
                    cls._nlp = spacy.load("en_core_web_sm")
                    logger.info("spaCy model loaded.")
                except OSError:
                    logger.info("spaCy model 'en_core_web_sm' not found. Downloading...")
                    from spacy.cli import download
                    download("en_core_web_sm")
                    cls._nlp = spacy.load("en_core_web_sm")
                except Exception as e:
                    logger.error(f"Failed to load spaCy model: {e}")
        return cls._instance

    def analyze_essay(self, essay_text: str) -> Dict[str, Any]:
        if not self._nlp:
            return {"error": "NLP model not available."}
        
        doc = self._nlp(essay_text)
        blob = TextBlob(essay_text)

        word_count = len([token for token in doc if not token.is_space])
        sentence_count = len(list(doc.sents))
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Simplified Flesch Reading Ease (requires syllable count, which is complex without a dedicated library)
        # For a rough estimate, we'll use average sentence length.
        readability_score = "N/A"
        if avg_sentence_length > 25:
            readability_score = "Challenging"
        elif avg_sentence_length > 15:
            readability_score = "Moderate"
        else:
            readability_score = "Easy"
        
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 2),
            "readability_assessment": readability_score,
            "sentiment_polarity": round(blob.sentiment.polarity, 2),
            "sentiment_subjectivity": round(blob.sentiment.subjectivity, 2)
        }

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

essay_analysis_instance = EssayAnalysisModel()

class ScoreEssayTool(BaseTool):
    """Scores an essay based on predefined criteria using an AI model and NLP features."""
    def __init__(self, tool_name="score_essay"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Scores an essay based on predefined criteria (e.g., grammar, cohesion, vocabulary) and provides an overall score and justification using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "essay_text": {"type": "string", "description": "The full text of the essay to be scored."},
                "criteria": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["grammar", "cohesion", "vocabulary", "argument_strength", "readability", "sentiment"]},
                    "description": "A list of criteria to score against.",
                    "default": ["grammar", "cohesion", "vocabulary"]
                }
            },
            "required": ["essay_text"]
        }

    def execute(self, essay_text: str, criteria: List[str] = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers', 'spacy', and 'textblob' libraries to be installed."})
        if not essay_text:
            return json.dumps({"error": "Essay text cannot be empty."})
            
        if criteria is None:
            criteria = ["grammar", "cohesion", "vocabulary"]

        features = essay_analysis_instance.analyze_essay(essay_text)
        
        prompt = f"Score the following essay based on the criteria: {', '.join(criteria)}. Consider its length ({features['word_count']} words), average sentence length ({features['avg_sentence_length']}), and readability ({features['readability_assessment']}). Also consider its sentiment polarity ({features['sentiment_polarity']}) and subjectivity ({features['sentiment_subjectivity']}). Provide a score for each criterion (out of 100) and an overall score, along with a brief justification.\n\nEssay:\n{essay_text}\n\nScores and Justification (in JSON format):"
        
        generated_text = essay_analysis_instance.generate_response(prompt, max_length=len(prompt.split()) + 400)
        
        # Attempt to parse the generated text as JSON
        json_start = generated_text.find('{')
        json_end = generated_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = generated_text[json_start:json_end]
            try:
                return json.dumps(json.loads(json_str), indent=2)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse generated JSON: {json_str}")
                return json.dumps({"raw_output": generated_text, "error": "Generated output was not valid JSON. Manual parsing needed."})
        else:
            return json.dumps({"raw_output": generated_text, "error": "Could not find JSON in generated output. Manual parsing needed."})

class ProvideEssayFeedbackTool(BaseTool):
    """Provides constructive feedback on an essay using an AI model."""
    def __init__(self, tool_name="provide_essay_feedback"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Provides constructive feedback on an essay, highlighting areas for improvement in grammar, style, and content, using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "essay_text": {"type": "string", "description": "The full text of the essay to provide feedback on."},
                "score_report_json": {"type": "string", "description": "Optional: The JSON score report from the ScoreEssayTool."}
            },
            "required": ["essay_text"]
        }

    def execute(self, essay_text: str, score_report_json: str = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers', 'spacy', and 'textblob' libraries to be installed."})
        if not essay_text:
            return json.dumps({"error": "Essay text cannot be empty."})

        features = essay_analysis_instance.analyze_essay(essay_text)
        
        prompt = f"Provide constructive feedback on the following essay, focusing on grammar, cohesion, vocabulary, and argument strength. Consider its length ({features['word_count']} words), average sentence length ({features['avg_sentence_length']}), and readability ({features['readability_assessment']}). Also consider its sentiment polarity ({features['sentiment_polarity']}) and subjectivity ({features['sentiment_subjectivity']})."
        if score_report_json:
            try:
                score_report = json.loads(score_report_json)
                prompt += f"\n\nHere is a score report: {json.dumps(score_report)}"
            except json.JSONDecodeError:
                logger.warning("Invalid score_report_json provided. Ignoring.")
        
        prompt += "\n\nFeedback:"

        generated_feedback = essay_analysis_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        report = {
            "essay_text_sample": essay_text[:200] + "..." if len(essay_text) > 200 else essay_text,
            "feedback": generated_feedback
        }
        return json.dumps(report, indent=2)