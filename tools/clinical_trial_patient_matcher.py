import logging
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool # Corrected import

logger = logging.getLogger(__name__)

# In-memory storage for simulated clinical trials and patients
clinical_trials: Dict[str, Dict[str, Any]] = {
    "trial_A": {
        "disease": "Type 2 Diabetes",
        "eligibility_criteria": ["age > 18", "HbA1c > 7.0"],
        "status": "recruiting"
    },
    "trial_B": {
        "disease": "Hypertension",
        "eligibility_criteria": ["age > 40", "systolic_bp > 140"],
        "status": "recruiting"
    }
}
patients: Dict[str, Dict[str, Any]] = {
    "patient_1": {"age": 35, "HbA1c": 7.5, "systolic_bp": 130},
    "patient_2": {"age": 50, "HbA1c": 6.8, "systolic_bp": 150}
}

class MatchPatientsToTrialsTool(BaseTool):
    """
    Tool to simulate matching patients to clinical trials.
    """
    def __init__(self, tool_name: str = "match_patients_to_trials"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates matching eligible patients to open clinical trials based on their medical profiles and trial eligibility criteria."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "The ID of the patient to match."},
                "trial_id": {"type": "string", "description": "Optional: The ID of a specific trial to match against. If not provided, matches against all open trials."}
            },
            "required": ["patient_id"]
        }

    def execute(self, patient_id: str, trial_id: str = None, **kwargs: Any) -> Dict[str, Any]:
        if patient_id not in patients:
            return {"error": f"Patient with ID '{patient_id}' not found."}
            
        patient_info = patients[patient_id]
        matched_trials = []
        
        trials_to_check = {}
        if trial_id:
            if trial_id not in clinical_trials:
                return {"error": f"Clinical trial with ID '{trial_id}' not found."}
            trials_to_check[trial_id] = clinical_trials[trial_id]
        else:
            trials_to_check = clinical_trials
            
        for t_id, trial_info in trials_to_check.items():
            if trial_info["status"] != "recruiting":
                continue
            
            # Simple simulation of eligibility check
            is_eligible = True
            for criterion in trial_info["eligibility_criteria"]:
                if "age >" in criterion:
                    min_age = int(criterion.split(">")[1].strip())
                    if patient_info["age"] <= min_age:
                        is_eligible = False
                        break
                if "HbA1c >" in criterion:
                    min_hba1c = float(criterion.split(">")[1].strip())
                    if patient_info["HbA1c"] <= min_hba1c:
                        is_eligible = False
                        break
                if "systolic_bp >" in criterion:
                    min_bp = int(criterion.split(">")[1].strip())
                    if patient_info["systolic_bp"] <= min_bp:
                        is_eligible = False
                        break
            
            if is_eligible:
                matched_trials.append(t_id)
        
        return {
            "patient_id": patient_id,
            "matched_trials": matched_trials,
            "message": f"Patient '{patient_id}' matched to {len(matched_trials)} trials."
        }

class GetTrialEligibilityCriteriaTool(BaseTool):
    """
    Tool to simulate retrieving eligibility criteria for a clinical trial.
    """
    def __init__(self, tool_name: str = "get_trial_eligibility_criteria"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates retrieving the detailed eligibility criteria for a specific clinical trial."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "trial_id": {"type": "string", "description": "The ID of the clinical trial to get eligibility criteria for."}
            },
            "required": ["trial_id"]
        }

    def execute(self, trial_id: str, **kwargs: Any) -> Dict[str, Any]:
        if trial_id not in clinical_trials:
            return {"error": f"Clinical trial with ID '{trial_id}' not found."}
            
        return {
            "trial_id": trial_id,
            "disease": clinical_trials[trial_id]["disease"],
            "eligibility_criteria": clinical_trials[trial_id]["eligibility_criteria"]
        }