import logging
import json
import random
from typing import Union, List, Dict, Any, Optional

# Deferring transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered customer journey mapping will not be available.")

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class CustomerJourneyModel:
    """Manages the text generation model for customer journey mapping tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CustomerJourneyModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for customer journey mapping are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for customer journey mapping...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if self._generator is None:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

customer_journey_model_instance = CustomerJourneyModel()

class CreateCustomerJourneyMapTool(BaseTool):
    """Creates a customer journey map based on a user persona, scenario, and key touchpoints using an AI model."""
    def __init__(self, tool_name="create_customer_journey_map"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a customer journey map based on a user persona, scenario, and key touchpoints using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_persona": {"type": "string", "description": "A description of the target user persona (e.g., 'tech-savvy millennial')."},
                "scenario": {"type": "string", "description": "The specific scenario the journey map covers (e.g., 'onboarding a new user', 'resolving a support issue')."},
                "touchpoints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of key touchpoints in the customer journey (e.g., ['Website Visit', 'Email Signup', 'Product Purchase']).",
                    "default": ["Awareness", "Consideration", "Purchase", "Retention"]
                }
            },
            "required": ["user_persona", "scenario"]
        }

    def execute(self, user_persona: str, scenario: str, touchpoints: List[str] = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered journey mapping."})

        if touchpoints is None:
            touchpoints = ["Awareness", "Consideration", "Purchase", "Retention"]

        prompt = f"Create a detailed customer journey map for the user persona '{user_persona}' in the scenario '{scenario}'. The key touchpoints are: {', '.join(touchpoints)}. For each touchpoint, describe the customer's actions, thoughts, emotions, pain points, and opportunities. Provide the output in JSON format with keys 'user_persona', 'scenario', and 'stages' (a list of objects, each with 'stage_name', 'actions', 'thoughts', 'emotions', 'pain_points', and 'opportunities' keys).\n\nJSON Output:"
        
        llm_response = customer_journey_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 1000)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class AnalyzeCustomerJourneyTool(BaseTool):
    """Analyzes a customer journey map for insights and optimizations using an AI model."""
    def __init__(self, tool_name="analyze_customer_journey"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a customer journey map to identify pain points, opportunities for improvement, and overall customer experience insights using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "journey_map_json": {
                    "type": "string",
                    "description": "The customer journey map data to analyze (e.g., output from CreateCustomerJourneyMapTool)."
                }
            },
            "required": ["journey_map_json"]
        }

    def execute(self, journey_map_json: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered journey analysis."})

        try:
            journey_map = json.loads(journey_map_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for journey_map_json."})

        prompt = f"Analyze the following customer journey map for insights and optimizations. Identify key pain points, opportunities for improvement, and provide actionable recommendations to enhance the customer experience. Provide the output in JSON format with keys 'analysis_summary', 'identified_pain_points', 'identified_opportunities', and 'recommendations'.\n\nCustomer Journey Map: {json.dumps(journey_map)}\n\nJSON Output:"
        
        llm_response = customer_journey_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})