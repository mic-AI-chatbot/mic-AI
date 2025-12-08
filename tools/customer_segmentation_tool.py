import logging
import json
import random
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from typing import Union, List, Dict, Any, Optional
from tools.base_tool import BaseTool

# Deferring scikit-learn and transformers imports
try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    KMeans = None
    silhouette_score = None
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn library not found. Customer segmentation will be limited.")

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered segment analysis will not be available.")

logger = logging.getLogger(__name__)

def _load_data_to_df(data_source: Union[str, List[Dict[str, Any]], Any]) -> pd.DataFrame:
    """
    Helper to load data into DataFrame from various sources.
    """
    if pd is None:
        raise ImportError("The 'pandas' library is not installed. Please install it with 'pip install pandas'.")
    if isinstance(data_source, pd.DataFrame):
        return data_source
    elif isinstance(data_source, list) and all(isinstance(i, dict) for i in data_source):
        return pd.DataFrame(data_source)
    elif isinstance(data_source, str):
        try:
            # Try loading as JSON string
            return pd.DataFrame(json.loads(data_source))
        except json.JSONDecodeError:
            # Assume it's a file path
            if data_source.endswith('.csv'):
                return pd.read_csv(data_source)
            elif data_source.endswith('.json'):
                return pd.read_json(data_source)
            else:
                raise ValueError("Unsupported data source format. Provide DataFrame, list of dicts, JSON string, or .csv/.json file path.")
    else:
        raise ValueError("Unsupported data source type.")

class SegmentAnalysisModel:
    """Manages the text generation model for segment analysis, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SegmentAnalysisModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for segment analysis are not installed.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for segment analysis...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if self._generator is None:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

segment_analysis_model_instance = SegmentAnalysisModel()

class SegmentCustomersTool(BaseTool):
    """Segments customers into distinct groups using K-Means clustering."""
    def __init__(self, tool_name="segment_customers"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Segments customers into distinct groups using K-Means clustering based on provided customer data and features."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": ["string", "array", "object"],
                    "description": "Customer data as a DataFrame, list of dicts, JSON string, or .csv/.json file path."
                },
                "n_segments": {"type": "integer", "description": "The number of customer segments to create.", "default": 3},
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: A list of numerical features to use for segmentation. If not provided, all numerical features will be used.",
                    "default": []
                }
            },
            "required": ["data"]
        }

    def execute(self, data: Union[str, List[Dict[str, Any]], Any], n_segments: int = 3, features: Optional[List[str]] = None, **kwargs: Any) -> str:
        if not SKLEARN_AVAILABLE:
            return json.dumps({"error": "Scikit-learn library is not installed. Please install it with 'pip install scikit-learn'."})
        if pd is None:
            return json.dumps({"error": "Pandas library is not installed. Please install it with 'pip install pandas'."})

        try:
            df = _load_data_to_df(data)
        except (ImportError, ValueError, json.JSONDecodeError, FileNotFoundError) as e:
            return json.dumps({"error": f"Failed to load data: {e}"})

        numerical_df = df.select_dtypes(include=np.number)
        if numerical_df.empty:
            return json.dumps({"error": "No numerical features found in the provided data for segmentation."})

        if features:
            missing_features = [f for f in features if f not in numerical_df.columns]
            if missing_features:
                return json.dumps({"error": f"Missing specified features in data: {', '.join(missing_features)}."})
            X = numerical_df[features]
        else:
            X = numerical_df

        if X.shape[0] < n_segments:
            return json.dumps({"error": f"Number of samples ({X.shape[0]}) is less than the number of segments ({n_segments}). Cannot perform clustering."})
        
        try:
            kmeans = KMeans(n_clusters=n_segments, random_state=42, n_init=10)
            df['segment'] = kmeans.fit_predict(X)
            
            # Calculate silhouette score for evaluation
            score = None
            if X.shape[0] > 1 and len(np.unique(df['segment'])) > 1:
                try:
                    score = silhouette_score(X, df['segment'])
                except Exception as e:
                    logger.warning(f"Could not calculate silhouette score: {e}")

            # Summarize segments
            segment_summary = df.groupby('segment').agg(['mean', 'std']).to_dict('index')
            
            return json.dumps({
                "message": "Customer segmentation performed successfully.",
                "n_segments": n_segments,
                "silhouette_score": score,
                "segment_summary": segment_summary,
                "customer_segments_sample": df[['segment']].head().to_dict('index') # Return segment for first few customer indices
            }, indent=2)
        except Exception as e:
            logger.error(f"Error during K-Means clustering: {e}")
            return json.dumps({"error": f"Error during K-Means clustering: {e}"})

class AnalyzeCustomerSegmentsTool(BaseTool):
    """Analyzes the characteristics of identified customer segments using an AI model."""
    def __init__(self, tool_name="analyze_customer_segments"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes the characteristics of identified customer segments, providing insights into their unique attributes and behaviors using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "segment_summary_json": {
                    "type": "string",
                    "description": "The JSON summary of customer segments (e.g., output from SegmentCustomersTool)."
                },
                "segment_id": {"type": "integer", "description": "Optional: The ID of a specific segment to analyze in detail.", "default": None}
            },
            "required": ["segment_summary_json"]
        }

    def execute(self, segment_summary_json: str, segment_id: Optional[int] = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "AI models for segment analysis are not available. Please install 'transformers', 'torch'."})

        try:
            segment_summary = json.loads(segment_summary_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for segment_summary_json."})

        prompt = f"Analyze the following customer segment summary. "
        if segment_id is not None:
            if str(segment_id) in segment_summary:
                prompt += f"Focus on segment {segment_id} with characteristics: {json.dumps(segment_summary[str(segment_id)])}. "
            else:
                return json.dumps({"error": f"Segment ID '{segment_id}' not found in summary."})
        
        prompt += f"Provide insights into their unique attributes and behaviors, and suggest potential marketing strategies. Provide the output in JSON format with keys 'analysis_summary', 'insights', and 'marketing_strategies'.\n\nSegment Summary: {json.dumps(segment_summary)}\n\nJSON Output:"
        
        llm_response = segment_analysis_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})