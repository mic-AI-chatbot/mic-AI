import logging
import json
import pandas as pd
import numpy as np
from typing import Union, List, Dict, Any, Tuple
from tools.base_tool import BaseTool
from statsmodels.tsa.arima.model import ARIMA
import joblib
import os
import warnings

logger = logging.getLogger(__name__)

class TimeSeriesForecastingTool(BaseTool):
    """
    A tool for performing time series forecasting using ARIMA models.
    It supports training, forecasting, evaluation, and model persistence.
    """

    def __init__(self, tool_name: str = "time_series_forecasting_tool"):
        super().__init__(tool_name)
        self.models: Dict[str, Any] = {}

    @property
    def description(self) -> str:
        return "Performs time series forecasting (training, prediction, evaluation) using ARIMA models."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform: 'train', 'forecast', 'evaluate', 'find_best_order', 'save_model', 'load_model'."
                },
                "model_name": {"type": "string", "description": "A unique name for the model."},
                "data": {
                    "type": "string",
                    "description": "Data source for training or evaluation. Can be a JSON string, list, or a path to a .csv/.json file."
                },
                "steps": {"type": "integer", "description": "The number of future steps to forecast."},
                "order": {"type": "array", "items": {"type": "integer"}, "description": "A tuple for the ARIMA order (p,d,q)."},
                "file_path": {"type": "string", "description": "File path for saving or loading a model."},
                "output_format": {"type": "string", "description": "Output format ('json' or 'text').", "default": "json"}
            },
            "required": ["action", "model_name"]
        }

    def execute(self, action: str, **kwargs: Any) -> Union[str, Dict, List]:
        try:
            action = action.lower()
            model_name = kwargs.get("model_name")
            if not model_name:
                return self._format_output({"error": "'model_name' is a required parameter."}, kwargs.get("output_format", "json"))

            actions = {
                "train": self._train_model,
                "forecast": self._make_forecast,
                "evaluate": self._evaluate_model,
                "find_best_order": self._find_best_order,
                "save_model": self._save_model,
                "load_model": self._load_model,
            }

            if action not in actions:
                raise ValueError(f"Invalid action '{action}'. Supported actions are: {list(actions.keys())})")

            result = actions[action](model_name=model_name, **kwargs)
            return self._format_output(result, kwargs.get("output_format", "json"))

        except Exception as e:
            logger.error(f"An error occurred in TimeSeriesForecastingTool: {e}")
            return self._format_output({"error": str(e)}, kwargs.get("output_format", "json"))

    def _load_data_to_series(self, data_source: Union[str, List[Union[int, float]], pd.Series]) -> pd.Series:
        if isinstance(data_source, pd.Series):
            return data_source
        if isinstance(data_source, list):
            return pd.Series(data_source)
        if isinstance(data_source, str):
            try:
                return pd.Series(json.loads(data_source))
            except json.JSONDecodeError:
                if data_source.endswith('.csv'):
                    return pd.read_csv(data_source, index_col=0, parse_dates=True).squeeze("columns")
                elif data_source.endswith('.json'):
                    return pd.read_json(data_source, orient='series')
                raise ValueError("Unsupported file format. Use .csv or .json.")
        raise TypeError("Unsupported data source type.")

    def _train_model(self, model_name: str, data: Any, order: Tuple[int, int, int] = (5, 1, 0), **kwargs) -> Dict:
        data_series = self._load_data_to_series(data)
        model = ARIMA(data_series, order=order)
        model_fit = model.fit()
        self.models[model_name] = model_fit
        return {"message": f"Model '{model_name}' (ARIMA) trained successfully.", "summary": str(model_fit.summary())}

    def _make_forecast(self, model_name: str, steps: int, **kwargs) -> Dict:
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found.")
        model_fit = self.models[model_name]
        forecast = model_fit.get_forecast(steps=steps)
        return {
            "forecast": forecast.predicted_mean.tolist(),
            "confidence_interval": forecast.conf_int().to_dict('records')
        }

    def _evaluate_model(self, model_name: str, data: Any, steps: int, **kwargs) -> Dict:
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found.")
        
        data_series = self._load_data_to_series(data)
        if len(data_series) <= steps:
            raise ValueError("Evaluation requires more data points than forecast steps.")
            
        train_data, test_data = data_series[:-steps], data_series[-steps:]
        
        model_fit = self.models[model_name]
        # Refit the model on the training part of the data for a fair evaluation
        model = ARIMA(train_data, order=model_fit.model.order)
        refit_model = model.fit()
        
        forecast = refit_model.get_forecast(steps=steps).predicted_mean
        
        mse = np.mean((forecast - test_data)**2)
        mae = np.mean(np.abs(forecast - test_data))
        
        return {"mean_squared_error": mse, "mean_absolute_error": mae}

    def _find_best_order(self, model_name: str, data: Any, p_values: range = range(3), d_values: range = range(2), q_values: range = range(3), **kwargs) -> Dict:
        data_series = self._load_data_to_series(data)
        best_aic, best_order = float("inf"), None
        
        warnings.filterwarnings("ignore") # Suppress convergence warnings
        for p in p_values:
            for d in d_values:
                for q in q_values:
                    try:
                        model = ARIMA(data_series, order=(p,d,q))
                        model_fit = model.fit()
                        if model_fit.aic < best_aic:
                            best_aic, best_order = model_fit.aic, (p,d,q)
                    except Exception as e:
                        logger.debug(f"ARIMA with order=({p},{d},{q}) failed: {e}")
                        continue
        warnings.resetwarnings()

        if best_order:
            # Optionally train and store the best model
            self._train_model(model_name, data_series, best_order)
            return {"best_order": best_order, "best_aic": best_aic, "message": f"Model '{model_name}' has been trained with this order."}
        else:
            return {"error": "Could not find a suitable ARIMA order. Try different p,d,q ranges or check data."}

    def _load_model(self, model_name: str, file_path: str, **kwargs) -> Dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Model file not found at {file_path}")
        self.models[model_name] = joblib.load(file_path)
        return {"message": f"Model '{model_name}' loaded successfully from '{file_path}'."}

    def _save_model(self, model_name: str, file_path: str, **kwargs) -> Dict:
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found.")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        joblib.dump(self.models[model_name], file_path)
        return {"message": f"Model '{model_name}' saved successfully to '{file_path}'."}

    def _format_output(self, result: Union[Dict, List, str], output_format: str) -> Union[str, Dict, List]:
        if output_format == 'json':
            if isinstance(result, (dict, list)):
                return result 
            return json.dumps({"message": str(result)})
        else: # text format
            if isinstance(result, dict):
                return "\n".join([f"{k}: {v}" for k, v in result.items()])
            elif isinstance(result, list):
                return "\n".join([str(item) for item in result])
            return str(result)