
import logging
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# A simple knowledge base mapping conditions to symptoms and their weights.
# This is for demonstration purposes only and is not real medical data.
KNOWLEDGE_BASE = {
    "common_cold": {
        "symptoms": {"runny_nose": 3, "sore_throat": 3, "cough": 2, "sneezing": 2, "mild_fever": 1},
        "severity": "Mild",
        "description": "A common viral infection of the nose and throat."
    },
    "influenza": {
        "symptoms": {"fever": 3, "body_aches": 3, "cough": 3, "fatigue": 3, "headache": 2},
        "severity": "Moderate",
        "description": "A contagious respiratory illness caused by influenza viruses."
    },
    "allergies": {
        "symptoms": {"sneezing": 3, "runny_nose": 3, "itchy_eyes": 3, "cough": 1},
        "severity": "Mild to Moderate",
        "description": "An exaggerated response by the immune system to a substance that is normally harmless."
    },
    "strep_throat": {
        "symptoms": {"sore_throat": 4, "fever": 3, "swollen_lymph_nodes": 2, "headache": 1},
        "severity": "Moderate",
        "description": "A bacterial infection that can make your throat feel sore and scratchy."
    }
}

class MedicalSymptomCheckerTool(BaseTool):
    """
    A rule-based tool that suggests possible conditions based on user-provided
    symptoms. This tool is for informational purposes only and is not a
    substitute for professional medical advice.
    """

    def __init__(self, tool_name: str = "SymptomChecker", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.disclaimer = "DISCLAIMER: This is a simulation and not a medical diagnosis. Always consult a healthcare professional for any health concerns."

    @property
    def description(self) -> str:
        return "Suggests possible conditions based on symptoms. Not a substitute for professional medical advice."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of symptoms experienced by the user (e.g., ['cough', 'fever'])."
                }
            },
            "required": ["symptoms"]
        }

    def execute(self, symptoms: List[str], **kwargs: Any) -> Dict[str, Any]:
        """
        Analyzes symptoms against a knowledge base to suggest possible conditions.
        """
        if not symptoms:
            return {"error": "Please provide a list of symptoms.", "disclaimer": self.disclaimer}

        symptoms_set = set(s.lower().replace(" ", "_") for s in symptoms)
        scores = []

        for condition, data in KNOWLEDGE_BASE.items():
            score = 0
            matched_symptoms = []
            for symptom in symptoms_set:
                if symptom in data["symptoms"]:
                    score += data["symptoms"][symptom]
                    matched_symptoms.append(symptom)
            
            if score > 0:
                scores.append({
                    "condition": condition.replace("_", " ").title(),
                    "match_score": score,
                    "matched_symptoms": matched_symptoms,
                    "description": data["description"],
                    "severity": data["severity"]
                })

        sorted_conditions = sorted(scores, key=lambda x: x['match_score'], reverse=True)

        return {
            "possible_conditions": sorted_conditions,
            "disclaimer": self.disclaimer
        }

if __name__ == '__main__':
    print("Demonstrating MedicalSymptomCheckerTool functionality...")
    
    symptom_checker = MedicalSymptomCheckerTool()
    
    try:
        # --- Scenario 1: Classic flu-like symptoms ---
        print("\n--- Checking symptoms: ['fever', 'body aches', 'cough'] ---")
        user_symptoms_1 = ["fever", "body aches", "cough"]
        result1 = symptom_checker.execute(symptoms=user_symptoms_1)
        print(json.dumps(result1, indent=2))

        # --- Scenario 2: Allergy-like symptoms ---
        print("\n--- Checking symptoms: ['sneezing', 'itchy eyes'] ---")
        user_symptoms_2 = ["sneezing", "itchy eyes"]
        result2 = symptom_checker.execute(symptoms=user_symptoms_2)
        print(json.dumps(result2, indent=2))
        
        # --- Scenario 3: Vague symptom ---
        print("\n--- Checking symptoms: ['sore throat'] ---")
        user_symptoms_3 = ["sore throat"]
        result3 = symptom_checker.execute(symptoms=user_symptoms_3)
        print(json.dumps(result3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")

