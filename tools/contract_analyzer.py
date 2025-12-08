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
    logging.warning("transformers library not found. AI-powered contract analysis will not be available.")

logger = logging.getLogger(__name__)

class ContractAnalysisModel:
    """Manages the text generation model for contract analysis tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContractAnalysisModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for contract analysis are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for contract analysis...")
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

contract_analysis_model_instance = ContractAnalysisModel()

class AnalyzeContractTool(BaseTool):
    """Analyzes a contract for key clauses, terms, and obligations using an AI model."""
    def __init__(self, tool_name="analyze_contract"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a contract text to identify key clauses, terms, and obligations based on a specified analysis type using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "contract_text": {"type": "string", "description": "The full text of the contract to analyze."},
                "analysis_type": {"type": "string", "description": "The type of analysis to perform.", "enum": ["key_clauses", "obligations", "terms"], "default": "key_clauses"}
            },
            "required": ["contract_text"]
        }

    def execute(self, contract_text: str, analysis_type: str = "key_clauses", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered analysis."})

        prompt = f"Analyze the following contract text and identify the {analysis_type}. Provide the findings in JSON format with a key 'findings' which is a list of strings.\n\nContract Text:\n{contract_text}\n\nJSON Output:"
        
        llm_response = contract_analysis_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class IdentifyContractRisksTool(BaseTool):
    """Identifies potential risks within a contract using an AI model."""
    def __init__(self, tool_name="identify_contract_risks"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Identifies potential risks (e.g., ambiguous language, missing clauses, unfavorable terms) within a contract text using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "contract_text": {"type": "string", "description": "The full text of the contract to analyze for risks."},
                "risk_categories": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["financial", "legal", "operational"]},
                    "description": "Specific categories of risks to look for.",
                    "default": ["financial", "legal", "operational"]
                }
            },
            "required": ["contract_text"]
        }

    def execute(self, contract_text: str, risk_categories: List[str] = ["financial", "legal", "operational"], **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered analysis."})

        prompt = f"Analyze the following contract text for potential risks, focusing on the following categories: {', '.join(risk_categories)}. For each identified risk, provide its category, a description, severity (low, medium, high), and a recommendation. Provide the output in JSON format with a key 'risks_identified' which is a list of objects, each with 'category', 'description', 'severity', and 'recommendation' keys.\n\nContract Text:\n{contract_text}\n\nJSON Output:"
        
        llm_response = contract_analysis_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})