

import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MachineLearningModelDebuggerTool(BaseTool):
    """
    A tool for debugging machine learning models by performing real data analysis
    on predictions and datasets, and generating visualizations.
    """

    def __init__(self, tool_name: str = "MLModelDebugger", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.reports_file = os.path.join(self.data_dir, "ml_debug_reports.json")
        self.viz_dir = os.path.join(self.data_dir, "visualizations")
        os.makedirs(self.viz_dir, exist_ok=True)
        self.reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Debugs ML models by analyzing predictions, data quality, and generating visualizations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["analyze_predictions", "identify_data_issues", "visualize_feature_importance"]},
                "debug_id": {"type": "string"}, "model_name": {"type": "string"},
                "predictions": {"type": "array", "description": "List of {'predicted': val, 'actual': val} dicts."},
                "dataset_sample": {"type": "array", "description": "List of data dictionaries."},
                "feature_importance": {"type": "object", "description": "Dict of {'feature': importance_score}."},
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

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.reports, f, indent=4)

    def analyze_predictions(self, debug_id: str, model_name: str, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes model predictions for accuracy and biases."""
        if not all([debug_id, model_name, predictions]):
            raise ValueError("Debug ID, model name, and predictions are required.")
        
        correct = sum(1 for p in predictions if p['predicted'] == p['actual'])
        accuracy = (correct / len(predictions)) * 100 if predictions else 0
        
        predicted_dist = Counter(p['predicted'] for p in predictions)
        actual_dist = Counter(p['actual'] for p in predictions)
        
        mismatches = Counter()
        for p in predictions:
            if p['predicted'] != p['actual']:
                mismatches[(p['actual'], p['predicted'])] += 1

        analysis = {
            "accuracy_percent": round(accuracy, 2),
            "predicted_distribution": dict(predicted_dist),
            "actual_distribution": dict(actual_dist),
            "top_3_mismatches": {f"actual_{k[0]}_predicted_{k[1]}": v for k, v in mismatches.most_common(3)}
        }
        
        report = {"debug_id": debug_id, "model_name": model_name, "debug_type": "prediction_analysis", "analysis": analysis}
        self.reports[debug_id] = report
        self._save_reports()
        return report

    def identify_data_issues(self, debug_id: str, dataset_sample: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identifies potential issues in a dataset sample."""
        if not all([debug_id, dataset_sample]):
            raise ValueError("Debug ID and dataset sample are required.")
        
        issues = {"missing_values": {}, "statistics": {}, "zero_variance_columns": []}
        if not dataset_sample: return issues

        df = {k: [d.get(k) for d in dataset_sample] for k in dataset_sample[0]}

        for col, values in df.items():
            # Missing values
            missing_count = sum(1 for v in values if v is None)
            if missing_count > 0:
                issues["missing_values"][col] = f"{missing_count}/{len(values)}"
            
            # Statistics for numeric columns
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if numeric_values:
                issues["statistics"][col] = {
                    "mean": round(np.mean(numeric_values), 2), "std": round(np.std(numeric_values), 2),
                    "min": np.min(numeric_values), "max": np.max(numeric_values)
                }
                if np.std(numeric_values) == 0:
                    issues["zero_variance_columns"].append(col)

        report = {"debug_id": debug_id, "debug_type": "data_issue_identification", "issues": issues}
        self.reports[debug_id] = report
        self._save_reports()
        return report

    def visualize_feature_importance(self, debug_id: str, model_name: str, feature_importance: Dict[str, float]) -> Dict[str, Any]:
        """Generates and saves a bar chart of feature importances."""
        if not all([debug_id, model_name, feature_importance]):
            raise ValueError("Debug ID, model name, and feature importance data are required.")

        features = list(feature_importance.keys())
        importances = list(feature_importance.values())
        
        fig, ax = plt.subplots()
        ax.barh(features, importances)
        ax.set_xlabel("Importance Score")
        ax.set_title(f"Feature Importance for {model_name}")
        plt.tight_layout()

        output_path = os.path.join(self.viz_dir, f"{debug_id}_feature_importance.png")
        plt.savefig(output_path)
        plt.close(fig)
        
        report = {"debug_id": debug_id, "debug_type": "visualization", "visualization_type": "feature_importance", "output_path": output_path}
        self.reports[debug_id] = report
        self._save_reports()
        return report

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "analyze_predictions": self.analyze_predictions,
            "identify_data_issues": self.identify_data_issues,
            "visualize_feature_importance": self.visualize_feature_importance,
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MachineLearningModelDebuggerTool functionality...")
    temp_dir = "temp_ml_debugger_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    debugger_tool = MachineLearningModelDebuggerTool(data_dir=temp_dir)
    
    try:
        # --- Analyze Predictions ---
        print("\n--- Analyzing model predictions ---")
        preds = [
            {"predicted": "cat", "actual": "cat"}, {"predicted": "dog", "actual": "cat"},
            {"predicted": "cat", "actual": "cat"}, {"predicted": "bird", "actual": "dog"}
        ]
        analysis = debugger_tool.execute(operation="analyze_predictions", debug_id="pred_01", model_name="pet_classifier", predictions=preds)
        print(json.dumps(analysis, indent=2))

        # --- Identify Data Issues ---
        print("\n--- Identifying data issues ---")
        dataset = [{"feat1": 10, "feat2": 20}, {"feat1": 12, "feat2": None}, {"feat1": 10, "feat2": 20}]
        issues = debugger_tool.execute(operation="identify_data_issues", debug_id="data_01", dataset_sample=dataset)
        print(json.dumps(issues, indent=2))

        # --- Visualize Feature Importance ---
        print("\n--- Visualizing feature importance ---")
        f_importance = {"age": 0.4, "income": 0.5, "location": 0.1}
        viz = debugger_tool.execute(operation="visualize_feature_importance", debug_id="viz_01", model_name="churn_model", feature_importance=f_importance)
        print(json.dumps(viz, indent=2))
        print(f"Visualization saved to: {viz['output_path']}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        import shutil
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
