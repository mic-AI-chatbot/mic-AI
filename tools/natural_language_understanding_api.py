import logging
import json
import random
import re
from typing import Union, List, Dict, Any, Optional
from collections import Counter
import spacy
from textblob import TextBlob

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'.")
    nlp = None

# A simple list of common English stop words (for summarization)
STOP_WORDS = set([
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', "can't", 'cannot',
    'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few',
    'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll",
    "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll",
    "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most',
    "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our',
    'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should',
    "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves',
    'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those',
    'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're",
    "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who',
    "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're",
    "you've", 'your', 'yours', 'yourself', 'yourselves'
])

class NaturalLanguageUnderstandingTool(BaseTool):
    """
    A tool for performing various Natural Language Understanding (NLU) tasks
    like sentiment analysis, entity extraction, text classification, and summarization.
    """

    def __init__(self, tool_name: str = "NLU_Tool", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        if nlp is None:
            raise RuntimeError("spaCy model 'en_core_web_sm' is not available.")

    @property
    def description(self) -> str:
        return "Performs sentiment analysis, entity extraction, text classification, and summarization."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["analyze_sentiment", "extract_entities", "classify_text", "summarize_text", "translate_text"]},
                "text": {"type": "string", "description": "The text to process."},
                "categories": {"type": "array", "items": {"type": "string"}, "description": "List of categories for classification."},
                "keywords_per_category": {"type": "object", "description": "Dict mapping category to list of keywords, e.g., {'tech': ['software', 'AI']}"},
                "summary_length": {"type": "string", "enum": ["short", "medium", "long"], "default": "medium"},
                "target_language": {"type": "string", "description": "Target language for translation (e.g., 'es', 'fr').", "default": "es"}
            },
            "required": ["operation", "text"]
        }

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyzes the sentiment of text using TextBlob."""
        blob = TextBlob(text)
        sentiment = "positive" if blob.sentiment.polarity > 0.1 else "negative" if blob.sentiment.polarity < -0.1 else "neutral"
        return {"polarity": round(blob.sentiment.polarity, 2), "subjectivity": round(blob.sentiment.subjectivity, 2), "sentiment": sentiment}

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extracts named entities from text using spaCy."""
        doc = nlp(text)
        return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

    def _classify_text(self, text: str, categories: Optional[List[str]] = None, keywords_per_category: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """Classifies text into categories based on keyword matching."""
        if not categories and not keywords_per_category:
            return {"predicted_category": "GENERAL", "confidence": 0.5, "message": "No categories or keywords provided, defaulting to GENERAL."}
        
        if not keywords_per_category:
            # If only categories are provided, create dummy keywords
            keywords_per_category = {cat: [cat.lower()] for cat in categories}

        text_lower = text.lower()
        scores = {cat: 0 for cat in keywords_per_category.keys()}
        
        for category, keywords in keywords_per_category.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[category] += 1
        
        if not any(scores.values()):
            return {"predicted_category": "UNCATEGORIZED", "confidence": 0.0, "message": "No matching keywords found."}

        best_category = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_category] / total_score if total_score > 0 else 0.0
        
        return {"predicted_category": best_category, "confidence": round(confidence, 2)}

    def _summarize_text(self, text: str, summary_length: str = "medium") -> str:
        """Generates an extractive summary based on sentence importance."""
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        if not sentences: return ""

        words = [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop]
        word_freq = Counter(words)
        
        sentence_scores = {}
        for i, sent in enumerate(sentences):
            sentence_words = [token.lemma_.lower() for token in nlp(sent) if token.is_alpha]
            score = sum(word_freq[word] for word in sentence_words)
            sentence_scores[i] = score

        length_map = {"short": 0.15, "medium": 0.3, "long": 0.5}
        num_sentences = int(len(sentences) * length_map[summary_length])
        num_sentences = max(1, num_sentences) # Ensure at least one sentence

        sorted_sentences = sorted(sentence_scores.items(), key=lambda item: item[1], reverse=True)
        top_sentence_indices = sorted([item[0] for item in sorted_sentences[:num_sentences]])
        
        summary = ' '.join([sentences[i] for i in top_sentence_indices])
        return summary

    def _translate_text(self, text: str, target_language: str = "es") -> Dict[str, Any]:
        """Simulates text translation."""
        return {
            "status": "simulated",
            "original_text": text,
            "translated_text": f"Simulated translation of '{text[:30]}...' to {target_language}.",
            "target_language": target_language,
            "disclaimer": "This is a simulated translation. No actual translation API was used."
        }

    def execute(self, operation: str, text: str, **kwargs: Any) -> Any:
        """Executes a specified NLU operation on the input text."""
        if not nlp:
            raise RuntimeError("spaCy model not loaded. Cannot execute NLU operations.")

        if operation == "analyze_sentiment":
            return self._analyze_sentiment(text)
        elif operation == "extract_entities":
            return self._extract_entities(text)
        elif operation == "classify_text":
            return self._classify_text(text, kwargs.get("categories"), kwargs.get("keywords_per_category"))
        elif operation == "summarize_text":
            return self._summarize_text(text, kwargs.get("summary_length", "medium"))
        elif operation == "translate_text":
            return self._translate_text(text, kwargs.get("target_language", "es"))
        else:
            raise ValueError(f"Unsupported operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating NaturalLanguageUnderstandingTool functionality...")
    
    nlu_tool = NaturalLanguageUnderstandingTool()
    
    sample_text_sentiment = "I love this product! It's absolutely fantastic and works perfectly."
    sample_text_entities = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
    sample_text_classification = "The new software update improved performance significantly. AI is the future."
    sample_text_summarization = """
    Natural Language Processing (NLP) is a subfield of artificial intelligence. 
    It focuses on enabling computers to understand, interpret, and generate human language. 
    NLP combines computational linguistics with machine learning. 
    Applications include machine translation, sentiment analysis, and chatbots. 
    Recent advancements, especially with deep learning, have significantly improved NLP capabilities.
    """
    
    try:
        # 1. Analyze Sentiment
        print("\n--- Analyzing Sentiment ---")
        sentiment_result = nlu_tool.execute(operation="analyze_sentiment", text=sample_text_sentiment)
        print(json.dumps(sentiment_result, indent=2))

        # 2. Extract Entities
        print("\n--- Extracting Entities ---")
        entities_result = nlu_tool.execute(operation="extract_entities", text=sample_text_entities)
        print(json.dumps(entities_result, indent=2))

        # 3. Classify Text
        print("\n--- Classifying Text ---")
        categories = ["Technology", "Finance", "Healthcare"]
        keywords = {
            "Technology": ["software", "AI", "update", "performance"],
            "Finance": ["money", "investment", "market"],
            "Healthcare": ["patient", "doctor", "hospital"]
        }
        classification_result = nlu_tool.execute(operation="classify_text", text=sample_text_classification, categories=categories, keywords_per_category=keywords)
        print(json.dumps(classification_result, indent=2))

        # 4. Summarize Text
        print("\n--- Summarizing Text (short) ---")
        summary_result = nlu_tool.execute(operation="summarize_text", text=sample_text_summarization, summary_length="short")
        print(summary_result)

        # 5. Simulate Translation
        print("\n--- Simulating Translation to Spanish ---")
        translation_result = nlu_tool.execute(operation="translate_text", text="Hello, how are you?", target_language="es")
        print(json.dumps(translation_result, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")