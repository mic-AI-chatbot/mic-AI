import logging
import json
import random
import re
from typing import Union, List, Dict, Any, Optional
from tools.base_tool import BaseTool

# Deferring transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered counterfactual reasoning will not be available.")

logger = logging.getLogger(__name__)

class CounterfactualModel:
    """Manages the text generation model for counterfactual reasoning tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CounterfactualModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for counterfactual reasoning are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for counterfactual reasoning...")
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

counterfactual_model_instance = CounterfactualModel()

class ExplainOutcomeCounterfactuallyTool(BaseTool):
    """Explains why a particular outcome occurred by identifying counterfactuals using an AI model."""
    def __init__(self, tool_name="explain_outcome_counterfactually"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Explains why a particular outcome occurred by identifying counterfactual scenarios (what would have happened if something was different) using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "actual_outcome": {"type": "string", "description": "The actual outcome that occurred."},
                "contributing_factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of factors that contributed to the actual outcome."
                }
            },
            "required": ["actual_outcome", "contributing_factors"]
        }

    def execute(self, actual_outcome: str, contributing_factors: List[str], **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered counterfactual reasoning."})

        factors_str = ", ".join(contributing_factors)
        prompt = f"The actual outcome was: '{actual_outcome}'. The contributing factors were: {factors_str}. Generate 3-5 plausible counterfactual scenarios, explaining what would have happened if one of these factors had been different. For each counterfactual, provide the hypothetical change and the simulated alternative outcome. Provide the output in JSON format with a key 'counterfactual_explanations' which is a list of objects, each with 'hypothetical_change' and 'simulated_alternative_outcome' keys.\n\nJSON Output:"
        
        llm_response = counterfactual_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class SimulateCounterfactualInterventionTool(BaseTool):
    """Simulates the outcome of a hypothetical intervention or change using an AI model."""
    def __init__(self, tool_name="simulate_counterfactual_intervention"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates the potential outcome of a hypothetical intervention or change to a given scenario, providing insights into 'what if' questions using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scenario_description": {"type": "string", "description": "A description of the current scenario."},
                "hypothetical_change": {"type": "string", "description": "A description of the hypothetical change or intervention."},
                "factors_involved": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: Key factors involved in the scenario that might be affected by the change."
                }
            },
            "required": ["scenario_description", "hypothetical_change"]
        }

    def execute(self, scenario_description: str, hypothetical_change: str, factors_involved: Optional[List[str]] = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered counterfactual reasoning."})

        factors_str = f"Factors involved: {', '.join(factors_involved)}." if factors_involved else ""
        prompt = f"Simulate the potential outcome of the following hypothetical change: '{hypothetical_change}' in the scenario: '{scenario_description}'. {factors_str} Provide a detailed simulated outcome, including potential impacts and consequences. Provide the output in JSON format with keys 'simulated_outcome', 'potential_impacts', and 'consequences'.\n\nJSON Output:"
        
        llm_response = counterfactual_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})