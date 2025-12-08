import logging
import json
import random
from typing import Union, List, Dict, Any, Optional
from tools.base_tool import BaseTool

# Deferring transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered threat hunting will not be available.")

# Import ThreatIntelligenceManager from cyber_threat_intelligence_tool.py
try:
    from .cyber_threat_intelligence_tool import threat_intelligence_manager
    THREAT_INTEL_AVAILABLE = True
except ImportError:
    threat_intelligence_manager = None
    THREAT_INTEL_AVAILABLE = False
    logging.warning("ThreatIntelligenceManager from cyber_threat_intelligence_tool.py not found. Threat indicator analysis will be simulated.")

logger = logging.getLogger(__name__)

class ThreatHuntingModel:
    """Manages the text generation model for AI-powered threat hunting, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThreatHuntingModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for threat hunting are not installed.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for threat hunting...")
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

threat_hunting_model_instance = ThreatHuntingModel()

class HuntThreatsTool(BaseTool):
    """Proactively searches for threats in a network or system using an AI model."""
    def __init__(self, tool_name="hunt_threats"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Proactively searches for threats within a specified scope (e.g., network, endpoint) using various hunting techniques and an AI model to generate findings."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "description": "The scope of the threat hunt.", "enum": ["network", "endpoint", "cloud_environment"]},
                "techniques": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["behavioral_analysis", "log_analysis", "malware_analysis", "vulnerability_scanning"]},
                    "description": "A list of threat hunting techniques to employ."
                }
            },
            "required": ["scope", "techniques"]
        }

    def execute(self, scope: str, techniques: List[str], **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered threat hunting."})

        techniques_str = ", ".join(techniques)
        prompt = f"Simulate a threat hunt in the '{scope}' scope using the following techniques: {techniques_str}. Generate 1-3 plausible threat hunting findings, including the threat type, severity (low, medium, high, critical), description, and simulated evidence. Provide the output in JSON format with a key 'threat_findings' which is a list of objects, each with 'type', 'severity', 'description', and 'evidence' keys.\n\nJSON Output:"
        
        llm_response = threat_hunting_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class AnalyzeThreatIndicatorsTool(BaseTool):
    """Analyzes specific threat indicators found during a hunt using an AI model."""
    def __init__(self, tool_name="analyze_threat_indicators"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes specific threat indicators (e.g., IP addresses, domains, file hashes) identified during a threat hunt to determine their nature and associated risks using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "indicator_value": {"type": "string", "description": "The value of the threat indicator to analyze (e.g., '192.168.1.1', 'malicious.com')."},
                "indicator_type": {"type": "string", "description": "The type of the indicator.", "enum": ["ip_address", "domain", "file_hash"]}
            },
            "required": ["indicator_value", "indicator_type"]
        }

    def execute(self, indicator_value: str, indicator_type: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered threat analysis."})

        # Integrate with cyber_threat_intelligence_tool.py if available
        threat_intel_context = "No external threat intelligence available."
        if THREAT_INTEL_AVAILABLE and threat_intelligence_manager:
            threat_intel_report = threat_intelligence_manager.search_threats(indicator_value)
            if threat_intel_report:
                threat_intel_context = f"Relevant threat intelligence: {json.dumps(threat_intel_report)}"

        prompt = f"Analyze the cyber threat indicator '{indicator_value}' of type '{indicator_type}'. Consider the following threat intelligence: {threat_intel_context}. Determine its nature, associated risks, and provide recommendations for mitigation. Provide the output in JSON format with keys 'analysis_summary', 'risk_assessment', and 'mitigation_recommendations'.\n\nJSON Output:"
        
        llm_response = threat_hunting_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})