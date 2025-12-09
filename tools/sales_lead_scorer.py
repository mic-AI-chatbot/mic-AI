
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SalesLeadScorerTool(BaseTool):
    """
    A tool that simulates sales lead scoring, allowing for defining scoring
    models and assigning a numerical score and grade to sales leads.
    """

    def __init__(self, tool_name: str = "SalesLeadScorer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.models_file = os.path.join(self.data_dir, "scoring_models.json")
        self.leads_file = os.path.join(self.data_dir, "scored_leads.json")
        
        # Scoring models: {model_id: {name: ..., rules: []}}
        self.scoring_models: Dict[str, Dict[str, Any]] = self._load_data(self.models_file, default={})
        # Scored leads: {lead_id: {data: ..., score: ..., grade: ...}}
        self.scored_leads: Dict[str, Dict[str, Any]] = self._load_data(self.leads_file, default={})

    @property
    def description(self) -> str:
        return "Simulates sales lead scoring: define models, score leads, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_scoring_model", "score_lead", "get_scoring_report"]},
                "model_id": {"type": "string"},
                "name": {"type": "string"},
                "rules": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"attribute": {"type": "string"}, "operator": {"type": "string"}, "value": {"type": "string"}, "score": {"type": "integer"}}},
                    "description": "e.g., [{'attribute': 'company_size', 'operator': '==', 'value': 'large', 'score': 50}]"
                },
                "lead_id": {"type": "string"},
                "lead_data": {"type": "object", "description": "Data related to the sales lead (e.g., {'company_size': 'medium', 'industry': 'tech'})."},
                "report_id": {"type": "string", "description": "ID of the scoring report to retrieve."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_models(self):
        with open(self.models_file, 'w') as f: json.dump(self.scoring_models, f, indent=2)

    def _save_leads(self):
        with open(self.leads_file, 'w') as f: json.dump(self.scored_leads, f, indent=2)

    def define_scoring_model(self, model_id: str, name: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Defines a new lead scoring model."""
        if model_id in self.scoring_models: raise ValueError(f"Scoring model '{model_id}' already exists.")
        
        new_model = {
            "id": model_id, "name": name, "rules": rules,
            "defined_at": datetime.now().isoformat()
        }
        self.scoring_models[model_id] = new_model
        self._save_models()
        return new_model

    def _evaluate_condition(self, attribute: str, operator: str, value: Any, lead_data: Dict[str, Any]) -> bool:
        """Evaluates a single condition against lead data."""
        lead_value = lead_data.get(attribute)
        if lead_value is None: return False
        
        # Simple type conversion for comparison
        try:
            if isinstance(lead_value, (int, float)) and isinstance(value, (int, float)):
                pass # Already numeric
            elif isinstance(lead_value, str) and isinstance(value, str):
                pass # Already string
            else: # Try to convert value to match lead_value type
                if isinstance(lead_value, int): value = int(value)
                elif isinstance(lead_value, float): value = float(value)
        except (ValueError, TypeError):
            return False # Cannot compare
        
        if operator == "==": return lead_value == value
        if operator == "!=": return lead_value != value
        if operator == ">": return lead_value > value
        if operator == "<": return lead_value < value
        if operator == ">=": return lead_value >= value
        if operator == "<=": return lead_value <= value
        
        return False

    def score_lead(self, lead_id: str, lead_data: Dict[str, Any], model_id: str) -> Dict[str, Any]:
        """Scores a sales lead based on a defined scoring model."""
        model = self.scoring_models.get(model_id)
        if not model: raise ValueError(f"Scoring model '{model_id}' not found. Define it first.")
        
        total_score = 0
        triggered_rules = []
        
        for rule in model["rules"]:
            if self._evaluate_condition(rule["attribute"], rule["operator"], rule["value"], lead_data):
                total_score += rule.get("score", 0)
                triggered_rules.append(rule["name"] if "name" in rule else f"Rule on {rule['attribute']}")
        
        lead_grade = "C"
        if total_score >= 80: lead_grade = "A"
        elif total_score >= 50: lead_grade = "B"
        
        new_scored_lead = {
            "id": lead_id, "data": lead_data, "score": total_score, "grade": lead_grade,
            "scored_at": datetime.now().isoformat()
        }
        self.scored_leads[lead_id] = new_scored_lead
        self._save_leads()

        report_id = f"score_report_{lead_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "lead_id": lead_id, "model_id": model_id,
            "total_score": total_score, "lead_grade": lead_grade,
            "triggered_rules": triggered_rules, "lead_data": lead_data,
            "generated_at": datetime.now().isoformat()
        }
        return report

    def get_scoring_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated lead scoring report."""
        report = self.scored_leads.get(report_id) # Assuming report_id is the lead_id for simplicity
        if not report: raise ValueError(f"Scoring report '{report_id}' not found.")
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_scoring_model":
            return self.define_scoring_model(kwargs['model_id'], kwargs['name'], kwargs['rules'])
        elif operation == "score_lead":
            return self.score_lead(kwargs['lead_id'], kwargs['lead_data'], kwargs['model_id'])
        elif operation == "get_scoring_report":
            return self.get_scoring_report(kwargs['report_id'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SalesLeadScorerTool functionality...")
    temp_dir = "temp_lead_scorer_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    scorer_tool = SalesLeadScorerTool(data_dir=temp_dir)
    
    try:
        # 1. Define a lead scoring model
        print("\n--- Defining lead scoring model 'b2b_scoring_model' ---")
        rules = [
            {"attribute": "company_size", "operator": ">=", "value": 50, "score": 30, "name": "Large Company"},
            {"attribute": "industry", "operator": "==", "value": "tech", "score": 25, "name": "Tech Industry"},
            {"attribute": "budget", "operator": ">", "value": 10000, "score": 40, "name": "High Budget"},
            {"attribute": "region", "operator": "==", "value": "EMEA", "score": 15, "name": "EMEA Region"}
        ]
        scorer_tool.execute(operation="define_scoring_model", model_id="b2b_scoring_model", name="B2B Lead Scoring", rules=rules)
        print("Scoring model defined.")

        # 2. Score a lead (high score)
        print("\n--- Scoring lead 'lead_001' (high score) ---")
        lead_data1 = {"company_size": 120, "industry": "tech", "budget": 15000, "region": "EMEA"}
        scoring_report1 = scorer_tool.execute(operation="score_lead", lead_id="lead_001", lead_data=lead_data1, model_id="b2b_scoring_model")
        print(json.dumps(scoring_report1, indent=2))

        # 3. Score another lead (medium score)
        print("\n--- Scoring lead 'lead_002' (medium score) ---")
        lead_data2 = {"company_size": 30, "industry": "retail", "budget": 5000, "region": "USA"}
        scoring_report2 = scorer_tool.execute(operation="score_lead", lead_id="lead_002", lead_data=lead_data2, model_id="b2b_scoring_model")
        print(json.dumps(scoring_report2, indent=2))

        # 4. Get scoring report
        print(f"\n--- Getting scoring report for '{scoring_report1['id']}' ---")
        report_details = scorer_tool.execute(operation="get_scoring_report", report_id=scoring_report1["id"])
        print(json.dumps(report_details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
