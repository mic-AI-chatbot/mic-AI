import logging
import json
from typing import Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Automated contract reviewer will not be available.")

logger = logging.getLogger(__name__)

class ContractReviewModel:
    """Manages the text generation model for contract review, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContractReviewModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for contract review are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for contract review...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def review_contract(self, contract_text: str) -> Dict[str, Any]:
        if not self._generator:
            return {"error": "Text generation model not available. Check logs for loading errors."}

        prompt = f"""Analyze the following legal contract and extract the following key information:
- Parties involved
- Effective Date
- Term of the contract
- Key obligations of each party
- Termination clauses
- Governing Law

Contract Text:
{contract_text}

Extracted Information (in JSON format):
"""
        try:
            # Generate a response that attempts to be JSON
            # max_length is set to be longer than the prompt to allow for generation
            generated_text = self._generator(prompt, max_length=len(prompt.split()) + 300, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            
            # Attempt to parse the generated text as JSON
            # The model might not always produce perfect JSON, so we need robust parsing
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_str = generated_text[json_start:json_end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse generated JSON: {json_str}")
                    return {"raw_output": generated_text, "error": "Generated output was not valid JSON. Manual parsing needed."}
            else:
                return {"raw_output": generated_text, "error": "Could not find JSON in generated output. Manual parsing needed."}

        except Exception as e:
            logger.error(f"Contract review failed: {e}")
            return {"error": f"An error occurred during contract review: {e}"}

contract_review_instance = ContractReviewModel()

class AutomatedContractReviewerTool(BaseTool):
    """Extracts key clauses, dates, and obligations from legal contracts using an AI model."""
    def __init__(self, tool_name="automated_contract_reviewer"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes legal contract text to extract key information such as parties, effective date, term, obligations, and termination clauses, returning a structured JSON report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"contract_text": {"type": "string", "description": "The full text of the legal contract to review."}},
            "required": ["contract_text"]
        }

    def execute(self, contract_text: str, **kwargs: Any) -> str:
        results = contract_review_instance.review_contract(contract_text)
        return json.dumps(results, indent=2)
