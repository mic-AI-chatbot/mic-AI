import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class NoCodeAIPlatformSimulatorTool(BaseTool):
    """
    A tool that simulates a no-code AI platform, allowing users to build,
    deploy, and make predictions with AI models without writing code.
    """

    def __init__(self, tool_name: str = "NoCodeAIPlatformSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.models_file = os.path.join(self.data_dir, "ai_models.json")
        # Models structure: {model_name: {type: ..., status: ..., performance: ..., deployments: []}}
        self.models: Dict[str, Dict[str, Any]] = self._load_data(self.models_file, default={})

    @property
    def description(self) -> str:
        return "Simulates a no-code AI platform: build, deploy, and make predictions with AI models."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["build_model", "deploy_model", "make_prediction", "list_models"]},
                "model_name": {"type": "string"},
                "model_type": {"type": "string", "enum": ["classification", "regression"], "description": "Type of AI model."},
                "data_source": {"type": "string", "description": "Simulated data source for model training."},
                "deployment_environment": {"type": "string", "enum": ["staging", "production"], "description": "Environment for deployment."},
                "input_data": {"type": "object", "description": "Input data for making a prediction."}
            },
            "required": ["operation", "model_name"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.models_file, 'w') as f: json.dump(self.models, f, indent=2)

    def build_model(self, model_name: str, model_type: str, data_source: str) -> Dict[str, Any]:
        """Simulates building a new AI model."""
        if model_name in self.models: raise ValueError(f"Model '{model_name}' already exists.")
        
        performance_metric = random.uniform(0.7, 0.95) # Simulated accuracy or R2 score  # nosec B311
        
        new_model = {
            "name": model_name, "type": model_type, "data_source": data_source,
            "status": "trained", "performance_metric": round(performance_metric, 2),
            "deployments": [], "built_at": datetime.now().isoformat()
        }
        self.models[model_name] = new_model
        self._save_data()
        return new_model

    def deploy_model(self, model_name: str, deployment_environment: str) -> Dict[str, Any]:
        """Simulates deploying an AI model to a specified environment."""
        model = self.models.get(model_name)
        if not model: raise ValueError(f"Model '{model_name}' not found.")
        if model["status"] != "trained": raise ValueError(f"Model '{model_name}' is not trained. Current status: {model['status']}.")

        deployment_record = {
            "environment": deployment_environment,
            "deployed_at": datetime.now().isoformat(),
            "status": "active"
        }
        model["deployments"].append(deployment_record)
        model["status"] = "deployed"
        self._save_data()
        return model

    def make_prediction(self, model_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates making a prediction using a deployed AI model."""
        model = self.models.get(model_name)
        if not model: raise ValueError(f"Model '{model_name}' not found.")
        if model["status"] != "deployed": raise ValueError(f"Model '{model_name}' is not deployed. Current status: {model['status']}.")

        prediction_output: Any = None
        if model["type"] == "classification":
            prediction_output = random.choice(["Class A", "Class B", "Class C"])  # nosec B311
        elif model["type"] == "regression":
            prediction_output = round(random.uniform(10.0, 1000.0), 2)  # nosec B311
        
        return {"model_name": model_name, "input_data": input_data, "prediction": prediction_output}

    def list_models(self) -> List[Dict[str, Any]]:
        """Lists all AI models in the catalog."""
        return list(self.models.values())

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "build_model": self.build_model,
            "deploy_model": self.deploy_model,
            "make_prediction": self.make_prediction,
            "list_models": self.list_models
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating NoCodeAIPlatformSimulatorTool functionality...")
    temp_dir = "temp_nocode_ai_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    nocode_ai_tool = NoCodeAIPlatformSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Build a classification model
        print("\n--- Building a classification model 'customer_churn_predictor' ---")
        nocode_ai_tool.execute(
            operation="build_model", model_name="customer_churn_predictor",
            model_type="classification", data_source="customer_data_warehouse"
        )
        print("Model 'customer_churn_predictor' built.")

        # 2. Deploy the model
        print("\n--- Deploying 'customer_churn_predictor' to production ---")
        nocode_ai_tool.execute(operation="deploy_model", model_name="customer_churn_predictor", deployment_environment="production")
        print("Model deployed.")

        # 3. Make a prediction
        print("\n--- Making a prediction with 'customer_churn_predictor' ---")
        prediction_input = {"age": 35, "income": 70000, "usage_frequency": "high"}
        prediction_result = nocode_ai_tool.execute(operation="make_prediction", model_name="customer_churn_predictor", input_data=prediction_input)
        print(json.dumps(prediction_result, indent=2))

        # 4. List all models
        print("\n--- Listing all models ---")
        all_models = nocode_ai_tool.execute(operation="list_models", model_name="any") # model_name is required but not used for list_models
        print(json.dumps(all_models, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")