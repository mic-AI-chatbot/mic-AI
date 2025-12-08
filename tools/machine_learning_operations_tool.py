

import logging
import os
import json
import random
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool
# Import the tools this orchestrator will use
from tools.machine_learning_model_deployer import MachineLearningModelDeployerTool
from tools.performance_monitoring_tool import PerformanceMonitoringTool

logger = logging.getLogger(__name__)

class MachineLearningOperationsTool(BaseTool):
    """
    An MLOps orchestration tool that manages the lifecycle of ML models by integrating
    with other specialized tools for deployment and monitoring.
    """

    def __init__(self, tool_name: str = "MLOpsOrchestrator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.models_file = os.path.join(self.data_dir, "ml_models_registry.json")
        self.ops_logs_file = os.path.join(self.data_dir, "ml_ops_logs.json")
        self.models: Dict[str, Dict[str, Any]] = self._load_data(self.models_file, default={})
        self.ops_logs: List[Dict[str, Any]] = self._load_data(self.ops_logs_file, default=[])

        # Instantiate the tools it orchestrates
        self.deployer = MachineLearningModelDeployerTool(data_dir=os.path.join(data_dir, "deployer"))
        self.monitor = PerformanceMonitoringTool(data_dir=os.path.join(data_dir, "monitor"))

    @property
    def description(self) -> str:
        return "Orchestrates the ML model lifecycle: registration, deployment, monitoring, and versioning."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["register_model", "deploy_model", "monitor_performance", "version_model", "get_model_status"]},
                "model_id": {"type": "string"}, "name": {"type": "string"}, "version": {"type": "string"},
                "description": {"type": "string"}, "environment": {"type": "string", "default": "production"},
                "model_artifact_content": {"type": "object", "description": "JSON content for the dummy model artifact."}
            },
            "required": ["operation", "model_id"]
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
        with open(self.models_file, 'w') as f: json.dump(self.models, f, indent=4)

    def _save_ops_logs(self):
        with open(self.ops_logs_file, 'w') as f: json.dump(self.ops_logs, f, indent=4)

    def _log_op(self, model_id: str, op_type: str, details: Dict):
        log_entry = {"timestamp": datetime.now().isoformat(), "model_id": model_id, "operation": op_type, "details": details}
        self.ops_logs.append(log_entry)
        self._save_ops_logs()

    def register_model(self, model_id: str, name: str, version: str, description: str) -> Dict[str, Any]:
        """Registers a new model in the central registry."""
        if model_id in self.models: raise ValueError(f"Model with ID '{model_id}' already exists.")
        
        new_model = {
            "model_id": model_id, "name": name, "version": version, "description": description,
            "status": "registered", "deployments": {}, "registered_at": datetime.now().isoformat()
        }
        self.models[model_id] = new_model
        self._save_models()
        self._log_op(model_id, "register", {"version": version})
        return new_model

    def deploy_model(self, model_id: str, environment: str, model_artifact_content: Dict) -> Dict[str, Any]:
        """Deploys a model by creating an artifact and calling the deployer tool."""
        model = self.models.get(model_id)
        if not model: raise ValueError(f"Model '{model_id}' not found.")

        # Create a dummy artifact file to be deployed
        artifact_path = os.path.join(self.data_dir, f"{model_id}_{model['version']}_artifact.json")
        with open(artifact_path, 'w') as f:
            json.dump(model_artifact_content, f)

        deployment_id = f"{model_id}_{environment}"
        try:
            self.deployer.execute(
                operation="deploy_model", deployment_id=deployment_id,
                model_name=model['name'], version=model['version'], model_path=artifact_path
            )
            status = "deployed"
        except Exception as e:
            status = "failed"
            self.logger.error(f"Deployment for {model_id} failed: {e}")
        
        os.remove(artifact_path) # Clean up temp artifact

        model["deployments"][environment] = {"status": status, "deployed_at": datetime.now().isoformat()}
        model["status"] = status
        self._save_models()
        self._log_op(model_id, "deploy", {"environment": environment, "status": status})
        return model

    def monitor_performance(self, model_id: str, environment: str) -> Dict[str, Any]:
        """Monitors performance by recording a simulated metric in the monitoring tool."""
        model = self.models.get(model_id)
        if not model or model["deployments"].get(environment, {}).get("status") != "deployed":
            raise ValueError(f"Model '{model_id}' is not deployed in '{environment}'.")

        # Simulate a performance metric
        accuracy = round(random.uniform(0.7, 0.99), 4)  # nosec B311
        system_name = f"{model_id}_{environment}"
        
        self.monitor.execute(
            operation="record_metric", system_name=system_name,
            metric_name="accuracy", metric_value=accuracy
        )
        
        report = {"model_id": model_id, "metric": "accuracy", "value": accuracy}
        self._log_op(model_id, "monitor", {"environment": environment, "report": report})
        return report

    def version_model(self, model_id: str, new_version: str) -> Dict[str, Any]:
        """Updates the version of a registered model."""
        model = self.models.get(model_id)
        if not model: raise ValueError(f"Model '{model_id}' not found.")
        
        model["version"] = new_version
        self._save_models()
        self._log_op(model_id, "version", {"new_version": new_version})
        return model

    def get_model_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the status of a model from the registry."""
        return self.models.get(model_id)

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "register_model": self.register_model, "deploy_model": self.deploy_model,
            "monitor_performance": self.monitor_performance, "version_model": self.version_model,
            "get_model_status": self.get_model_status
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MLOpsOrchestrator functionality...")
    temp_dir = "temp_mlops_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    orchestrator = MachineLearningOperationsTool(data_dir=temp_dir)
    
    try:
        # 1. Register a new model
        print("\n--- Registering model 'fraud_detector' ---")
        orchestrator.execute(operation="register_model", model_id="fraud_detector", name="Fraud Detector", version="1.0", description="Detects fraud.")

        # 2. Deploy the model (which calls the deployer tool)
        print("\n--- Deploying model to production ---")
        dummy_artifact = {"rules": [{"feature": "amount", "operator": ">", "value": 1000, "prediction": "high_risk"}]}
        orchestrator.execute(operation="deploy_model", model_id="fraud_detector", environment="production", model_artifact_content=dummy_artifact)
        
        # 3. Monitor performance (which calls the monitor tool)
        print("\n--- Monitoring model performance ---")
        perf_report = orchestrator.execute(operation="monitor_performance", model_id="fraud_detector", environment="production")
        print(f"Performance report: {perf_report}")

        # 4. Verify integration by checking the other tools' data
        print("\n--- Verifying integration ---")
        deployer_deployments = orchestrator.deployer.execute(operation="list_deployments")
        print(f"Deployer has {len(deployer_deployments)} active deployments.")
        
        monitor_metrics = orchestrator.monitor.execute(operation="list_metrics", system_name="fraud_detector_production")
        print(f"Monitor has {len(monitor_metrics)} metrics for 'fraud_detector_production'.")
        print(json.dumps(monitor_metrics, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")

