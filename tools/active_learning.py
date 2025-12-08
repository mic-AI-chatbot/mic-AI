import logging
import random
import json
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for the active learning simulation
class ActiveLearningState:
    def __init__(self):
        self.unlabeled_data_pool: List[Dict[str, Any]] = [
            {"id": i, "text": f"Sample text for active learning item {i}"} for i in range(1, 101)
        ]
        # Simulate model confidence scores for each data point
        self.model_confidences: Dict[int, float] = {item['id']: random.uniform(0.5, 1.0) for item in self.unlabeled_data_pool}  # nosec B311
        self.model_performance: Dict[str, Any] = {"accuracy": 0.75, "labeled_samples": 0}

active_learning_state = ActiveLearningState()

class QueryByUncertaintyTool(BaseTool):
    """
    Tool to query unlabeled data points using uncertainty sampling for human annotation.
    """
    def __init__(self, tool_name="query_by_uncertainty"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Queries unlabeled data points with the lowest model confidence (most uncertain) for human annotation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "num_samples": {"type": "integer", "description": "The number of uncertain samples to query.", "default": 5}
            },
            "required": []
        }

    def execute(self, num_samples: int = 5, **kwargs: Any) -> str:
        """
        Selects the most uncertain samples from the unlabeled data pool.
        Returns a JSON string of the queried samples.
        """
        if not active_learning_state.unlabeled_data_pool:
            return json.dumps([{"message": "No unlabeled data available."}], indent=2)

        # Sort the unlabeled data by model confidence (ascending)
        unlabeled_ids = [item['id'] for item in active_learning_state.unlabeled_data_pool]
        sorted_by_uncertainty = sorted(
            unlabeled_ids,
            key=lambda item_id: active_learning_state.model_confidences.get(item_id, 1.0)
        )

        num_to_query = min(num_samples, len(sorted_by_uncertainty))
        queried_ids = sorted_by_uncertainty[:num_to_query]
        
        queried_samples = [item for item in active_learning_state.unlabeled_data_pool if item['id'] in queried_ids]
        
        return json.dumps(queried_samples, indent=2)

class IncorporateFeedbackAndRetrainTool(BaseTool):
    """
    Tool to simulate incorporating human feedback and retraining the model.
    """
    def __init__(self, tool_name="incorporate_feedback_and_retrain"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates incorporating human-annotated feedback, removing data from the unlabeled pool, and retraining the model to improve performance."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "feedback_data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "label": {"type": "string"}
                        },
                        "required": ["id", "label"]
                    },
                    "description": "A list of human-annotated data points (from the query tool)."
                }
            },
            "required": ["feedback_data"]
        }

    def execute(self, feedback_data: List[Dict[str, Any]], **kwargs: Any) -> str:
        """
        Incorporates feedback, updates the data pool, and simulates model retraining.
        Returns a JSON string with the new model performance.
        """
        if not feedback_data:
            return json.dumps({"error": "No feedback data provided."}, indent=2)

        annotated_ids = {item['id'] for item in feedback_data}
        
        # Remove annotated data from the unlabeled pool
        active_learning_state.unlabeled_data_pool = [
            item for item in active_learning_state.unlabeled_data_pool if item['id'] not in annotated_ids
        ]
        
        # Also remove from confidence scores
        for item_id in annotated_ids:
            active_learning_state.model_confidences.pop(item_id, None)

        # Simulate model performance improvement
        # The improvement is proportional to the number of new samples
        improvement = len(feedback_data) * random.uniform(0.005, 0.015)  # nosec B311
        new_accuracy = active_learning_state.model_performance["accuracy"] + improvement
        active_learning_state.model_performance["accuracy"] = min(new_accuracy, 0.99) # Cap at 99%
        active_learning_state.model_performance["labeled_samples"] += len(feedback_data)

        # Simulate updating confidences for the remaining unlabeled data after retraining
        for item in active_learning_state.unlabeled_data_pool:
            # In a real scenario, the model would produce new confidences. Here we simulate that.
            active_learning_state.model_confidences[item['id']] = random.uniform(0.6, 1.0)  # nosec B311

        report = {
            "message": f"Feedback from {len(feedback_data)} samples incorporated and model retrained.",
            "new_performance": active_learning_state.model_performance
        }
        return json.dumps(report, indent=2)