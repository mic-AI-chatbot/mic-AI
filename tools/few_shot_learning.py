import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

FEW_SHOT_TASKS_FILE = "few_shot_tasks.json"

class FewShotLearner:
    """
    A tool for simulating few-shot learning, where a model learns effectively
    from very limited examples. It allows for defining tasks with examples
    and simulating predictions for new inputs.
    Learning tasks and their outcomes are persisted in a local JSON file.
    """

    def __init__(self):
        """
        Initializes the FewShotLearner.
        Loads existing learning tasks or creates new ones.
        """
        self.tasks: Dict[str, Dict[str, Any]] = self._load_tasks()

    def _load_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Loads few-shot learning tasks from a JSON file."""
        if os.path.exists(FEW_SHOT_TASKS_FILE):
            with open(FEW_SHOT_TASKS_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted tasks file '{FEW_SHOT_TASKS_FILE}'. Starting with empty data.")
                    return {}
        return {}

    def _save_tasks(self) -> None:
        """Saves current few-shot learning tasks to a JSON file."""
        with open(FEW_SHOT_TASKS_FILE, 'w') as f:
            json.dump(self.tasks, f, indent=4)

    def define_task(self, task_id: str, task_description: str,
                    examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Defines a new few-shot learning task with limited examples.

        Args:
            task_id: A unique identifier for the task.
            task_description: A description of the task to learn.
            examples: A list of dictionaries, each representing an example
                      (e.g., {"input": "apple", "output": "fruit"}).

        Returns:
            A dictionary containing the details of the newly defined task.
        """
        if not task_id or not task_description or not examples:
            raise ValueError("Task ID, description, and examples cannot be empty.")
        if task_id in self.tasks:
            raise ValueError(f"Few-shot learning task with ID '{task_id}' already exists.")
        if not all("input" in ex and "output" in ex for ex in examples):
            raise ValueError("Each example must be a dictionary with 'input' and 'output' keys.")

        new_task = {
            "task_id": task_id,
            "task_description": task_description,
            "examples": examples,
            "defined_at": datetime.now().isoformat(),
            "predictions_history": []
        }
        self.tasks[task_id] = new_task
        self._save_tasks()
        logger.info(f"Few-shot learning task '{task_id}' defined successfully.")
        return new_task

    def learn_from_examples(self, task_id: str, new_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates learning from examples and making a prediction/decision for a new input.

        Args:
            task_id: The ID of the few-shot learning task.
            new_input: A dictionary representing the new input for which to make a prediction.

        Returns:
            A dictionary containing the simulated prediction/decision.
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Few-shot learning task with ID '{task_id}' not found.")
        
        # Simulate learning and prediction based on examples
        # Very basic simulation: if new_input matches any example input, return its output
        # Otherwise, try to generalize or return a random output from examples
        
        predicted_output = "unknown"
        confidence = round(random.uniform(0.5, 0.95), 2)  # nosec B311

        for example in task["examples"]:
            if example["input"] == new_input.get("value"): # Simple direct match
                predicted_output = example["output"]
                confidence = round(random.uniform(0.9, 0.99), 2)  # nosec B311
                break
        else:
            # If no direct match, try to infer or pick a random output from examples
            if task["examples"]:
                predicted_output = random.choice([ex["output"] for ex in task["examples"]])  # nosec B311
                confidence = round(random.uniform(0.5, 0.7), 2) # Lower confidence for inference  # nosec B311

        prediction_record = {
            "prediction_id": f"PRED-{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}",
            "task_id": task_id,
            "new_input": new_input,
            "predicted_output": predicted_output,
            "confidence": confidence,
            "predicted_at": datetime.now().isoformat()
        }
        task["predictions_history"].append(prediction_record)
        self._save_tasks()
        logger.info(f"Prediction made for task '{task_id}'. Predicted: '{predicted_output}'.")
        return prediction_record

    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        Lists all defined few-shot learning tasks.

        Returns:
            A list of dictionaries, each representing a task (summary).
        """
        return [{k: v for k, v in task.items() if k != "examples" and k != "predictions_history"} for task in self.tasks.values()]

    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the full details of a specific few-shot learning task, including examples and predictions history.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            A dictionary containing the task's full details, or None if not found.
        """
        return self.tasks.get(task_id)

# Example usage (for direct script execution)
if __name__ == '__main__':
    print("Demonstrating FewShotLearner functionality...")

    learner = FewShotLearner()

    # Clean up previous state for a fresh demo
    if os.path.exists(FEW_SHOT_TASKS_FILE):
        os.remove(FEW_SHOT_TASKS_FILE)
        learner = FewShotLearner() # Re-initialize to clear loaded state
        print(f"\nCleaned up {FEW_SHOT_TASKS_FILE} for fresh demo.")

    # --- Define Task ---
    print("\n--- Defining Few-Shot Learning Task 'sentiment_classification' ---")
    try:
        task1 = learner.define_task(
            task_id="sentiment_classification",
            task_description="Classify text as positive or negative sentiment.",
            examples=[
                {"input": "I love this product!", "output": "positive"},
                {"input": "This is terrible.", "output": "negative"},
                {"input": "Amazing service!", "output": "positive"}
            ]
        )
        print(json.dumps(task1, indent=2))
    except Exception as e:
        print(f"Define task failed: {e}")

    # --- Learn from Examples and Predict ---
    print("\n--- Learning and Predicting for 'sentiment_classification' ---")
    try:
        prediction1 = learner.learn_from_examples("sentiment_classification", {"value": "I am so happy."})
        print(json.dumps(prediction1, indent=2))

        print("\n--- Predicting for a new input ---")
        prediction2 = learner.learn_from_examples("sentiment_classification", {"value": "This is not good."})
        print(json.dumps(prediction2, indent=2))

    except Exception as e:
        print(f"Learn from examples failed: {e}")

    # --- List Tasks ---
    print("\n--- Listing All Tasks ---")
    all_tasks = learner.list_tasks()
    print(json.dumps(all_tasks, indent=2))

    # --- Get Task Details ---
    print("\n--- Getting Details for 'sentiment_classification' ---")
    task_details = learner.get_task_details("sentiment_classification")
    print(json.dumps(task_details, indent=2))

    # Clean up
    if os.path.exists(FEW_SHOT_TASKS_FILE):
        os.remove(FEW_SHOT_TASKS_FILE)
        print(f"\nCleaned up {FEW_SHOT_TASKS_FILE} for fresh demo.")