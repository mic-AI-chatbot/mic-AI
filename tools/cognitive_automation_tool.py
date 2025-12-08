import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    from PIL import Image
    # librosa and soundfile are often dependencies of audio-classification pipelines
    import librosa
    import soundfile as sf
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers, PIL, librosa, or soundfile not found. Unstructured data processing will be simulated.")

logger = logging.getLogger(__name__)

class UnstructuredDataProcessor:
    """Manages AI models for processing unstructured data (text, image, audio), using a singleton pattern."""
    _sentiment_analyzer = None
    _object_detector = None
    _audio_classifier = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UnstructuredDataProcessor, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for unstructured data processing are not installed. Please install 'transformers', 'torch', 'Pillow', 'librosa', 'soundfile'.")
                return cls._instance # Return instance without models
            
            try:
                logger.info("Initializing sentiment analyzer...")
                cls._instance._sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
                logger.info("Initializing object detector...")
                cls._instance._object_detector = pipeline("object-detection", model="facebook/detr-resnet-50")
                logger.info("Initializing audio classifier...")
                cls._instance._audio_classifier = pipeline("audio-classification", model="MIT/ast-finetuned-audioset-10-10-0.4593")
            except Exception as e:
                logger.error(f"Failed to load AI models for unstructured data processing: {e}")
        return cls._instance

    def process_text(self, text_content: str) -> Dict[str, Any]:
        if not self._sentiment_analyzer: return {"error": "Sentiment analyzer not available."}
        sentiment_result = self._sentiment_analyzer(text_content)[0]
        return {"sentiment": sentiment_result['label'].lower(), "confidence": round(sentiment_result['score'], 2)}

    def process_image(self, image_path: str) -> Dict[str, Any]:
        if not self._object_detector: return {"error": "Object detector not available."}
        try:
            image = Image.open(image_path)
            detection_results = self._object_detector(image)
            objects = [{"box": det['box'], "label": det['label'], "score": round(det['score'], 2)} for det in detection_results]
            return {"objects_detected": objects}
        except Exception as e:
            return {"error": f"Image processing failed: {e}"}

    def process_audio(self, audio_path: str) -> Dict[str, Any]:
        if not self._audio_classifier: return {"error": "Audio classifier not available."}
        try:
            audio_results = self._audio_classifier(audio_path)
            events = [{"label": ev['label'], "score": round(ev['score'], 2)} for ev in audio_results]
            return {"events_detected": events}
        except Exception as e:
            return {"error": f"Audio processing failed: {e}"}

unstructured_data_processor = UnstructuredDataProcessor()

# In-memory storage for simulated decision rules and learning data
decision_rules: Dict[str, Any] = {
    "invoice_processing": {"threshold": 1000, "action_high_value": "require_approval", "action_low_value": "auto_approve"},
    "customer_support_routing": {"keywords": {"technical": "tech_support_queue", "billing": "billing_queue", "refund": "billing_queue", "issue": "tech_support_queue"}, "default": "general_support_queue"}
}
learning_data: List[Dict[str, Any]] = [] # Stores simulated learning data

class ProcessUnstructuredDataTool(BaseTool):
    """Processes unstructured data (text, image, audio) to extract key insights using AI models."""
    def __init__(self, tool_name="process_unstructured_data"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Processes unstructured data (text, image, audio) to extract key insights like keywords, sentiment, or detected objects using AI models."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data_id": {"type": "string", "description": "A unique ID for the unstructured data."},
                "data_type": {"type": "string", "description": "The type of unstructured data.", "enum": ["text", "image", "audio"]},
                "content": {"type": "string", "description": "The content of the unstructured data (e.g., text string, image path, audio path)."}
            },
            "required": ["data_id", "data_type", "content"]
        }

    def execute(self, data_id: str, data_type: str, content: str, **kwargs: Any) -> str:
        insights = {}
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "AI models for unstructured data processing are not available. Please install 'transformers', 'torch', 'Pillow', 'librosa', 'soundfile'."})

        if data_type == "text":
            insights = unstructured_data_processor.process_text(content)
        elif data_type == "image":
            insights = unstructured_data_processor.process_image(content)
        elif data_type == "audio":
            insights = unstructured_data_processor.process_audio(content)
        else:
            return json.dumps({"error": f"Unsupported data type: {data_type}."})
            
        return json.dumps({
            "data_id": data_id,
            "data_type": data_type,
            "insights": insights,
            "message": f"Unstructured data '{data_id}' processed successfully."
        }, indent=2)

