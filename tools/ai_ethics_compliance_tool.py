import logging
import json
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# --- Mock Data and Model for Bias Simulation ---
# A simple dataset where a protected attribute ('group') is correlated with the outcome.
# Group B has a lower feature value on average, which will lead to a biased outcome.
MOCK_DATASET = [
    {"feature1": 0.8, "group": "A"}, {"feature1": 0.9, "group": "A"},
    {"feature1": 0.7, "group": "A"}, {"feature1": 0.85, "group": "A"},
    {"feature1": 0.2, "group": "B"}, {"feature1": 0.3, "group": "B"},
    {"feature1": 0.1, "group": "B"}, {"feature1": 0.4, "group": "B"},
] * 20 # Multiply the dataset for a larger sample size

# A simple mock model that is biased based on the feature
def mock_model_predict(data_point: Dict[str, Any]) -> int:
    # The model is more likely to predict a positive outcome (1) if the feature is high.
    return 1 if data_point["feature1"] > 0.5 else 0

# --- Detailed Ethical Guidelines ---
ETHICAL_GUIDELINES_DB = {
    "Data Privacy": "Implement data minimization, collecting only necessary data. Use anonymization and strong encryption. Be transparent with users about data collection, usage, and their rights.",
    "Algorithmic Bias": "Regularly audit training data and models for biases across demographic groups. Use fairness metrics (e.g., Demographic Parity, Equal Opportunity) to evaluate performance. Employ bias mitigation techniques during pre-processing, in-processing, or post-processing.",
    "Human Oversight": "Ensure meaningful human oversight in all high-stakes AI systems. Design clear processes for users to appeal or challenge automated decisions and receive a human review.",
    "Transparency": "Maintain clear, accessible documentation about the AI system's purpose, capabilities, and limitations. Use explainable AI (XAI) techniques like SHAP or LIME where appropriate to make decisions understandable.",
    "Accountability": "Establish clear lines of responsibility for the AI system's development, deployment, and ongoing monitoring. Maintain detailed and immutable logs for auditing and tracing decisions."
}

class CheckAIBiasTool(BaseTool):
    """Tool to check an AI model for demographic bias using a simulated dataset."""
    def __init__(self, tool_name="check_ai_bias"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Checks for demographic bias in a simulated AI model by calculating the demographic parity fairness metric."

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

class GenerateEthicalGuidelinesTool(BaseTool):
    """Tool to generate detailed ethical guidelines for AI development."""
    def __init__(self, tool_name="generate_ethical_guidelines"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a set of detailed ethical guidelines for AI development based on specified focus areas."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(ETHICAL_GUIDELINES_DB.keys())},
                    "description": "A list of focus areas for the guidelines."
                }
            },
            "required": ["focus_areas"]
        }

    def execute(self, focus_areas: List[str], **kwargs: Any) -> str:
        guidelines = {
            "title": "Ethical AI Development Guidelines",
            "principles": []
        }
        
        for area in focus_areas:
            if area in ETHICAL_GUIDELINES_DB:
                guidelines["principles"].append({
                    "area": area,
                    "guideline": ETHICAL_GUIDELINES_DB[area]
                })
        
        return json.dumps(guidelines, indent=2)

class SuggestBiasMitigationTool(BaseTool):
    """Tool to suggest mitigation strategies for AI bias."""
    def __init__(self, tool_name="suggest_bias_mitigation"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Suggests common mitigation strategies for AI bias based on a bias check report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "bias_report_json": {"type": "string", "description": "The JSON report from the CheckAIBiasTool."}
            },
            "required": ["bias_report_json"]
        }

    def execute(self, bias_report_json: str, **kwargs: Any) -> str:
        try:
            bias_report = json.loads(bias_report_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for the bias report."}, indent=2)

        if not bias_report.get("bias_detected"):
            return json.dumps({"message": "No bias was detected, so no mitigation is suggested."}, indent=2)

        suggestions = [
            {"strategy": "Pre-processing (Data-level)", "description": "Consider re-sampling the training data to ensure more balanced representation of different groups. Techniques include up-sampling the minority group or down-sampling the majority group."},
            {"strategy": "In-processing (Model-level)", "description": "Explore using different model architectures or adding fairness constraints during training. Adversarial debiasing is one such technique."},
            {"strategy": "Post-processing (Prediction-level)", "description": "Adjust the model's predictions after they are made to ensure fairness. This can involve setting different classification thresholds for different groups to achieve equal opportunity or demographic parity."}
        ]
        
        report = {
            "mitigation_suggestions": suggestions
        }
        return json.dumps(report, indent=2)