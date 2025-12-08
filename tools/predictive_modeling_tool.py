import logging
import json
import pandas as pd
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.metrics import mean_squared_error, accuracy_score, r2_score
import joblib # For saving/loading models
import os

logger = logging.getLogger(__name__)

class PredictiveModelingTool(BaseTool):
    """
    A tool for performing predictive modeling actions, including training,
    evaluating, and making predictions with various scikit-learn models.
    """

    def __init__(self, tool_name: str = "PredictiveModeling", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.models: Dict[str, Any] = {} # In-memory storage for loaded models

    @property
    def description(self) -> str:
        return "Performs predictive modeling: train, evaluate, and make predictions with scikit-learn models."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["train_model", "make_prediction", "evaluate_model", "load_model", "save_model"]},
                "model_name": {"type": "string"},
                "model_type": {"type": "string", "enum": ["linear_regression", "logistic_regression", "decision_tree_classifier", "decision_tree_regressor"]},
                "data": {"type": "object", "description": "Input data as a list of dicts or JSON string."},
                "target_column": {"type": "string", "description": "The name of the target column."},
                "features": {"type": "array", "items": {"type": "string"}, "description": "List of feature column names."},
                "input_data": {"type": "object", "description": "Input data for prediction as a list of dicts or JSON string."},
                "file_path": {"type": "string", "description": "Absolute path to save/load the model file."}
            },
            "required": ["operation", "model_name"]
        }

    def _load_data_to_df(self, data_source: Union[str, List[Dict[str, Any]]]) -> pd.DataFrame:
        """Helper to load data into DataFrame from various sources."""
        if isinstance(data_source, list) and all(isinstance(i, dict) for i in data_source):
            return pd.DataFrame(data_source)
        elif isinstance(data_source, str):
            try:
                return pd.DataFrame(json.loads(data_source))
            except json.JSONDecodeError:
                raise ValueError("Unsupported data source format. Provide list of dicts or JSON string.")
        else:
            raise ValueError("Unsupported data source type.")

    def _train_model(self, model_name: str, model_type: str, data: List[Dict[str, Any]], target_column: str, features: Optional[List[str]] = None) -> Dict[str, Any]:
        """Trains a predictive model."""
        data_df = self._load_data_to_df(data)
        if target_column not in data_df.columns: raise ValueError(f"Target column '{target_column}' not found in data.")
        
        X = data_df[features] if features else data_df.drop(columns=[target_column])
        y = data_df[target_column]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = None
        if model_type == "linear_regression": model = LinearRegression()
        elif model_type == "logistic_regression": model = LogisticRegression(solver='liblinear')
        elif model_type == "decision_tree_classifier": model = DecisionTreeClassifier()
        elif model_type == "decision_tree_regressor": model = DecisionTreeRegressor()
        else: raise ValueError(f"Unsupported model type: {model_type}")

        model.fit(X_train, y_train)
        self.models[model_name] = model
        return {"status": "success", "message": f"Model '{model_name}' ({model_type}) trained successfully."}

    def _make_prediction(self, model_name: str, input_data: List[Dict[str, Any]]) -> List[Any]:
        """Makes predictions using a trained model."""
        if model_name not in self.models: raise ValueError(f"Model '{model_name}' not found. Train or load it first.")
        
        model = self.models[model_name]
        input_df = self._load_data_to_df(input_data)
        predictions = model.predict(input_df)
        return predictions.tolist()

    def _evaluate_model(self, model_name: str, data: List[Dict[str, Any]], target_column: str, features: Optional[List[str]] = None) -> Dict[str, Any]:
        """Evaluates the performance of a trained model."""
        if model_name not in self.models: raise ValueError(f"Model '{model_name}' not found. Train or load it first.")
        
        model = self.models[model_name]
        data_df = self._load_data_to_df(data)
        X = data_df[features] if features else data_df.drop(columns=[target_column])
        y = data_df[target_column]

        y_pred = model.predict(X)

        metrics = {}
        if isinstance(model, (LinearRegression, DecisionTreeRegressor)):
            metrics["mean_squared_error"] = round(mean_squared_error(y, y_pred), 4)
            metrics["r2_score"] = round(r2_score(y, y_pred), 4)
        elif isinstance(model, (LogisticRegression, DecisionTreeClassifier)):
            metrics["accuracy_score"] = round(accuracy_score(y, y_pred), 4)
        
        return metrics

    def _load_model(self, model_name: str, file_path: str) -> Dict[str, Any]:
        """Loads a pre-trained model from a file."""
        if not os.path.exists(file_path): raise FileNotFoundError(f"Model file not found at {file_path}")
        
        self.models[model_name] = joblib.load(file_path)
        return {"status": "success", "message": f"Model '{model_name}' loaded successfully from '{file_path}'."}

    def _save_model(self, model_name: str, file_path: str) -> Dict[str, Any]:
        """Saves a trained model to a file."""
        if model_name not in self.models: raise ValueError(f"Model '{model_name}' not found. Train the model first.")
        
        joblib.dump(self.models[model_name], file_path)
        return {"status": "success", "message": f"Model '{model_name}' saved successfully to '{file_path}'."}

    def execute(self, operation: str, model_name: str, **kwargs: Any) -> Any:
        if operation == "train_model":
            model_type = kwargs.get('model_type')
            data = kwargs.get('data')
            target_column = kwargs.get('target_column')
            if not all([model_type, data, target_column]):
                raise ValueError("Missing 'model_type', 'data', or 'target_column' for 'train_model' operation.")
            return self._train_model(model_name, model_type, data, target_column, kwargs.get('features'))
        elif operation == "make_prediction":
            input_data = kwargs.get('input_data')
            if not input_data:
                raise ValueError("Missing 'input_data' for 'make_prediction' operation.")
            return self._make_prediction(model_name, input_data)
        elif operation == "evaluate_model":
            data = kwargs.get('data')
            target_column = kwargs.get('target_column')
            if not all([data, target_column]):
                raise ValueError("Missing 'data' or 'target_column' for 'evaluate_model' operation.")
            return self._evaluate_model(model_name, data, target_column, kwargs.get('features'))
        elif operation == "load_model":
            file_path = kwargs.get('file_path')
            if not file_path:
                raise ValueError("Missing 'file_path' for 'load_model' operation.")
            return self._load_model(model_name, file_path)
        elif operation == "save_model":
            file_path = kwargs.get('file_path')
            if not file_path:
                raise ValueError("Missing 'file_path' for 'save_model' operation.")
            return self._save_model(model_name, file_path)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PredictiveModelingTool functionality...")
    temp_dir = "temp_predictive_modeling_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    modeling_tool = PredictiveModelingTool(data_dir=temp_dir)
    
    # Sample data for demonstration
    sample_data_regression = [
        {"feature1": 10, "feature2": 20, "target": 30},
        {"feature1": 12, "feature2": 22, "target": 34},
        {"feature1": 15, "feature2": 25, "target": 40},
        {"feature1": 8, "feature2": 18, "target": 26},
        {"feature1": 11, "feature2": 21, "target": 32},
    ]
    sample_data_classification = [
        {"feature1": 1, "feature2": 0, "target": 0},
        {"feature1": 0, "feature2": 1, "target": 1},
        {"feature1": 1, "feature2": 1, "target": 0},
        {"feature1": 0, "feature2": 0, "target": 1},
    ]
    
    try:
        # 1. Train a Linear Regression model
        print("\n--- Training Linear Regression model 'sales_predictor' ---")
        modeling_tool.execute(operation="train_model", model_name="sales_predictor", model_type="linear_regression",
                              data=sample_data_regression, target_column="target", features=["feature1", "feature2"])
        print("Model 'sales_predictor' trained.")

        # 2. Evaluate the Linear Regression model
        print("\n--- Evaluating 'sales_predictor' ---")
        evaluation_results = modeling_tool.execute(operation="evaluate_model", model_name="sales_predictor",
                                                   data=sample_data_regression, target_column="target", features=["feature1", "feature2"])
        print(json.dumps(evaluation_results, indent=2))

        # 3. Make predictions with the Linear Regression model
        print("\n--- Making predictions with 'sales_predictor' ---")
        prediction_input = [{"feature1": 13, "feature2": 23}]
        predictions = modeling_tool.execute(operation="make_prediction", model_name="sales_predictor", input_data=prediction_input)
        print(f"Prediction for {prediction_input}: {predictions}")

        # 4. Train a Logistic Regression model
        print("\n--- Training Logistic Regression model 'churn_classifier' ---")
        modeling_tool.execute(operation="train_model", model_name="churn_classifier", model_type="logistic_regression",
                              data=sample_data_classification, target_column="target", features=["feature1", "feature2"])
        print("Model 'churn_classifier' trained.")

        # 5. Save the Logistic Regression model
        model_save_path = os.path.join(temp_dir, "churn_classifier.joblib")
        print(f"\n--- Saving 'churn_classifier' to {model_save_path} ---")
        modeling_tool.execute(operation="save_model", model_name="churn_classifier", file_path=model_save_path)
        print("Model saved.")

        # 6. Load the Logistic Regression model
        print(f"\n--- Loading 'churn_classifier_loaded' from {model_save_path} ---")
        modeling_tool.execute(operation="load_model", model_name="churn_classifier_loaded", file_path=model_save_path)
        print("Model loaded.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")