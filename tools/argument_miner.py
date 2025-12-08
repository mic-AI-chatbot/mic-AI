import logging
import json
import re
from typing import List, Dict, Any
from tools.base_tool import BaseTool

try:
    from transformers import pipeline
    import spacy
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers or spacy not found. Argument mining tools will not be available.")

logger = logging.getLogger(__name__)

class ArgumentMiningModel:
    """Manages the NLP models for argument mining, using a lazy-loading singleton pattern."""
    _instance = None
    _classifier = None
    _nlp = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ArgumentMiningModel, cls).__new__(cls)
        return cls._instance

    def _load_models(self):
        """Lazily loads the NLP models on first use."""
        if self._classifier is None or self._nlp is None:
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for argument mining are not installed. Please install 'transformers' and 'spacy'.")
                self._classifier = self._nlp = "unavailable"
                return

            try:
                # Load classifier
                if self._classifier is None:
                    logger.info("Initializing zero-shot classification model for argument mining...")
                    self._classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
                    logger.info("Zero-shot classification model loaded.")
                
                # Load spaCy model
                if self._nlp is None:
                    logger.info("Initializing spaCy model 'en_core_web_sm'...")
                    self._nlp = spacy.load("en_core_web_sm")
                    logger.info("spaCy model loaded.")

            except Exception as e:
                logger.error(f"Failed to load NLP models for argument mining: {e}")
                # Mark as unavailable to prevent retries
                if self._classifier is None: self._classifier = "unavailable"
                if self._nlp is None: self._nlp = "unavailable"

    def extract_arguments(self, text: str) -> List[Dict[str, Any]]:
        self._load_models() # Ensure models are loaded

        if self._classifier == "unavailable" or self._nlp == "unavailable" or not self._classifier or not self._nlp:
            return [{"error": "NLP models for argument mining are not available. Check logs for details."}]
            
        doc = self._nlp(text)
        sentences = [sent.text for sent in doc.sents if len(sent.text.strip()) > 10]
        
        if not sentences:
            return []

        candidate_labels = ["claim", "premise", "evidence"]
        results = self._classifier(sentences, candidate_labels, multi_label=False)
        
        extracted_args = []
        for i, res in enumerate(results):
            extracted_args.append({
                "sentence": res["sequence"],
                "argument_type": res["labels"][0],
                "confidence": round(res["scores"][0], 2)
            })
        return extracted_args

argument_miner_instance = ArgumentMiningModel()

class ExtractArgumentsTool(BaseTool):
    """Extracts arguments (claims, premises, evidence) from text using a zero-shot classification model."""
    def __init__(self, tool_name="extract_arguments"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a text to identify and classify sentences as claims, premises, or evidence using a zero-shot NLP model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The text to analyze."}},
            "required": ["text"]
        }

    def execute(self, text: str, **kwargs: Any) -> str:
        arguments = argument_miner_instance.extract_arguments(text)
        return json.dumps(arguments, indent=2)

class AnalyzeArgumentStructureTool(BaseTool):
    """Analyzes the structure and coherence of extracted arguments."""
    def __init__(self, tool_name="analyze_argument_structure"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes the logical structure of extracted arguments, checking if claims are supported by premises."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"extracted_arguments_json": {"type": "string", "description": "The JSON output from the ExtractArgumentsTool."}},
            "required": ["extracted_arguments_json"]
        }

    def execute(self, extracted_arguments_json: str, **kwargs: Any) -> str:
        try:
            args = json.loads(extracted_arguments_json)
            if not isinstance(args, list) or (args and "argument_type" not in args[0]):
                 return json.dumps({"error": "Invalid input format. Expected a JSON list of argument objects."})
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for arguments."})

        claims = [arg for arg in args if arg.get("argument_type") == "claim"]
        premises = [arg for arg in args if arg.get("argument_type") == "premise"]
        
        analysis = []
        if not claims:
            analysis.append("The text does not appear to contain any clear claims.")
        elif not premises:
            analysis.append("The text makes claims but provides no clear supporting premises or reasons.")
        else:
            analysis.append(f"The text presents {len(claims)} claim(s) that appear to be supported by {len(premises)} premise(s).")

        report = {"structural_analysis": analysis}
        return json.dumps(report, indent=2)

class DetectLogicalFallacyTool(BaseTool):
    """Simulates the detection of common logical fallacies using pattern matching."""
    def __init__(self, tool_name="detect_logical_fallacy"):
        super().__init__(tool_name=tool_name)
        self.fallacy_patterns = {
            "Ad Hominem": r"\bis (an idiot|stupid|a fool|dishonest)\b",
            "Straw Man": r"so you're saying that|so what you're really saying is",
            "Slippery Slope": r"\bif we allow this, then what's next\b"
        }

    @property
    def description(self) -> str:
        return "Simulates the detection of common logical fallacies (e.g., Ad Hominem, Straw Man) in a text using pattern matching."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The text to analyze for fallacies."}},
            "required": ["text"]
        }

    def execute(self, text: str, **kwargs: Any) -> str:
        detected_fallacies = []
        for fallacy, pattern in self.fallacy_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                detected_fallacies.append({
                    "fallacy_type": fallacy,
                    "suspicious_phrase": match.group(0),
                    "explanation": f"The text may contain an '{fallacy}' fallacy. This is a simulation based on pattern matching."
                })
        
        if not detected_fallacies:
            report = {"message": "No obvious logical fallacies were detected based on the simulated patterns."}
        else:
            report = {"detected_fallacies": detected_fallacies}
            
        return json.dumps(report, indent=2)