import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from mic.llm_loader import get_llm # Import the shared LLM instance
from tools.base_tool import BaseTool

# Import conversational_ai_tool components
try:
    from .conversational_ai_tool import conversation_manager, ConversationalAITool as SpecificConversationalAITool
    CONVERSATIONAL_AI_TOOL_AVAILABLE = True
except ImportError:
    SpecificConversationalAITool = None
    CONVERSATIONAL_AI_TOOL_AVAILABLE = False
    logging.warning("SpecificConversationalAITool from conversational_ai_tool.py not found. Customer support chatbot will use a simpler LLM interaction.")

# Import customer_feedback_analyzer components
try:
    from .customer_feedback_analyzer import AnalyzeFeedbackSentimentTool
    FEEDBACK_ANALYZER_AVAILABLE = True
except ImportError:
    AnalyzeFeedbackSentimentTool = None
    FEEDBACK_ANALYZER_AVAILABLE = False
    logging.warning("AnalyzeFeedbackSentimentTool from customer_feedback_analyzer.py not found. Feedback analysis will be simulated.")

logger = logging.getLogger(__name__)

FAQ_FILE = Path("faq_knowledge_base.json")
ESCALATION_LOG_FILE = Path("escalation_log.json")
FEEDBACK_LOG_FILE = Path("feedback_log.json")

