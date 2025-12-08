import logging
import json
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Automated policy generation tools will not be available.")

logger = logging.getLogger(__name__)

class PolicyGenerationModel:
    """Manages the text generation model for policy generation and review, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PolicyGenerationModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for policy generation are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for policy generation...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

policy_model_instance = PolicyGenerationModel()

class GeneratePolicyTool(BaseTool):
    """Generates a new policy based on a topic and requirements using an AI model."""
    def __init__(self, tool_name="generate_policy"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a new policy (e.g., data privacy, security access) based on a specified type and requirements using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "policy_type": {"type": "string", "description": "The type of policy to generate (e.g., 'Data Privacy', 'Security Access', 'Remote Work', 'AI Ethics')."},
                "requirements": {
                    "type": "object",
                    "description": "A dictionary of requirements or parameters for the policy (e.g., {\"scope\": \"global\", \"data_types\": [\"PII\"]})."
                }
            },
            "required": ["policy_type", "requirements"]
        }

    def execute(self, policy_type: str, requirements: Dict[str, Any], **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        requirements_str = json.dumps(requirements)
        prompt = f"Generate a comprehensive '{policy_type}' policy based on the following requirements: {requirements_str}. The policy should include an introduction, scope, key principles, and specific rules. Policy:"
        
        generated_policy_content = policy_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        report = {
            "policy_type": policy_type,
            "requirements": requirements,
            "generated_policy_content": generated_policy_content
        }
        return json.dumps(report, indent=2)

class ReviewPolicyTool(BaseTool):
    """Reviews a generated policy for completeness, clarity, and compliance using an AI model."""
    def __init__(self, tool_name="review_policy"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Reviews a generated policy for completeness, clarity, and compliance with best practices, providing feedback using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "policy_type": {"type": "string", "description": "The type of policy being reviewed."},
                "policy_content": {"type": "string", "description": "The full content of the policy to review."
                }
            },
            "required": ["policy_type", "policy_content"]
        }

    def execute(self, policy_type: str, policy_content: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Review the following '{policy_type}' policy for clarity, completeness, and adherence to best practices. Provide constructive feedback and suggest improvements.\n\nPolicy:\n{policy_content}\n\nFeedback:"
        
        generated_feedback = policy_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 300)
        
        report = {
            "policy_type": policy_type,
            "policy_content_sample": policy_content[:200] + "..." if len(policy_content) > 200 else policy_content,
            "review_feedback": generated_feedback
        }
        return json.dumps(report, indent=2)