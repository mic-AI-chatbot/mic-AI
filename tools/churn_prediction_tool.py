import logging
import json
import random
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from typing import Dict, Any, List, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class CustomerDataGenerator:
    """Generates mock customer data for churn prediction simulation."""
    def generate_data(self, num_customers: int = 1000) -> pd.DataFrame:
        data = {
            "age": np.random.randint(18, 70, num_customers),
            "tenure_months": np.random.randint(1, 60, num_customers),
            "usage_frequency": np.random.choice(["low", "medium", "high"], num_customers, p=[0.3, 0.4, 0.3]),
            "monthly_spend": np.random.normal(50, 20, num_customers).round(2),
            "customer_service_calls": np.random.randint(0, 5, num_customers)
        }
        df = pd.DataFrame(data)
        
        # Introduce churn based on some factors to create a realistic dataset
        df["churn"] = 0
        # Customers with low tenure and low usage are more likely to churn
        df.loc[(df["tenure_months"] < 12) & (df["usage_frequency"] == "low"), "churn"] = 1
        # Customers with low spend and many service calls are more likely to churn
        df.loc[(df["monthly_spend"] < 30) & (df["customer_service_calls"] > 2), "churn"] = 1
        # Older customers might have a slightly higher churn rate (simulated)
        df.loc[df["age"] > 60, "churn"] = np.random.binomial(1, 0.2, df[df["age"] > 60].shape[0])
        
        return df

class ChurnPredictorModel:
    """Trains and uses a simple ML model for churn prediction, using a singleton pattern."""
    _model = None
    _instance = None
    _feature_encoder = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChurnPredictorModel, cls).__new__(cls)
            cls._instance._train_model()
        return cls._instance

    def _train_model(self):
        data_generator = CustomerDataGenerator()
        df = data_generator.generate_data(num_customers=2000)
        
        # One-hot encode categorical features for the model
        df_encoded = pd.get_dummies(df, columns=["usage_frequency"], drop_first=True)
        
        # Store feature columns to ensure consistent input for prediction
        self._feature_encoder = list(df_encoded.drop(columns=["churn"]).columns)

        X = df_encoded.drop(columns=["churn"])
        y = df_encoded["churn"]
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self._model = LogisticRegression(random_state=42, solver='liblinear') # liblinear is good for small datasets
        self._model.fit(X_train, y_train)
        
        accuracy = accuracy_score(y_test, self._model.predict(X_test))
        logger.info(f"Churn prediction model trained with accuracy: {accuracy:.2f}")

    def predict_churn(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        if self._model is None:
            self._train_model() # Ensure model is trained if not already
        
        # Convert input customer data to DataFrame for prediction
        input_df = pd.DataFrame([customer_data])
        
        # One-hot encode categorical features, ensuring all expected columns are present
        input_df_encoded = pd.get_dummies(input_df, columns=["usage_frequency"], drop_first=True)
        
        # Align columns with training data features: add missing columns with 0, remove extra ones
        for col in self._feature_encoder:
            if col not in input_df_encoded.columns:
                input_df_encoded[col] = 0
        input_df_encoded = input_df_encoded[self._feature_encoder]

        churn_probability = self._model.predict_proba(input_df_encoded)[:, 1][0]
        prediction = "likely to churn" if churn_probability > 0.5 else "unlikely to churn"
        
        return {
            "churn_probability": churn_probability,
            "prediction": prediction
        }

churn_predictor_instance = ChurnPredictorModel()

class ChurnPredictionTool(BaseTool):
    """Predicts customer churn based on provided customer data using a machine learning model."""
    def __init__(self, tool_name="churn_prediction_tool"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Predicts customer churn based on provided customer data and returns a churn probability, prediction, and actionable recommendations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_data": {
                    "type": "object",
                    "description": "A dictionary containing customer features (e.g., {'age': 30, 'tenure_months': 12, 'usage_frequency': 'high', 'monthly_spend': 50.0, 'customer_service_calls': 1})."
                }
            },
            "required": ["customer_data"]
        }

    def execute(self, customer_data: dict, **kwargs: Any) -> str:
        prediction_results = churn_predictor_instance.predict_churn(customer_data)
        churn_probability = prediction_results["churn_probability"]
        prediction = prediction_results["prediction"]
        
        recommendations = []
        if prediction == "likely to churn":
            recommendations.append("Customer is at high risk of churn. Consider proactive outreach with personalized offers or support.")
            if customer_data.get("tenure_months", 0) < 12:
                recommendations.append("Focus on improving early customer experience and onboarding to build loyalty.")
            if customer_data.get("customer_service_calls", 0) > 2:
                recommendations.append("Investigate recent customer service interactions for unresolved issues or recurring problems.")
            if customer_data.get("monthly_spend", 0) < 40:
                recommendations.append("Consider offering incentives or discounts to increase engagement and perceived value.")
        else:
            recommendations.append("Customer is currently unlikely to churn. Continue to monitor engagement and satisfaction to maintain loyalty.")
        
        report = {
            "customer_data": customer_data,
            "churn_probability": round(churn_probability, 2),
            "prediction": prediction,
            "recommendations": recommendations
        }
        return json.dumps(report, indent=2)