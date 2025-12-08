import logging
import json
import random
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class BCISignalGenerator:
    """Generates mock EEG-like brain signals for different intentions."""
    def generate_signals(self, num_data_points: int = 100, intention: str = "neutral") -> List[float]:
        # Simulate different frequency bands and their typical power
        alpha_power = np.random.normal(loc=10, scale=2, size=num_data_points) # 8-12 Hz, often associated with relaxation
        beta_power = np.random.normal(loc=20, scale=5, size=num_data_points)  # 13-30 Hz, often associated with active thinking/concentration
        theta_power = np.random.normal(loc=6, scale=1, size=num_data_points)  # 4-7 Hz, often associated with drowsiness/meditation
        
        # Combine these into a single simulated signal, with some noise
        signals = alpha_power + beta_power + theta_power + np.random.normal(loc=0, scale=3, size=num_data_points)
        
        # Introduce patterns based on intention
        if intention == "move_forward":
            signals += np.random.normal(loc=10, scale=2, size=num_data_points) # Simulate increased beta/gamma activity
        elif intention == "relax":
            signals += np.random.normal(loc=-10, scale=2, size=num_data_points) # Simulate increased alpha activity, reduced overall
        
        return signals.tolist()

    def generate_training_data(self, num_samples_per_intention: int = 50) -> Dict[str, Any]:
        X = [] # Features (e.g., mean, std dev of signals)
        y = [] # Labels (intentions)
        
        for intention in ["move_forward", "relax", "neutral"]:
            for _ in range(num_samples_per_intention):
                signals = self.generate_signals(num_data_points=50, intention=intention)
                # Simple features: mean and standard deviation of the simulated signals
                X.append([np.mean(signals), np.std(signals)])
                y.append(intention)
        
        return {"X": X, "y": y}

class BCIInterpreter:
    """Interprets simulated brain signals into commands or insights using simple rules."""
    def interpret(self, brain_signals: List[float]) -> Dict[str, Any]:
        avg_signal = np.mean(brain_signals)
        std_signal = np.std(brain_signals)
        
        command = "No clear command"
        insight = "Neutral state"
        confidence = random.uniform(0.5, 0.7)  # nosec B311

        # Simple heuristic rules for interpretation
        if avg_signal > 25 and std_signal > 10: # High average and high variability
            command = "Move forward"
            insight = "High concentration/motor intention detected"
            confidence = random.uniform(0.7, 0.95)  # nosec B311
        elif avg_signal < 15 and std_signal < 5: # Low average and low variability
            command = "Relax"
            insight = "Low activity/relaxed state detected"
            confidence = random.uniform(0.7, 0.95)  # nosec B311
            
        return {
            "interpreted_command": command,
            "interpreted_insight": insight,
            "confidence_score": round(confidence, 2)
        }

bci_signal_generator = BCISignalGenerator()
bci_interpreter = BCIInterpreter()

class InterpretBrainSignalsTool(BaseTool):
    """Interprets simulated brain signals into commands or insights."""
    def __init__(self, tool_name="interpret_brain_signals"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Interprets simulated brain signals (e.g., EEG readings) into actionable commands or insights, with a confidence score."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "The ID of the BCI device providing the signals."},
                "simulated_intention": {"type": "string", "description": "The simulated user intention to generate signals for.", "enum": ["move_forward", "relax", "neutral"], "default": "neutral"}
            },
            "required": ["device_id"]
        }

    def execute(self, device_id: str, simulated_intention: str = "neutral", **kwargs: Any) -> str:
        brain_signals = bci_signal_generator.generate_signals(intention=simulated_intention)
        interpretation = bci_interpreter.interpret(brain_signals)
        
        report = {
            "device_id": device_id,
            "simulated_intention": simulated_intention,
            "interpretation": interpretation
        }
        return json.dumps(report, indent=2)

class TrainBCIModelTool(BaseTool):
    """Simulates training a BCI model using generated brain signal data."""
    def __init__(self, tool_name="train_bci_model"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates training a BCI model using generated brain signal data and associated user intentions, returning simulated model performance."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_name": {"type": "string", "description": "The name of the BCI model to train."},
                "num_samples_per_intention": {"type": "integer", "description": "Number of simulated data samples to generate for each intention.", "default": 100}
            },
            "required": ["model_name"]
        }

    def execute(self, model_name: str, num_samples_per_intention: int = 100, **kwargs: Any) -> str:
        training_data = bci_signal_generator.generate_training_data(num_samples_per_intention)
        X = np.array(training_data["X"])
        y = training_data["y"]

        # Simulate training a simple Logistic Regression model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = LogisticRegression(max_iter=1000)
        model.fit(X_train, y_train)
        
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        
        report = {
            "model_name": model_name,
            "training_status": "completed",
            "simulated_performance": {
                "accuracy": round(accuracy, 2),
                "num_training_samples": len(X_train),
                "num_test_samples": len(X_test)
            },
            "message": f"BCI model '{model_name}' successfully trained with a simulated accuracy of {accuracy:.2f}."
        }
        return json.dumps(report, indent=2)