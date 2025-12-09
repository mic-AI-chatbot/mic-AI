import os
from .config import GOOGLE_API_KEY, LLAMA_MODEL_PATH

class LLMLoader:
    _LLM_INSTANCE = None

    @classmethod
    def load_llm(cls, llm_type: str = "llama", api_key: str = None, model_name: str = None, model_path: str = None):
        # Lazy import to prevent circular dependencies
        from .llama_llm import LlamaLLM
        from .gemini_llm import GeminiLLM
        from .hf_llm import HfLLM

        if llm_type == "gemini":
            return GeminiLLM(api_key=api_key, model_name=model_name)
        elif llm_type == "hf":
            return HfLLM(model_name=model_name)
        elif llm_type == "llama":
            if not model_path:
                raise ValueError("model_path must be provided for LlamaLLM")
            return LlamaLLM(model_path=model_path)
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")

    @classmethod
    def get_llm(cls):
        """
        Returns the initialized LLM instance, creating it if it doesn't exist.
        """
        if cls._LLM_INSTANCE is None:
            # Default to a small, local Hugging Face model for baseline functionality.
            # The HRM will upgrade to a larger model when necessary.
            cls._LLM_INSTANCE = cls.load_llm(llm_type="hf", model_name="distilgpt2")
        return cls._LLM_INSTANCE

def get_llm():
    """
    Initializes and returns the singleton LLM instance using the LLMLoader class.
    """
    # This function now acts as a simple public interface
    # to the more complex LLMLoader class.
    try:
        # Note: The LLMLoader will default to 'llama' if not configured otherwise.
        # The server will fail to start if LLAMA_MODEL_PATH is not set and valid.
        # To use a different LLM, configure it via environment variables.
        return LLMLoader.get_llm()
    except Exception as e:
        print(f"CRITICAL: Failed to load LLM. The application may not function correctly. Error: {e}")
        return None