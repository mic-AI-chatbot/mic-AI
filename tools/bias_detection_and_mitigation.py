import logging
import json
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# --- Mock Data and Model for Bias Simulation (reused from ai_ethics_compliance_tool.py) ---
# This dataset has an inherent bias: Group B has lower feature values on average,
# leading to a biased outcome if a simple threshold model is used.
MOCK_DATASET = [
    {"feature1": 0.8, "group": "A"}, {"feature1": 0.9, "group": "A"},
    {"feature1": 0.7, "group": "A"}, {"feature1": 0.85, "group": "A"},
    {"feature1": 0.2, "group": "B"}, {"feature1": 0.3, "group": "B"},
    {"feature1": 0.1, "group": "B"}, {"feature1": 0.4, "group": "B"},
] * 20 # Multiply the dataset for a larger sample size

# A simple mock model that is biased based on the feature
def mock_model_predict(data_point: Dict[str, Any]) -> int:
    # The model is more likely to predict a positive outcome (1) if the feature is high.
    # This will inherently be biased against Group B due to their lower feature1 values.
    return 1 if data_point["feature1"] > 0.5 else 0

class DetectBiasTool(BaseTool):
    """Detects demographic bias in a simulated AI model by calculating the demographic parity fairness metric."""
    def __init__(self, tool_name="detect_bias"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Detects demographic bias in a simulated AI model by calculating the demographic parity fairness metric for a specified protected attribute."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "protected_attribute": {"type": "string", "description": "The protected attribute to check for bias against (e.g., 'group').", "default": "group"}
            },
            "required": []
        }

    def execute(self, protected_attribute: str = "group", **kwargs: Any) -> str:
        predictions = [mock_model_predict(d) for d in MOCK_DATASET]
        
        group_outcomes: Dict[str, Dict[str, int]] = {}
        for data, pred in zip(MOCK_DATASET, predictions):
            group = data[protected_attribute]
            if group not in group_outcomes:
                group_outcomes[group] = {"total": 0, "positive_outcomes": 0}
            group_outcomes[group]["total"] += 1
            if pred == 1:
                group_outcomes[group]["positive_outcomes"] += 1

        parity_report: Dict[str, float] = {}
        for group, outcomes in group_outcomes.items():
            parity_report[group] = outcomes["positive_outcomes"] / outcomes["total"] if outcomes["total"] > 0 else 0

        parity_values = list(parity_report.values())
        disparity = max(parity_values) - min(parity_values) if len(parity_values) > 1 else 0
        
        bias_detected = disparity > 0.2 # A common threshold for significant disparity

        report = {
            "bias_metric": "Demographic Parity",
            "protected_attribute": protected_attribute,
            "bias_detected": bias_detected,
            "demographic_parity_rates": {k: f"{v:.2f}" for k, v in parity_report.items()},
            "disparity": f"{disparity:.2f}",
            "summary": f"The model shows a disparity of {disparity:.2f} in positive outcomes between groups. A value > 0.2 is often considered indicative of bias." if bias_detected else "No significant demographic parity bias was detected."
        }
        return json.dumps(report, indent=2)

class MitigateBiasTool(BaseTool):
    """Suggests and simulates the effectiveness of mitigation strategies for AI bias."""
    def __init__(self, tool_name="mitigate_bias"):
        super().__init__(tool_name=tool_name)
        self.mitigation_strategies_db = {
            "re-sampling": "Adjust the training data to balance representation across protected groups (e.g., oversample minority, undersample majority). This is a pre-processing technique.",
            "re-weighting": "Assign different weights to samples in the training data to reduce the impact of bias. This is a pre-processing or in-processing technique.",
            "post-processing": "Adjust model predictions after they are made to ensure fairness (e.g., equalizing classification thresholds for different groups).",
            "in-processing": "Modify the model training algorithm itself to incorporate fairness constraints during the learning process."
        }

    @property
    def description(self) -> str:
        return "Suggests and simulates the effectiveness of mitigation strategies to reduce identified bias in a dataset or AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "bias_report_json": {
                    "type": "string",
                    "description": "The JSON bias detection report from the DetectBiasTool."
                },
                "mitigation_strategy": {
                    "type": "string",
                    "description": "The strategy to apply.",
                    "enum": list(self.mitigation_strategies_db.keys())
                }
            },
            "required": ["bias_report_json", "mitigation_strategy"]
        }

    def execute(self, bias_report_json: str, mitigation_strategy: str, **kwargs: Any) -> str:
        try:
            bias_report = json.loads(bias_report_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for the bias report."})

        if not bias_report.get("bias_detected"):
            return json.dumps({"message": "No bias was detected in the original report, so no mitigation is needed."})

        original_disparity = float(bias_report.get("disparity", 0))
        
        # Simulate effectiveness: reduce disparity by a random amount
        effectiveness_reduction = random.uniform(0.1, 0.5) # Reduce disparity by 10-50%  # nosec B311
        new_disparity = max(0, original_disparity * (1 - effectiveness_reduction))
        
        report = {
            "original_bias_report": bias_report,
            "mitigation_strategy_applied": mitigation_strategy,
            "strategy_description": self.mitigation_strategies_db.get(mitigation_strategy, "No description available."),
            "simulated_effectiveness": {
                "original_disparity": original_disparity,
                "new_simulated_disparity": round(new_disparity, 2),
                "reduction_percent": round(effectiveness_reduction * 100, 2)
            },
            "message": f"Simulated application of '{mitigation_strategy}' reduced the demographic disparity from {original_disparity:.2f} to {new_disparity:.2f}. Further evaluation is recommended."
        }
        return json.dumps(report, indent=2)