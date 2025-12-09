import logging
import torch
from typing import Dict, Any, List
from tools.base_tool import BaseTool
from transformers import AutoTokenizer, AutoModel
import numpy as np

logger = logging.getLogger(__name__)

# In-memory cache for loaded models and tokenizers to avoid reloading
loaded_models: Dict[str, Dict[str, Any]] = {}

class TransferLearningTool(BaseTool):
    """
    A tool for using pre-trained models from Hugging Face for feature extraction (embeddings).
    """
    def __init__(self, tool_name: str = "transfer_learning_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Extracts text features (embeddings) using pre-trained models from Hugging Face."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "The name of the pre-trained model from Hugging Face (e.g., 'distilbert-base-uncased')."
                },
                "text_input": {
                    "type": "string",
                    "description": "The text to extract features from."
                },
                "pooling_strategy": {
                    "type": "string",
                    "description": "The pooling strategy to get a single vector ('mean' or 'cls').",
                    "default": "mean"
                }
            },
            "required": ["model_name", "text_input"]
        }

    def execute(self, model_name: str, text_input: str, pooling_strategy: str = "mean", revision: str = None, **kwargs) -> Dict:
        """
        Loads a pre-trained model and uses it to extract features from text.
        Pinning to a specific revision (e.g., commit hash) is recommended for security and reproducibility.
        """
        if not text_input:
            return {"error": "Input text cannot be empty."}

        try:
            # Use 'main' as the default revision if not provided, for security and reproducibility
            safe_revision = revision if revision else "main"

            # Load model and tokenizer, using cache if available
            if model_name not in loaded_models:
                logger.info(f"Loading model '{model_name}' (revision: {safe_revision}) for the first time...")
                tokenizer = AutoTokenizer.from_pretrained(model_name, revision=safe_revision)
                model = AutoModel.from_pretrained(model_name, revision=safe_revision)
                loaded_models[model_name] = {"tokenizer": tokenizer, "model": model}
            
            tokenizer = loaded_models[model_name]["tokenizer"]
            model = loaded_models[model_name]["model"]

            # Tokenize the input text
            inputs = tokenizer(text_input, return_tensors="pt", truncation=True, padding=True)
            
            # Get model outputs (hidden states)
            with torch.no_grad():
                outputs = model(**inputs)
            
            last_hidden_states = outputs.last_hidden_state

            # Apply pooling strategy
            if pooling_strategy == 'mean':
                # Mean pooling: average the token embeddings
                embedding = last_hidden_states.mean(dim=1).squeeze().numpy()
            elif pooling_strategy == 'cls':
                # CLS pooling: use the embedding of the [CLS] token
                embedding = last_hidden_states[:, 0, :].squeeze().numpy()
            else:
                raise ValueError("Unsupported pooling strategy. Use 'mean' or 'cls'.")

            # For simplicity, return a snippet of the embedding
            embedding_snippet = embedding[:10].tolist()

            return {
                "model_name": model_name,
                "pooling_strategy": pooling_strategy,
                "embedding_shape": embedding.shape,
                "embedding_snippet": embedding_snippet,
                "message": "Feature extraction successful."
            }

        except Exception as e:
            logger.error(f"An error occurred in TransferLearningTool: {e}")
            # If a model fails to load, remove it from the cache
            if model_name in loaded_models:
                del loaded_models[model_name]
            return {"error": f"Failed to process request. Ensure model name is correct and you have an internet connection. Details: {e}"}