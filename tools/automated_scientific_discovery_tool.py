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
    logging.warning("transformers library not found. Automated scientific discovery tools will not be available.")

# Import tools from automated_experiment_design.py
try:
    from .automated_experiment_design import experiment_manager, DesignExperimentTool as AED_DesignExperimentTool, ExecuteExperimentTool as AED_ExecuteExperimentTool, AnalyzeExperimentResultsTool as AED_AnalyzeExperimentResultsTool
    AED_TOOLS_AVAILABLE = True
except ImportError:
    AED_TOOLS_AVAILABLE = False
    logging.warning("automated_experiment_design.py tools not found. Experiment design, execution, and analysis will be limited.")

logger = logging.getLogger(__name__)

class ScientificDiscoveryModel:
    """Manages the text generation model for scientific discovery tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScientificDiscoveryModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for scientific discovery are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for scientific discovery...")
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

scientific_discovery_model_instance = ScientificDiscoveryModel()

class FormulateHypothesisTool(BaseTool):
    """Formulates a testable hypothesis based on a research question using an AI model."""
    def __init__(self, tool_name="formulate_hypothesis"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Formulates a testable scientific hypothesis based on a given research question, suitable for experimental design, using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"research_question": {"type": "string", "description": "The research question for which to formulate a hypothesis."}},
            "required": ["research_question"]
        }

    def execute(self, research_question: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Formulate a testable scientific hypothesis for the following research question: '{research_question}'. The hypothesis should be clear and concise. Hypothesis:"
        
        generated_hypothesis = scientific_discovery_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 100)
        
        report = {
            "research_question": research_question,
            "formulated_hypothesis": generated_hypothesis
        }
        return json.dumps(report, indent=2)

class DesignScientificExperimentTool(BaseTool):
    """Designs a scientific experiment based on a hypothesis, leveraging the automated_experiment_design tools."""
    def __init__(self, tool_name="design_scientific_experiment"):
        super().__init__(tool_name=tool_name)
        self.aed_design_tool = AED_DesignExperimentTool()

    @property
    def description(self) -> str:
        return "Designs a scientific experiment based on a hypothesis, specifying methodology, controls, and data collection, leveraging the automated_experiment_design tools."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "experiment_name": {"type": "string", "description": "A unique name for the experiment."},
                "hypothesis": {"type": "string", "description": "The hypothesis to be tested (e.g., from FormulateHypothesisTool)."},
                "independent_variable": {"type": "string", "description": "The independent variable of the experiment."},
                "dependent_variable": {"type": "string", "description": "The dependent variable of the experiment."},
                "control_group_size": {"type": "integer", "description": "The number of participants in the control group.", "default": 50},
                "treatment_group_size": {"type": "integer", "description": "The number of participants in the treatment group.", "default": 50},
                "data_collection_method": {"type": "string", "description": "The method for data collection (e.g., 'surveys', 'observations', 'sensor_data')."}
            },
            "required": ["experiment_name", "hypothesis", "independent_variable", "dependent_variable", "data_collection_method"]
        }

    def execute(self, experiment_name: str, hypothesis: str, independent_variable: str, dependent_variable: str, data_collection_method: str, control_group_size: int = 50, treatment_group_size: int = 50, **kwargs: Any) -> str:
        if not AED_TOOLS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'automated_experiment_design.py' tools to be available. Please ensure the file exists and is correctly implemented."})

        # Use the AED_DesignExperimentTool to create the experiment
        design_report_json = self.aed_design_tool.execute(
            experiment_name=experiment_name,
            research_question=hypothesis, # Using hypothesis as research question for AED tool
            independent_variable=independent_variable,
            dependent_variable=dependent_variable,
            control_group_size=control_group_size,
            treatment_group_size=treatment_group_size
        )
        
        design_report = json.loads(design_report_json)
        if "error" in design_report:
            return json.dumps({"error": f"Failed to design experiment: {design_report['error']}"})

        report = {
            "message": f"Scientific experiment '{experiment_name}' designed successfully.",
            "experiment_details": design_report["experiment_details"],
            "data_collection_method": data_collection_method
        }
        return json.dumps(report, indent=2)

class ExecuteScientificExperimentTool(BaseTool):
    """Executes a designed scientific experiment, leveraging the automated_experiment_design tools."""
    def __init__(self, tool_name="execute_scientific_experiment"):
        super().__init__(tool_name=tool_name)
        self.aed_execute_tool = AED_ExecuteExperimentTool()

    @property
    def description(self) -> str:
        return "Simulates the execution of a designed scientific experiment and generates mock data, leveraging the automated_experiment_design tools."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "experiment_name": {"type": "string", "description": "The name of the experiment to execute."},
                "treatment_effect_magnitude": {"type": "number", "description": "Magnitude of the simulated treatment effect (e.g., 0 for no effect, 10 for strong positive effect).", "default": 0}
            },
            "required": ["experiment_name"]
        }

    def execute(self, experiment_name: str, treatment_effect_magnitude: float = 0, **kwargs: Any) -> str:
        if not AED_TOOLS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'automated_experiment_design.py' tools to be available. Please ensure the file exists and is correctly implemented."})

        execute_report_json = self.aed_execute_tool.execute(
            experiment_name=experiment_name,
            treatment_effect_magnitude=treatment_effect_magnitude
        )
        
        execute_report = json.loads(execute_report_json)
        if "error" in execute_report:
            return json.dumps({"error": f"Failed to execute experiment: {execute_report['error']}"})

        return json.dumps(execute_report, indent=2)

class AnalyzeScientificExperimentResultsTool(BaseTool):
    """Analyzes the results of an executed scientific experiment, leveraging the automated_experiment_design tools."""
    def __init__(self, tool_name="analyze_scientific_experiment_results"):
        super().__init__(tool_name=tool_name)
        self.aed_analyze_tool = AED_AnalyzeExperimentResultsTool()

    @property
    def description(self) -> str:
        return "Analyzes the results of an executed scientific experiment using statistical tests, leveraging the automated_experiment_design tools."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"experiment_name": {"type": "string", "description": "The name of the experiment to analyze results for."}},
            "required": ["experiment_name"]
        }

    def execute(self, experiment_name: str, **kwargs: Any) -> str:
        if not AED_TOOLS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'automated_experiment_design.py' tools to be available. Please ensure the file exists and is correctly implemented."})

        analyze_report_json = self.aed_analyze_tool.execute(
            experiment_name=experiment_name
        )
        
        analyze_report = json.loads(analyze_report_json)
        if "error" in analyze_report:
            return json.dumps({"error": f"Failed to analyze experiment results: {analyze_report['error']}"})

        return json.dumps(analyze_report, indent=2)