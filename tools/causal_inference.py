import logging
import json
import random
import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class CausalDataGenerator:
    """Generates mock data with predefined causal relationships for simulation."""
    def generate_data(self, num_samples: int = 100, has_causal_effect: bool = True) -> pd.DataFrame:
        # Simulate a confounder (Z)
        Z = np.random.normal(loc=50, scale=10, size=num_samples)
        
        # Simulate treatment (T) influenced by Z (e.g., sicker patients get more treatment)
        # Using a logistic function to make T binary (0 or 1)
        T_prob = 1 / (1 + np.exp(-(0.1 * Z - 5))) # Z influences probability of T
        T = np.random.binomial(n=1, p=T_prob, size=num_samples)
        
        # Simulate outcome (Y) influenced by T and Z
        if has_causal_effect:
            # Y = effect_of_T * T + effect_of_Z * Z + noise
            Y = 5 * T + 0.8 * Z + np.random.normal(loc=0, scale=5, size=num_samples)
        else:
            # Y only influenced by Z, T has no direct causal effect
            Y = 0.8 * Z + np.random.normal(loc=0, scale=5, size=num_samples)
        
        df = pd.DataFrame({"Z": Z, "T": T, "Y": Y})
        return df

class IdentifyCausalRelationshipsTool(BaseTool):
    """Identifies potential causal relationships between variables using simulated data."""
    def __init__(self, tool_name="identify_causal_relationships"):
        super().__init__(tool_name=tool_name)
        self.data_generator = CausalDataGenerator()

    @property
    def description(self) -> str:
        return "Identifies potential causal relationships between specified variables within a simulated dataset using correlation analysis."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "num_samples": {"type": "integer", "description": "Number of data samples to generate.", "default": 100},
                "simulated_causal_effect_present": {"type": "boolean", "description": "Whether to inject a causal effect in the simulated data.", "default": True}
            },
            "required": []
        }

    def execute(self, num_samples: int = 100, simulated_causal_effect_present: bool = True, **kwargs: Any) -> str:
        df = self.data_generator.generate_data(num_samples, simulated_causal_effect_present)
        
        # Simple correlation-based approach (correlation != causation, but a starting point for identifying relationships)
        correlations = df.corr().stack().reset_index()
        correlations.columns = ['variable1', 'variable2', 'correlation']
        
        identified_relationships = []
        for index, row in correlations.iterrows():
            if row["variable1"] != row["variable2"] and abs(row["correlation"]) > 0.5: # Threshold for strong correlation
                identified_relationships.append({
                    "variable1": row["variable1"],
                    "variable2": row["variable2"],
                    "correlation": round(row["correlation"], 2),
                    "potential_causal_link": "High correlation suggests a potential relationship, but further causal inference methods are needed to confirm causation."
                })
        
        report = {
            "num_samples": num_samples,
            "simulated_causal_effect_present_in_data": simulated_causal_effect_present,
            "identified_relationships": identified_relationships
        }
        return json.dumps(report, indent=2)

class EstimateTreatmentEffectTool(BaseTool):
    """Estimates the causal effect of a treatment using simulated data from a randomized controlled trial (RCT)."""
    def __init__(self, tool_name="estimate_treatment_effect"):
        super().__init__(tool_name=tool_name)
        self.data_generator = CausalDataGenerator()

    @property
    def description(self) -> str:
        return "Estimates the causal effect of a specific treatment or intervention on an outcome variable using simulated data from a randomized controlled trial (RCT)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "num_samples": {"type": "integer", "description": "Number of data samples to generate for the RCT.", "default": 100},
                "simulated_treatment_effect_magnitude": {"type": "number", "description": "The simulated magnitude of the treatment effect to inject into the data.", "default": 5.0}
            },
            "required": []
        }

    def execute(self, num_samples: int = 100, simulated_treatment_effect_magnitude: float = 5.0, **kwargs: Any) -> str:
        # Simulate an RCT: treatment (T) is randomly assigned, so Z is not a confounder for T->Y
        Z = np.random.normal(loc=50, scale=10, size=num_samples)
        T = np.random.binomial(n=1, p=0.5, size=num_samples) # Random assignment of treatment
        Y = simulated_treatment_effect_magnitude * T + 0.8 * Z + np.random.normal(loc=0, scale=5, size=num_samples)
        
        df = pd.DataFrame({"Z": Z, "T": T, "Y": Y})

        # Calculate average outcome for treated and control groups
        treated_group = df[df["T"] == 1]["Y"]
        control_group = df[df["T"] == 0]["Y"]

        avg_treated = treated_group.mean()
        avg_control = control_group.mean()
        
        estimated_effect = avg_treated - avg_control

        # Perform an independent samples t-test to check for statistical significance
        t_stat, p_value = stats.ttest_ind(treated_group, control_group)
        
        alpha = 0.05 # Common significance level
        significance = "statistically significant" if p_value < alpha else "not statistically significant"

        report = {
            "num_samples": num_samples,
            "treatment_variable": "T",
            "outcome_variable": "Y",
            "average_outcome_treated": round(avg_treated, 2),
            "average_outcome_control": round(avg_control, 2),
            "estimated_treatment_effect": round(estimated_effect, 2),
            "t_statistic": round(t_stat, 3),
            "p_value": round(p_value, 3),
            "significance_level_alpha": alpha,
            "statistical_significance": significance,
            "summary": f"The estimated causal effect of the treatment is {estimated_effect:.2f}. This effect is {significance} (p={p_value:.3f})."
        }
        return json.dumps(report, indent=2)