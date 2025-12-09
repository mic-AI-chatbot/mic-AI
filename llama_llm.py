import os
from typing import Any, Dict, List, AsyncGenerator
from llama_cpp import Llama
from .base_llm import BaseLLM
import json

class LlamaLLM(BaseLLM):
    """
    A class to interact with a local GGUF model using llama-cpp-python.
    """

    def __init__(self, model_path: str, **kwargs):
        """
        Initializes the LlamaLLM.

        Args:
            model_path: The path to the GGUF model file.
        """
        super().__init__(model_name=os.path.basename(model_path))
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")

        llama_params = {
            "n_ctx": 4096,
            "n_gpu_layers": 0,
            "verbose": True,
        }
        llama_params.update(kwargs)

        try:
            print(f"LlamaLLM: Loading model from '{self.model_name}'. This may take a moment...")
            self.llm = Llama(model_path=model_path, **llama_params)
            print("LlamaLLM: Model loaded successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to load GGUF model. Error: {e}")

    async def stream_response(self, prompt: str, tools: List[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generates a response from the local GGUF model and streams the output.

        Args:
            prompt: The user's prompt.
            tools: A list of tool definitions.

        Yields:
            A dictionary for each event in the stream (e.g., token, tool_call).
        """
        import time
        print(f"[{time.time()}] LlamaLLM.stream_response: Entered method.")

        messages = [{"role": "user", "content": prompt}]
        
        generation_args = {
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.95,
            "stop": ["<|end|>", "<|user|>"],
        }

        try:
            print(f"[{time.time()}] LlamaLLM.stream_response: Calling create_chat_completion...")
            stream = self.llm.create_chat_completion(
                messages=messages,
                tools=tools,
                tool_choice="auto",
                stream=True,
                **generation_args
            )
            print(f"[{time.time()}] LlamaLLM.stream_response: Got stream object. Starting iteration...")
            
            first_chunk = True
            for chunk in stream:
                if first_chunk:
                    print(f"[{time.time()}] LlamaLLM.stream_response: Received first chunk from model.")
                    first_chunk = False
                
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                if "tool_calls" in delta and delta["tool_calls"]:
                    tool_call = delta["tool_calls"][0]
                    yield {
                        "type": "tool_call",
                        "tool_name": tool_call["function"]["name"],
                        "args": json.loads(tool_call["function"]["arguments"])
                    }
                elif "content" in delta and delta["content"]:
                    yield {"type": "token", "content": delta["content"]}

        except Exception as e:
            print(f"An error occurred while generating response: {e}")
            yield {"type": "error", "content": "Sorry, I encountered an error."}

    

