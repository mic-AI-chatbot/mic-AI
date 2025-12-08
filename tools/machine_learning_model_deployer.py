

import logging
import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MachineLearningModelDeployerTool(BaseTool):
    """
    Manages the deployment lifecycle of ML models as local artifacts,
    including running a simple rule-based inference engine.
    """

    def __init__(self, tool_name: str = "MLModelDeployer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.deployments_file = os.path.join(self.data_dir, "ml_deployments.json")
        self.artifacts_dir = os.path.join(self.data_dir, "artifacts")
        os.makedirs(self.artifacts_dir, exist_ok=True)
        self.deployments: Dict[str, Dict[str, Any]] = self._load_data(self.deployments_file, default={})

    @property
    def description(self) -> str:
        return "Manages local deployment of ML model artifacts and runs rule-based inference."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["deploy_model", "undeploy_model", "run_inference", "list_deployments"]},
                "deployment_id": {"type": "string"}, "model_name": {"type": "string"}, "version": {"type": "string"},
                "model_path": {"type": "string", "description": "Path to the model artifact file (e.g., a JSON rule file)."},
                "input_data": {"type": "object"}
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

    def _save_deployments(self):
        with open(self.deployments_file, 'w') as f: json.dump(self.deployments, f, indent=4)

    def deploy_model(self, deployment_id: str, model_name: str, version: str, model_path: str) -> Dict[str, Any]:
        """Deploys a model by copying its artifact to the serving location."""
        if not all([deployment_id, model_name, version, model_path]):
            raise ValueError("Deployment ID, model name, version, and model path are required.")
        if deployment_id in self.deployments:
            raise ValueError(f"Deployment with ID '{deployment_id}' already exists.")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model artifact not found at '{model_path}'.")

        artifact_dir = os.path.join(self.artifacts_dir, deployment_id)
        os.makedirs(artifact_dir)
        artifact_dest_path = os.path.join(artifact_dir, os.path.basename(model_path))
        shutil.copy(model_path, artifact_dest_path)

        new_deployment = {
            "deployment_id": deployment_id, "model_name": model_name, "version": version,
            "status": "deployed", "artifact_path": artifact_dest_path,
            "inference_count": 0, "deployed_at": datetime.now().isoformat()
        }
        self.deployments[deployment_id] = new_deployment
        self._save_deployments()
        self.logger.info(f"Model '{model_name}' v{version} deployed as '{deployment_id}'.")
        return new_deployment

    def undeploy_model(self, deployment_id: str) -> Dict[str, Any]:
        """Undeploys a model by removing its artifact and updating its status."""
        deployment = self.deployments.get(deployment_id)
        if not deployment: raise ValueError(f"Deployment '{deployment_id}' not found.")
        if deployment["status"] == "undeployed": raise ValueError("Model already undeployed.")

        artifact_dir = os.path.join(self.artifacts_dir, deployment_id)
        if os.path.exists(artifact_dir):
            shutil.rmtree(artifact_dir)

        deployment["status"] = "undeployed"
        deployment["undeployed_at"] = datetime.now().isoformat()
        self._save_deployments()
        self.logger.info(f"Deployment '{deployment_id}' has been undeployed.")
        return deployment

    def run_inference(self, deployment_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs inference using the deployed model's rules."""
        deployment = self.deployments.get(deployment_id)
        if not deployment or deployment['status'] != 'deployed':
            raise ValueError(f"Deployment '{deployment_id}' is not active.")

        model_path = deployment['artifact_path']
        with open(model_path, 'r') as f:
            model_rules = json.load(f)

        prediction = "default"
        for rule in model_rules.get("rules", []):
            feature, op, value = rule["feature"], rule["operator"], rule["value"]
            input_val = input_data.get(feature)
            if input_val is None: continue
            
            if (op == ">" and input_val > value) or \
               (op == "<" and input_val < value) or \
               (op == "==" and input_val == value):
                prediction = rule["prediction"]
                break
        
        deployment["inference_count"] += 1
        self._save_deployments()
        return {"prediction": prediction, "input_data": input_data}

    def list_deployments(self, status: Optional[str] = "deployed") -> List[Dict[str, Any]]:
        """Lists all deployments, optionally filtered by status."""
        return [d for d in self.deployments.values() if d.get("status") == status] if status else list(self.deployments.values())

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "deploy_model": self.deploy_model, "undeploy_model": self.undeploy_model,
            "run_inference": self.run_inference, "list_deployments": self.list_deployments
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MachineLearningModelDeployerTool functionality...")
    temp_dir = "temp_ml_deployer_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    deployer_tool = MachineLearningModelDeployerTool(data_dir=temp_dir)
    
    # 1. Create a dummy model file
    dummy_model_path = os.path.join(temp_dir, "fraud_model.json")
    model_definition = {
        "rules": [
            {"feature": "amount", "operator": ">", "value": 1000, "prediction": "high_risk"},
            {"feature": "amount", "operator": ">", "value": 500, "prediction": "medium_risk"}
        ]
    }
    with open(dummy_model_path, 'w') as f:
        json.dump(model_definition, f)

    try:
        # 2. Deploy the model
        print("\n--- Deploying a model ---")
        deployer_tool.execute(
            operation="deploy_model", deployment_id="fraud_v1",
            model_name="fraud_detector", version="1.0", model_path=dummy_model_path
        )
        print("Model 'fraud_v1' deployed.")

        # 3. Run inference
        print("\n--- Running inference ---")
        inference1 = deployer_tool.execute(operation="run_inference", deployment_id="fraud_v1", input_data={"amount": 1200})
        print(f"Input: {{'amount': 1200}}, Prediction: {inference1['prediction']}")
        
        inference2 = deployer_tool.execute(operation="run_inference", deployment_id="fraud_v1", input_data={"amount": 750})
        print(f"Input: {{'amount': 750}}, Prediction: {inference2['prediction']}")

        # 4. List deployments
        print("\n--- Listing active deployments ---")
        active_deps = deployer_tool.execute(operation="list_deployments", status="deployed")
        print(json.dumps(active_deps, indent=2))

        # 5. Undeploy the model
        print("\n--- Undeploying the model ---")
        deployer_tool.execute(operation="undeploy_model", deployment_id="fraud_v1")
        print("Model 'fraud_v1' undeployed.")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
