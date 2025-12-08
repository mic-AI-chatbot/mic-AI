import logging
import json
import random
import re
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Cognitive bias detection tools will not be fully functional.")

logger = logging.getLogger(__name__)

class BiasDetectorModel:
    """Manages the text generation model for cognitive bias detection and explanation, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BiasDetectorModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for bias detection are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for bias detection...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

bias_detector_model_instance = BiasDetectorModel()

class AnalyzeTextForBiasTool(BaseTool):
    """Analyzes a given text for common cognitive biases using an AI model."""
    def __init__(self, tool_name="analyze_text_for_bias"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a given text for common cognitive biases (e.g., confirmation bias, anchoring bias, bandwagon effect) and reports potential biases detected using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The text to analyze for cognitive biases."}},
            "required": ["text"]
        }

    def execute(self, text: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Analyze the following text for common cognitive biases (e.g., confirmation bias, anchoring bias, bandwagon effect, availability heuristic). For each detected bias, provide its name, a brief explanation of why it might be present, and a suggestion to mitigate it. Provide the output in JSON format with a key 'detected_biases' which is a list of objects, each with 'name', 'explanation', and 'mitigation_suggestion' keys.\n\nText:\n{text}\n\nJSON Output:"
        
        llm_response = bias_detector_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class GetCognitiveBiasDefinitionTool(BaseTool):
    """Provides definitions and examples of common cognitive biases using an AI model."""
    def __init__(self, tool_name="get_cognitive_bias_definition"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Provides a definition and example of a specified common cognitive bias using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"bias_name": {"type": "string", "description": "The name of the cognitive bias to get a definition for (e.g., 'confirmation bias', 'anchoring bias')."}},
            "required": ["bias_name"]
        }

    def execute(self, bias_name: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Provide a clear definition and a concrete example for the cognitive bias '{bias_name}'. Provide the output in JSON format with keys 'bias_name', 'definition', and 'example'.\n\nJSON Output:"
        
        llm_response = bias_detector_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 300)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})