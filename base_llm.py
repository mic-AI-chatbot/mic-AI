
from abc import ABC, abstractmethod
from typing import Any, Dict, List, AsyncGenerator

class BaseLLM(ABC):
    """
    An abstract base class for all Large Language Models.
    """

    def __init__(self, api_key: str = None, model_name: str = None):
        """
        Initializes the BaseLLM.

        Args:
            api_key: The API key for the LLM service.
            model_name: The name of the model to use.
        """
        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    async def stream_response(self, prompt: str, tools: List[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generates a response from the LLM and streams the output.

        Args:
            prompt: The user's prompt.
            tools: A list of tools available for the model to use.

        Yields:
            A dictionary for each event in the stream (e.g., token, tool_call).
        """
        pass
