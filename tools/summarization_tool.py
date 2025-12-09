import logging
import os
import json
import re
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool
from transformers import pipeline
# from sumy.parsers.plaintext import PlaintextParser # For extractive summarization
# from sumy.nlp.tokenizers import Tokenizer
# from sumy.summarizers.lsa import LsaSummarizer
# from sumy.nlp.stemmers import Stemmer
# from sumy.utils import get_stop_words

logger = logging.getLogger(__name__)

class SummarizationTool(BaseTool):
    """
    A tool for summarizing text and documents, and extracting keywords.
    """

    @property
    def description(self) -> str:
        return "Summarizes text using abstractive or extractive methods, and extracts keywords."

    def __init__(self, tool_name: str = "summarization_tool"):
        super().__init__(tool_name)
        self.model_name = self.config.get('DEFAULT', 'summarization_model', fallback='t5-small')
        self.device = self.config.getint('DEFAULT', 'summarization_device', fallback=-1) # -1 for CPU, 0 for GPU
        self.summarizer_pipeline = None
        # self._load_summarizer_pipeline() # REMOVED: This will be called lazily

    def _load_summarizer_pipeline(self):
        """
        Loads the summarization pipeline.
        """
        if self.summarizer_pipeline is None:
            self.logger.info(f"Loading summarization model: {self.model_name} on device {self.device}")
            self.summarizer_pipeline = pipeline("summarization", model=self.model_name, device=self.device)

    def _summarize_abstractive(self, text: str, max_length: int = 150, min_length: int = 30) -> str:
        """
        Summarizes text using an abstractive (LLM-based) approach.
        """
        self._load_summarizer_pipeline() # LAZY LOADING: Ensure model is loaded before use
        if not text.strip():
            raise ValueError("No text provided for summarization.")
        summary = self.summarizer_pipeline(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']

    def _summarize_extractive(self, text: str, sentences_count: int = 5) -> str:
        """
        Summarizes text using an extractive approach. (Placeholder for sumy/gensim)
        """
        self.logger.warning("Extractive summarization is a placeholder. Integrate with sumy/gensim for real summarization.")
        # Simulated extractive summary: just return the first few sentences
        sentences = text.split('.')
        return ". ".join(sentences[:sentences_count]) + "."

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extracts keywords from text. (Placeholder for more advanced keyword extraction)
        """
        self.logger.warning("Keyword extraction is a placeholder. Integrate with NLP libraries for real extraction.")
        # Simulated keyword extraction: simple word frequency
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        sorted_keywords = sorted(word_counts.items(), key=lambda item: item[1], reverse=True)
        return [word for word, count in sorted_keywords[:5]] # Top 5 keywords

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["summarize_abstractive", "summarize_extractive", "extract_keywords"]},
                "text": {"type": "string", "description": "The text to process."},
                "max_length": {"type": "integer", "minimum": 10, "default": 150},
                "min_length": {"type": "integer", "minimum": 5, "default": 30},
                "sentences_count": {"type": "integer", "minimum": 1, "default": 5}
            },
            "required": ["operation", "text"]
        }

    def execute(self, operation: str, text: str, **kwargs: Any) -> Union[str, Dict[str, Any], List[str]]:
        if not text:
            raise ValueError("Input 'text' cannot be empty.")

        if operation == "summarize_abstractive":
            return self._summarize_abstractive(text, kwargs.get('max_length', 150), kwargs.get('min_length', 30))
        elif operation == "summarize_extractive":
            return self._summarize_extractive(text, kwargs.get('sentences_count', 5))
        elif operation == "extract_keywords":
            return self._extract_keywords(text)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SummarizationTool functionality...")
    
    summarizer_tool = SummarizationTool()
    
    sample_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, unlike the natural intelligence
    displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents":
    any device that perceives its environment and takes actions that maximize its chance of successfully
    achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines
    that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and
    "problem-solving".

    AI applications include advanced web search engines (e.g., Google Search), recommendation systems
    (used by YouTube, Amazon, and Netflix), understanding human speech (such as Siri and Alexa),
    self-driving cars (e.g., Waymo), and competing at the highest level in strategic game systems
    (such as AlphaGo and AlphaZero).
    """

    try:
        # 1. Abstractive summarization
        print("\n--- Abstractive Summarization ---")
        abstractive_summary = summarizer_tool.execute(operation="summarize_abstractive", text=sample_text, max_length=50, min_length=20)
        print(abstractive_summary)

        # 2. Extractive summarization
        print("\n--- Extractive Summarization ---")
        extractive_summary = summarizer_tool.execute(operation="summarize_extractive", text=sample_text, sentences_count=2)
        print(extractive_summary)

        # 3. Keyword extraction
        print("\n--- Keyword Extraction ---")
        keywords = summarizer_tool.execute(operation="extract_keywords", text=sample_text)
        print(json.dumps(keywords, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")