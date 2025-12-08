import logging
import json
import random
import numpy as np
from scipy import stats
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class Experiment:
    """Represents a single experiment with its design, data, and status."""
    def __init__(self, experiment_name: str, research_question: str, independent_variable: str, dependent_variable: str, control_group_size: int, treatment_group_size: int):
        self.experiment_name = experiment_name
        self.research_question = research_question
        self.independent_variable = independent_variable
        self.dependent_variable = dependent_variable
        self.control_group_size = control_group_size
        self.treatment_group_size = treatment_group_size
        self.status = "designed" # designed, executed, completed
        self.control_data: List[float] = []
        self.treatment_data: List[float] = []
        self.results: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_name": self.experiment_name,
            "research_question": self.research_question,
            "independent_variable": self.independent_variable,
            "dependent_variable": self.dependent_variable,
            "control_group_size": self.control_group_size,
            "treatment_group_size": self.treatment_group_size,
            "status": self.status,
            "control_data_sample": self.control_data[:5], # Show a sample of data
            "treatment_data_sample": self.treatment_data[:5],
            "results": self.results
        }

class ExperimentManager:
    """Manages all created experiments, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExperimentManager, cls).__new__(cls)
            cls._instance.experiments: Dict[str, Experiment] = {}
        return cls._instance

    def create_experiment(self, experiment_name: str, research_question: str, independent_variable: str, dependent_variable: str, control_group_size: int, treatment_group_size: int) -> Experiment:
        experiment = Experiment(experiment_name, research_question, independent_variable, dependent_variable, control_group_size, treatment_group_size)
        self.experiments[experiment_name] = experiment
        return experiment

    def get_experiment(self, experiment_name: str) -> Experiment:
        return self.experiments.get(experiment_name)

experiment_manager = ExperimentManager()

class DesignExperimentTool(BaseTool):
    """Designs a new experiment with specified variables and sample sizes."""
    def __init__(self, tool_name="design_experiment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Designs a new experiment, defining its research question, independent and dependent variables, and sample sizes for control and treatment groups."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "experiment_name": {"type": "string", "description": "A unique name for the experiment."},
                "research_question": {"type": "string", "description": "The research question the experiment aims to answer."},
                "independent_variable": {"type": "string", "description": "The variable that will be manipulated."},
                "dependent_variable": {"type": "string", "description": "The variable that will be measured."},
                "control_group_size": {"type": "integer", "description": "The number of participants in the control group.", "default": 50},
                "treatment_group_size": {"type": "integer", "description": "The number of participants in the treatment group.", "default": 50}
            },
            "required": ["experiment_name", "research_question", "independent_variable", "dependent_variable"]
        }

    def execute(self, experiment_name: str, research_question: str, independent_variable: str, dependent_variable: str, control_group_size: int = 50, treatment_group_size: int = 50, **kwargs: Any) -> str:
        if experiment_name in experiment_manager.experiments:
            return json.dumps({"error": f"Experiment '{experiment_name}' already exists."})
        
        experiment = experiment_manager.create_experiment(experiment_name, research_question, independent_variable, dependent_variable, control_group_size, treatment_group_size)
        
        report = {
            "message": f"Experiment '{experiment_name}' designed successfully.",
            "experiment_details": experiment.to_dict()
        }
        return json.dumps(report, indent=2)

class ExecuteExperimentTool(BaseTool):
    """Simulates the execution of an experiment and generates mock data."""
    def __init__(self, tool_name="execute_experiment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates the execution of a designed experiment and generates mock data for control and treatment groups."

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
        experiment = experiment_manager.get_experiment(experiment_name)
        if not experiment:
            return json.dumps({"error": f"Experiment '{experiment_name}' not found."})
        if experiment.status != "designed":
            return json.dumps({"error": f"Experiment '{experiment_name}' is not in 'designed' status. Current status: {experiment.status}. Please design it first."})

        # Generate mock data
        control_mean = 100
        control_std = 15
        experiment.control_data = np.random.normal(control_mean, control_std, experiment.control_group_size).tolist()
        
        treatment_mean = control_mean + treatment_effect_magnitude
        experiment.treatment_data = np.random.normal(treatment_mean, control_std, experiment.treatment_group_size).tolist()
        
        experiment.status = "executed"
        
        report = {
            "message": f"Experiment '{experiment_name}' executed successfully. Mock data generated.",
            "experiment_details": experiment.to_dict()
        }
        return json.dumps(report, indent=2)

class AnalyzeExperimentResultsTool(BaseTool):
    """Analyzes the results of an executed experiment using statistical tests."""
    def __init__(self, tool_name="analyze_experiment_results"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes the results of a completed experiment using statistical tests (e.g., t-test) to determine significance."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"experiment_name": {"type": "string", "description": "The name of the experiment to analyze results for."}},
            "required": ["experiment_name"]
        }

    def execute(self, experiment_name: str, **kwargs: Any) -> str:
        experiment = experiment_manager.get_experiment(experiment_name)
        if not experiment:
            return json.dumps({"error": f"Experiment '{experiment_name}' not found."})
        if experiment.status != "executed":
            return json.dumps({"error": f"Experiment '{experiment_name}' has not been executed. Current status: {experiment.status}. Please execute it first."})

        # Perform an independent samples t-test
        t_stat, p_value = stats.ttest_ind(experiment.control_data, experiment.treatment_data)
        
        alpha = 0.05 # Common significance level
        statistical_significance = "Yes" if p_value < alpha else "No"
        
        conclusions = f"Based on the independent samples t-test (t-statistic={t_stat:.3f}, p-value={p_value:.3f}), we {'do' if p_value < alpha else 'do not'} have sufficient evidence to reject the null hypothesis at the {alpha*100}% significance level. The treatment {'had a statistically significant effect' if p_value < alpha else 'did not have a statistically significant effect'} on the dependent variable."

        experiment.results = {
            "t_statistic": round(t_stat, 3),
            "p_value": round(p_value, 3),
            "alpha": alpha,
            "statistical_significance": statistical_significance,
            "conclusions": conclusions
        }
        experiment.status = "completed"
        
        return json.dumps(experiment.to_dict(), indent=2)