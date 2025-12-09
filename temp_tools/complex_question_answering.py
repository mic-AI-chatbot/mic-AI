import logging
import json
import random
from typing import List, Dict, Any, Optional

try:
    from tools.base_tool import BaseTool
except ImportError:
    class BaseTool:
        def __init__(self, tool_name: str):
            self.tool_name = tool_name
        @property
        def description(self) -> str:
            raise NotImplementedError
        @property
        def parameters(self) -> Dict[str, Any]:
            raise NotImplementedError
        def execute(self, *args, **kwargs) -> Any:
            raise NotImplementedError
    logging.warning("Could not import BaseTool from mic.base_tool. Using a placeholder BaseTool class. Please ensure mic package is correctly installed and accessible.")

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Question answering tools will not be fully functional.")

logger = logging.getLogger(__name__)

class QAModel:
    """Manages the question answering model, using a singleton pattern."""
    _qa_pipeline = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QAModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for question answering are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without model
            
            if cls._qa_pipeline is None:
                try:
                    logger.info("Initializing question answering model (distilbert-base-uncased-distilled-squad)...")
                    cls._qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")
                    logger.info("Question answering model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load question answering model: {e}")
        return cls._instance

    def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        if not self._qa_pipeline:
            return {"error": "Question answering model not available. Check logs for loading errors."}
        try:
            result = self._qa_pipeline(question=question, context=context)
            return {"answer": result['answer'], "score": round(result['score'], 2), "start": result['start'], "end": result['end']}
        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            return {"error": f"Question answering failed: {e}"}

qa_model_instance = QAModel()

class AnswerQuestionTool(BaseTool):
    """Answers a complex question based on provided context using an AI model."""
    def __init__(self, tool_name="answer_question"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Answers a complex question based on provided context or an internal knowledge base, returning an answer and confidence score using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The complex question to answer."},
                "context": {"type": "string", "description": "Additional context (e.g., a document, paragraph) to use for answering the question."}
            },
            "required": ["question", "context"]
        }

    def execute(self, question: str, context: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        result = qa_model_instance.answer_question(question, context)
        return json.dumps({"question": question, "answer_details": result}, indent=2)

class ExtractAnswerTool(BaseTool):
    """Extracts a concise answer to a question from a longer text using an AI model."""
    def __init__(self, tool_name="extract_answer"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Extracts a concise answer to a question from a longer provided text or document using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question for which to extract an answer."},
                "document_text": {"type": "string", "description": "The longer text or document from which to extract the answer."}
            },
            "required": ["question", "document_text"]
        }

    def execute(self, question: str, document_text: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        # The question-answering pipeline can directly extract answers from a document context
        result = qa_model_instance.answer_question(question, document_text)
        return json.dumps({"question": question, "extracted_answer_details": result}, indent=2)