import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

# Deferring transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered threat analysis will not be available.")

logger = logging.getLogger(__name__)

THREAT_INTELLIGENCE_FILE = Path("threat_intelligence.json")

class ThreatIntelligenceManager:
    """Manages threat intelligence data, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = THREAT_INTELLIGENCE_FILE):
        if cls._instance is None:
            cls._instance = super(ThreatIntelligenceManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.threats: Dict[str, Any] = cls._instance._load_threat_intelligence()
        return cls._instance

    def _load_threat_intelligence(self) -> Dict[str, Any]:
        """Loads threat intelligence data from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty threat intelligence.")
                return {}
            except Exception as e:
                logger.error(f"Error loading threat intelligence from {self.file_path}: {e}")
                return {}
        # Initial dummy data if file doesn't exist
        return {
            "threat_1": {"type": "malware", "indicator": "malicious.com", "severity": "high", "description": "Phishing site distributing malware.", "last_seen": datetime.now().isoformat() + "Z"},
            "threat_2": {"type": "phishing", "indicator": "phish.net", "severity": "medium", "description": "Credential harvesting site.", "last_seen": datetime.now().isoformat() + "Z"},
            "threat_3": {"type": "vulnerability", "indicator": "CVE-2023-XXXX", "severity": "critical", "description": "Zero-day exploit in popular software.", "last_seen": datetime.now().isoformat() + "Z"}
        }

    def _save_threat_intelligence(self) -> None:
        """Saves threat intelligence data to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.threats, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving threat intelligence to {self.file_path}: {e}")

    def add_threat_indicator(self, threat_id: str, threat_type: str, indicator: str, severity: str, description: str) -> bool:
        if threat_id in self.threats:
            return False
        self.threats[threat_id] = {
            "type": threat_type,
            "indicator": indicator,
            "severity": severity,
            "description": description,
            "last_seen": datetime.now().isoformat() + "Z"
        }
        self._save_threat_intelligence()
        return True

    def get_threat_indicator(self, threat_id: str) -> Optional[Dict[str, Any]]:
        return self.threats.get(threat_id)

    def list_threats(self, threat_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not threat_type or threat_type == "all":
            return [{"id": t_id, "type": details['type'], "indicator": details['indicator'], "severity": details['severity'], "last_seen": details['last_seen']} for t_id, details in self.threats.items()]
        
        filtered_list = []
        for t_id, details in self.threats.items():
            if details['type'] == threat_type:
                filtered_list.append({"id": t_id, "type": details['type'], "indicator": details['indicator'], "severity": details['severity'], "last_seen": details['last_seen']})
        return filtered_list

    def search_threats(self, query: str) -> List[Dict[str, Any]]:
        found_threats = []
        for t_id, details in self.threats.items():
            if query.lower() in details['indicator'].lower() or query.lower() in details['description'].lower():
                found_threats.append({"id": t_id, "type": details['type'], "indicator": details['indicator'], "severity": details['severity'], "description": details['description'], "last_seen": details['last_seen']})
        return found_threats

threat_intelligence_manager = ThreatIntelligenceManager()

class ThreatAnalysisModel:
    """Manages the text generation model for AI-powered threat analysis, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThreatAnalysisModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for threat analysis are not installed.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for threat analysis...")
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

threat_analysis_model_instance = ThreatAnalysisModel()

class AddThreatIndicatorTool(BaseTool):
    """Adds a new cyber threat indicator to the intelligence database."""
    def __init__(self, tool_name="add_threat_indicator"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new cyber threat indicator (e.g., malicious IP, domain, file hash) to the intelligence database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "threat_id": {"type": "string", "description": "A unique ID for the threat indicator."},
                "threat_type": {"type": "string", "description": "The type of threat.", "enum": ["malware", "phishing", "vulnerability", "ip_address", "domain", "file_hash"]},
                "indicator": {"type": "string", "description": "The actual indicator value (e.g., 'malicious.com', '192.168.1.1')."},
                "severity": {"type": "string", "description": "The severity of the threat.", "enum": ["low", "medium", "high", "critical"]},
                "description": {"type": "string", "description": "A brief description of the threat."}
            },
            "required": ["threat_id", "threat_type", "indicator", "severity", "description"]
        }

    def execute(self, threat_id: str, threat_type: str, indicator: str, severity: str, description: str, **kwargs: Any) -> str:
        success = threat_intelligence_manager.add_threat_indicator(threat_id, threat_type, indicator, severity, description)
        if success:
            report = {"message": f"Threat indicator '{threat_id}' ('{indicator}') added successfully."}
        else:
            report = {"error": f"Threat indicator with ID '{threat_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class GetLatestThreatsTool(BaseTool):
    """Retrieves the latest threat intelligence."""
    def __init__(self, tool_name="get_latest_threats"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the latest threat intelligence, optionally filtered by threat type."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "threat_type": {"type": "string", "description": "The type of threat to retrieve.", "enum": ["all", "malware", "phishing", "vulnerability", "ip_address", "domain", "file_hash"], "default": "all"}
            },
            "required": []
        }

    def execute(self, threat_type: str = "all", **kwargs: Any) -> str:
        threats = threat_intelligence_manager.list_threats(threat_type)
        if not threats:
            return json.dumps({"message": "No threat intelligence found matching the criteria."})
        
        return json.dumps({"total_threats": len(threats), "threats": threats}, indent=2)

class AnalyzeThreatIndicatorTool(BaseTool):
    """Analyzes a specific threat indicator using an AI model."""
    def __init__(self, tool_name="analyze_threat_indicator"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a specific threat indicator (e.g., IP address, domain, file hash) to determine its nature and associated risks using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "indicator_value": {"type": "string", "description": "The value of the threat indicator to analyze (e.g., 'malicious.com', '192.168.1.1')."},
                "indicator_type": {"type": "string", "description": "The type of the indicator.", "enum": ["ip_address", "domain", "file_hash"]}
            },
            "required": ["indicator_value", "indicator_type"]
        }

    def execute(self, indicator_value: str, indicator_type: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered threat analysis."})

        prompt = f"Analyze the cyber threat indicator '{indicator_value}' of type '{indicator_type}'. Determine its nature, associated risks, and provide recommendations for mitigation. Provide the output in JSON format with keys 'analysis_summary', 'risk_assessment', and 'mitigation_recommendations'.\n\nJSON Output:"
        
        llm_response = threat_analysis_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class SearchThreatIntelligenceTool(BaseTool):
    """Searches for threat intelligence based on a query."""
    def __init__(self, tool_name="search_threat_intelligence"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Searches for threat intelligence based on a keyword or phrase in indicators or descriptions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The keyword or phrase to search for."}},
            "required": ["query"]
        }

    def execute(self, query: str, **kwargs: Any) -> str:
        threats = threat_intelligence_manager.search_threats(query)
        if not threats:
            return json.dumps({"message": f"No threat intelligence found matching query: '{query}'."})
        
        return json.dumps({"total_threats": len(threats), "threats": threats}, indent=2)