class AutomateDecisionMakingTool(BaseTool):
    """Automates decision-making based on extracted insights and predefined rules."""
    def __init__(self, tool_name="automate_decision_making"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Automates decision-making processes based on extracted insights from unstructured data and predefined decision rules."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "process_name": {"type": "string", "description": "The name of the automated process.", "enum": ["invoice_processing", "customer_support_routing"]},
                "insights_json": {
                    "type": "string",
                    "description": "JSON string of extracted insights from unstructured data (e.g., from ProcessUnstructuredDataTool)."
                }
            },
            "required": ["process_name", "insights_json"]
        }

    def execute(self, process_name: str, insights_json: str, **kwargs: Any) -> str:
        try:
            insights = json.loads(insights_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for insights_json."})

        if process_name not in decision_rules:
            return json.dumps({"error": f"No decision rules found for process '{process_name}'."})
            
        rule = decision_rules[process_name]
        decision = "No decision made"
        
        if process_name == "invoice_processing":
            invoice_value = insights.get("invoice_value", 0)
            if invoice_value > rule["threshold"]:
                decision = rule["action_high_value"]
            else:
                decision = rule["action_low_value"]
        elif process_name == "customer_support_routing":
            text_sentiment = insights.get("sentiment", "neutral")
            text_content = insights.get("text_content", "").lower() # Assuming text content is available for keyword matching
            
            routed_to = rule["default"]
            for keyword, queue in rule["keywords"].items():
                if keyword in text_content:
                    routed_to = queue
                    break
            decision = f"Route to {routed_to}"
            if text_sentiment == "negative":
                decision += " with high priority"
        
        return json.dumps({
            "process_name": process_name,
            "insights_used": insights,
            "decision": decision,
            "confidence": random.uniform(0.8, 0.99)  # nosec B311
        }, indent=2)

class LearnFromDecisionTool(BaseTool):
    """Simulates learning from past decisions to improve future automation."""
    def __init__(self, tool_name="learn_from_decision"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates learning from a past automated decision, recording feedback to improve future automation accuracy."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "process_name": {"type": "string", "description": "The name of the automated process.", "enum": ["invoice_processing", "customer_support_routing"]},
                "insights_json": {"type": "string", "description": "JSON string of insights that led to the decision."},
                "automated_decision": {"type": "string", "description": "The decision made by the automation."},
                "human_override_decision": {"type": "string", "description": "The decision made by a human if it differed from the automated one."},
                "feedback_score": {"type": "integer", "description": "A score indicating the quality of the automated decision (1-5, 5 being best)."}
            },
            "required": ["process_name", "insights_json", "automated_decision", "feedback_score"]
        }

    def execute(self, process_name: str, insights_json: str, automated_decision: str, human_override_decision: str = None, feedback_score: int = 0, **kwargs: Any) -> str:
        try:
            insights = json.loads(insights_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for insights_json."})

        learning_data.append({
            "process_name": process_name,
            "insights": insights,
            "automated_decision": automated_decision,
            "human_override_decision": human_override_decision,
            "feedback_score": feedback_score,
            "timestamp": datetime.now().isoformat() + "Z"
        })
        
        # Simulate updating decision rules based on feedback
        if feedback_score < 3 and human_override_decision:
            message = "Automated decision was suboptimal. Simulating adjustment of decision rules based on human override."
            # In a real system, this would involve retraining a model or updating rules.
        else:
            message = "Automated decision was good. Reinforcing current decision rules."
        
        return json.dumps({
            "message": message,
            "process_name": process_name,
            "feedback_recorded": True
        }, indent=2)