class FAQManager:
    """Manages FAQ knowledge base, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = FAQ_FILE):
        if cls._instance is None:
            cls._instance = super(FAQManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.faqs: Dict[str, str] = cls._instance._load_faqs()
        return cls._instance

    def _load_faqs(self) -> Dict[str, str]:
        """Loads FAQs from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty FAQs.")
                return {}
            except Exception as e:
                logger.error(f"Error loading FAQs from {self.file_path}: {e}")
                return {}
        return {}

    def _save_faqs(self) -> None:
        """Saves FAQs to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.faqs, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving FAQs to {self.file_path}: {e}")

    def add_faq_entry(self, topic: str, answer: str) -> bool:
        if topic in self.faqs:
            return False
        self.faqs[topic] = answer
        self._save_faqs()
        return True

    def get_faq_answer(self, topic: str) -> Optional[str]:
        return self.faqs.get(topic)

faq_manager = FAQManager()

class CustomerSupportModel:
    """Manages the LLM instance for customer support tasks."""
    _llm = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomerSupportModel, cls).__new__(cls)
            cls._instance._llm = get_llm()
            if cls._instance._llm is None:
                logger.error("LLM not initialized. Customer support tools will not be fully functional.")
        return cls._instance

    def generate_response(self, prompt: str) -> str:
        if self._llm is None:
            return json.dumps({"error": "LLM not available. Please ensure it is configured correctly."})
        try:
            return self._llm.generate_response(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return json.dumps({"error": f"LLM generation failed: {e}"})

customer_support_model_instance = CustomerSupportModel()

class HandleCustomerQueryTool(BaseTool):
    """Handles a customer query using an LLM, leveraging conversation history."""
    def __init__(self, tool_name="handle_customer_query"):
        super().__init__(tool_name=tool_name)
        self.specific_conversational_ai_tool = SpecificConversationalAITool() if CONVERSATIONAL_AI_TOOL_AVAILABLE else None

    @property
    def description(self) -> str:
        return "Handles a customer query using an LLM to generate a response based on the query text and conversation history."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the customer."},
                "user_query": {"type": "string", "description": "The customer's query or question."}
            },
            "required": ["user_id", "user_query"]
        }

    def execute(self, user_id: str, user_query: str, **kwargs: Any) -> str:
        if self.specific_conversational_ai_tool:
            return self.specific_conversational_ai_tool.execute(user_id=user_id, user_message=user_query)
        else:
            # Fallback if specific conversational AI tool is not available
            if customer_support_model_instance._llm is None:
                return json.dumps({"error": "Local LLM not available. Please ensure it is configured correctly."})
            
            prompt = f"You are a helpful customer support chatbot. Respond to the following customer query: {user_query}"
            response = customer_support_model_instance.generate_response(prompt)
            return json.dumps({"user_id": user_id, "user_query": user_query, "chatbot_response": response}, indent=2)

class EscalateToHumanTool(BaseTool):
    """Escalates a customer query to a human agent."""
    def __init__(self, tool_name="escalate_to_human"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Escalates a customer query to a human support agent, recording the escalation in a persistent log."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the customer."},
                "user_query": {"type": "string", "description": "The customer's query that needs escalation."},
                "reason": {"type": "string", "description": "The reason for escalation.", "default": "Chatbot unable to resolve."}
            },
            "required": ["user_id", "user_query"]
        }

    def execute(self, user_id: str, user_query: str, reason: str = "Chatbot unable to resolve.", **kwargs: Any) -> str:
        # Record escalation in a log file
        escalation_entry = {
            "user_id": user_id,
            "query": user_query,
            "reason": reason,
            "timestamp": datetime.now().isoformat() + "Z"
        }
        try:
            if ESCALATION_LOG_FILE.exists():
                with open(ESCALATION_LOG_FILE, 'r+', encoding='utf-8') as f:
                    log_data = json.load(f)
                    log_data.append(escalation_entry)
                    f.seek(0)
                    json.dump(log_data, f, indent=4)
            else:
                os.makedirs(ESCALATION_LOG_FILE.parent, exist_ok=True)
                with open(ESCALATION_LOG_FILE, 'w', encoding='utf-8') as f:
                    json.dump([escalation_entry], f, indent=4)
            
            return json.dumps({"message": f"Query for user '{user_id}' escalated to a human agent. Reason: {reason}.", "escalation_details": escalation_entry}, indent=2)
        except Exception as e:
            logger.error(f"Error recording escalation: {e}")
            return json.dumps({"error": f"Failed to escalate query: {e}"})

class ProvideFAQAnswerTool(BaseTool):
    """Provides an answer to a customer query from a predefined FAQ knowledge base."""
    def __init__(self, tool_name="provide_faq_answer"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Provides an answer to a customer query from a predefined FAQ knowledge base."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"query_topic": {"type": "string", "description": "The topic of the customer's query (e.g., 'shipping', 'returns', 'contact')."}},
            "required": ["query_topic"]
        }

    def execute(self, query_topic: str, **kwargs: Any) -> str:
        answer = faq_manager.get_faq_answer(query_topic)
        if answer:
            return json.dumps({"query_topic": query_topic, "answer": answer}, indent=2)
        else:
            return json.dumps({"message": f"No FAQ answer found for topic '{query_topic}'."})

class CollectCustomerFeedbackTool(BaseTool):
    """Collects customer feedback and analyzes its sentiment."""
    def __init__(self, tool_name="collect_customer_feedback"):
        super().__init__(tool_name=tool_name)
        self.sentiment_analyzer = AnalyzeFeedbackSentimentTool() if FEEDBACK_ANALYZER_AVAILABLE else None

    @property
    def description(self) -> str:
        return "Collects customer feedback, records it in a persistent log, and analyzes its sentiment."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the customer providing feedback."},
                "feedback_text": {"type": "string", "description": "The customer's feedback text."}
            },
            "required": ["user_id", "feedback_text"]
        }

    def execute(self, user_id: str, feedback_text: str, **kwargs: Any) -> str:
        sentiment_result = {"sentiment": "N/A", "score": "N/A"}
        if self.sentiment_analyzer:
            sentiment_json = self.sentiment_analyzer.execute(feedback_text=feedback_text)
            sentiment_data = json.loads(sentiment_json)
            sentiment_result = sentiment_data.get("sentiment_analysis", sentiment_result)

        feedback_entry = {
            "user_id": user_id,
            "feedback_text": feedback_text,
            "sentiment": sentiment_result["sentiment"],
            "sentiment_score": sentiment_result["score"],
            "timestamp": datetime.now().isoformat() + "Z"
        }
        try:
            if FEEDBACK_LOG_FILE.exists():
                with open(FEEDBACK_LOG_FILE, 'r+', encoding='utf-8') as f:
                    log_data = json.load(f)
                    log_data.append(feedback_entry)
                    f.seek(0)
                    json.dump(log_data, f, indent=4)
            else:
                os.makedirs(FEEDBACK_LOG_FILE.parent, exist_ok=True)
                with open(FEEDBACK_LOG_FILE, 'w', encoding='utf-8') as f:
                    json.dump([feedback_entry], f, indent=4)
            
            return json.dumps({"message": f"Feedback from user '{user_id}' collected and analyzed.", "feedback_details": feedback_entry}, indent=2)
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return json.dumps({"error": f"Failed to collect feedback: {e}"})

class AddFAQEntryTool(BaseTool):
    """Adds a new FAQ entry to the knowledge base."""
    def __init__(self, tool_name="add_faq_entry"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new question and answer entry to the FAQ knowledge base."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic or question for the FAQ entry."},
                "answer": {"type": "string", "description": "The answer to the FAQ entry."}
            },
            "required": ["topic", "answer"]
        }

    def execute(self, topic: str, answer: str, **kwargs: Any) -> str:
        success = faq_manager.add_faq_entry(topic, answer)
        if success:
            report = {"message": f"FAQ entry for topic '{topic}' added successfully."}
        else:
            report = {"error": f"FAQ entry for topic '{topic}' already exists. Use update if you want to modify it."}
        return json.dumps(report, indent=2)