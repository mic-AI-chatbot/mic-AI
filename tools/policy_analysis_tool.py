import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PolicyAnalysisSimulatorTool(BaseTool):
    """
    A tool that simulates policy analysis, allowing for defining policies,
    evaluating their effectiveness, and predicting outcomes under different scenarios.
    """

    def __init__(self, tool_name: str = "PolicyAnalysisSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.policies_file = os.path.join(self.data_dir, "policy_definitions.json")
        self.reports_file = os.path.join(self.data_dir, "policy_analysis_reports.json")
        
        # Policy definitions: {policy_id: {name: ..., target_area: ..., rules: []}}
        self.policy_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.policies_file, default={})
        # Analysis reports: {report_id: {policy_id: ..., type: ..., results: {}}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates policy analysis: evaluate effectiveness and predict outcomes for defined policies."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_policy", "evaluate_effectiveness", "predict_outcomes", "list_policies"]},
                "policy_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "target_area": {"type": "string", "enum": ["economy", "environment", "social", "health"]},
                "rules": {"type": "array", "items": {"type": "object"}, "description": "e.g., [{'metric': 'gdp_growth', 'effect': 0.02}]"},
                "metrics": {"type": "array", "items": {"type": "string"}, "description": "Metrics to evaluate (e.g., ['gdp_growth', 'unemployment_rate'])."},
                "scenarios": {"type": "object", "description": "e.g., {'economic_growth': 'high', 'public_support': 'low'}"}
            },
            "required": ["operation", "policy_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_policies(self):
        with open(self.policies_file, 'w') as f: json.dump(self.policy_definitions, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def define_policy(self, policy_id: str, name: str, description: str, target_area: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Defines a new policy with its rules and target area."""
        if policy_id in self.policy_definitions: raise ValueError(f"Policy '{policy_id}' already exists.")
        
        new_policy = {
            "id": policy_id, "name": name, "description": description,
            "target_area": target_area, "rules": rules,
            "created_at": datetime.now().isoformat()
        }
        self.policy_definitions[policy_id] = new_policy
        self._save_policies()
        return new_policy

    def evaluate_effectiveness(self, policy_id: str, metrics: List[str]) -> Dict[str, Any]:
        """Evaluates the simulated effectiveness of a policy on specified metrics."""
        policy = self.policy_definitions.get(policy_id)
        if not policy: raise ValueError(f"Policy '{policy_id}' not found.")
        
        evaluation_results = {}
        for metric in metrics:
            simulated_effect = 0.0
            for rule in policy["rules"]:
                if rule.get("metric") == metric:
                    simulated_effect += rule.get("effect", 0.0)
            
            # Add some random noise to simulate real-world variability
            simulated_effect += random.uniform(-0.01, 0.01)  # nosec B311
            evaluation_results[metric] = round(simulated_effect, 4)
        
        report_id = f"eval_{policy_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "policy_id": policy_id, "type": "effectiveness_evaluation",
            "metrics_evaluated": metrics, "results": evaluation_results,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def predict_outcomes(self, policy_id: str, scenarios: Dict[str, str]) -> Dict[str, Any]:
        """Predicts policy outcomes under different simulated scenarios."""
        policy = self.policy_definitions.get(policy_id)
        if not policy: raise ValueError(f"Policy '{policy_id}' not found.")
        
        predicted_outcomes = {}
        
        # Simple rule-based outcome prediction
        if policy["target_area"] == "economy":
            if scenarios.get("economic_growth") == "high":
                predicted_outcomes["gdp_growth"] = random.uniform(0.03, 0.05)  # nosec B311
                predicted_outcomes["unemployment_rate"] = random.uniform(-0.01, -0.02)  # nosec B311
            else:
                predicted_outcomes["gdp_growth"] = random.uniform(0.01, 0.02)  # nosec B311
                predicted_outcomes["unemployment_rate"] = random.uniform(0.005, 0.01)  # nosec B311
        
        if scenarios.get("public_support") == "low":
            predicted_outcomes["public_approval"] = random.uniform(0.2, 0.4)  # nosec B311
        else:
            predicted_outcomes["public_approval"] = random.uniform(0.6, 0.8)  # nosec B311

        report_id = f"pred_{policy_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "policy_id": policy_id, "type": "outcome_prediction",
            "scenario": scenarios, "predicted_outcomes": predicted_outcomes,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def list_policies(self) -> List[Dict[str, Any]]:
        """Lists all defined policies."""
        return list(self.policy_definitions.values())

    def execute(self, operation: str, policy_id: str, **kwargs: Any) -> Any:
        if operation == "define_policy":
            name = kwargs.get('name')
            description = kwargs.get('description')
            target_area = kwargs.get('target_area')
            rules = kwargs.get('rules')
            if not all([name, description, target_area, rules]):
                raise ValueError("Missing 'name', 'description', 'target_area', or 'rules' for 'define_policy' operation.")
            return self.define_policy(policy_id, name, description, target_area, rules)
        elif operation == "evaluate_effectiveness":
            metrics = kwargs.get('metrics')
            if not metrics:
                raise ValueError("Missing 'metrics' for 'evaluate_effectiveness' operation.")
            return self.evaluate_effectiveness(policy_id, metrics)
        elif operation == "predict_outcomes":
            scenarios = kwargs.get('scenarios')
            if not scenarios:
                raise ValueError("Missing 'scenarios' for 'predict_outcomes' operation.")
            return self.predict_outcomes(policy_id, scenarios)
        elif operation == "list_policies":
            # policy_id is required by the tool's parameters, but not used by list_policies method itself.
            # No additional kwargs are required for list_policies.
            return self.list_policies()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PolicyAnalysisSimulatorTool functionality...")
    temp_dir = "temp_policy_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    policy_tool = PolicyAnalysisSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a new economic policy
        print("\n--- Defining policy 'economic_stimulus_2025' ---")
        policy_tool.execute(operation="define_policy", policy_id="economic_stimulus_2025", name="Economic Stimulus Package",
                            description="Policy to boost post-recession growth.", target_area="economy",
                            rules=[{"metric": "gdp_growth", "effect": 0.015}, {"metric": "unemployment_rate", "effect": -0.005}])
        print("Policy defined.")

        # 2. Evaluate its effectiveness
        print("\n--- Evaluating effectiveness of 'economic_stimulus_2025' ---")
        evaluation = policy_tool.execute(operation="evaluate_effectiveness", policy_id="economic_stimulus_2025", metrics=["gdp_growth", "unemployment_rate"])
        print(json.dumps(evaluation, indent=2))

        # 3. Predict outcomes under a specific scenario
        print("\n--- Predicting outcomes for 'economic_stimulus_2025' under 'high growth, low support' scenario ---")
        outcomes = policy_tool.execute(operation="predict_outcomes", policy_id="economic_stimulus_2025", scenarios={"economic_growth": "high", "public_support": "low"})
        print(json.dumps(outcomes, indent=2))

        # 4. List all defined policies
        print("\n--- Listing all defined policies ---")
        all_policies = policy_tool.execute(operation="list_policies", policy_id="any") # policy_id is not used for list_policies
        print(json.dumps(all_policies, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")