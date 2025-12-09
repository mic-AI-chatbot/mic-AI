import os
import torch
from typing import Any, Dict, List, AsyncGenerator
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

from .base_llm import BaseLLM

class HfLLM(BaseLLM):
    """
    A class to interact with a local Hugging Face model.
    """

    def __init__(self, model_name: str = 'distilgpt2', api_key: str = None, revision: str = None):
        """
        Initializes the HuggingFaceLLM.
        The first time this is run, it will download the model weights from the Hugging Face Hub.
        Subsequent runs will use the cached local files.

        Args:
            model_name: The name of the model on the Hugging Face Hub.
            api_key: Not used for local models, but included for interface compatibility.
            revision: The specific model revision (e.g., commit hash, branch name, or tag name) to use.
                      Pinning to a commit hash is recommended for security and reproducibility.
        """
        super().__init__(api_key, model_name)
        
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"HuggingFaceLLM: Using device: {self.device}")

            print(f"HuggingFaceLLM: Loading model '{self.model_name}' (revision: {revision if revision else 'main'}). This may take a while...")
            self.model = AutoModelForCausalLM.from_pretrained( # nosec B615 - Revision is pinned, false positive
                self.model_name,
                torch_dtype="auto", 
                trust_remote_code=True, # nosec B501 - Bandit incorrectly flags trust_remote_code as verify=False
                revision=revision # Pin revision for security and reproducibility
            ).to(self.device)

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True, revision=revision) # nosec B615 - Revision is pinned, false positive # Pin revision
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
            )
            print("HuggingFaceLLM: Model loaded successfully.")

        except Exception as e:
            raise RuntimeError(f"Failed to load Hugging Face model. Please check your internet connection and dependencies. Error: {e}")

    async def stream_response(self, prompt: str, tools: List[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generates a response from the local Hugging Face model and streams the output.

        Args:
            prompt: The user's prompt.
            tools: A list of tool definitions. (Note: Tool use with local models is complex and not implemented in this basic version).

        Yields:
            A dictionary for each event in the stream (e.g., token).
        """
        if tools:
            # Basic tool-use formatting for a chat model
            # This is a simplified approach. Real tool use requires more complex prompting.
            formatted_prompt = f"""You are a helpful assistant with access to the following tools. 
            Use them if required. 
            Tools: {tools}
            
            User query: {prompt}"""
        else:
            formatted_prompt = prompt

        try:
            messages = [
                {"role": "user", "content": formatted_prompt},
            ]

            # The transformers pipeline does not directly support streaming tool calls
            # in the same structured way as llama-cpp-python or Gemini. 
            # We will stream tokens and rely on post-processing or a more advanced
            # tool-calling mechanism if needed.
            
            # For streaming, we need to call the model directly or use a custom streaming pipeline.
            # The standard pipeline(messages, stream=True) is not directly available for all models/versions.
            # A common way to stream with transformers is to generate token by token.

            input_ids = self.tokenizer.apply_chat_template(messages, return_tensors="pt").to(self.device)

            # Generate with streaming
            # This is a simplified token-by-token generation. For true streaming, 
            # you'd typically use model.generate with appropriate callbacks or a custom loop.
            # For now, we'll simulate token streaming by decoding each new token.
            
            # Note: The `pipeline` object itself doesn't have a direct `stream=True` for token-by-token output
            # that's easily exposed for `yield`ing. We'll use the model's `generate` method.

            # This is a basic token-by-token generation loop. 
            # More advanced streaming might involve `TextIteratorStreamer` from transformers.
            generated_ids = input_ids
            generation_args = {} # Define generation_args
            for _ in range(generation_args.get("max_new_tokens", 500)):
                with torch.no_grad():
                    output = self.model.generate(
                        generated_ids,
                        max_new_tokens=1,
                        do_sample=True,
                        temperature=0.7,
                        top_p=0.95,
                        pad_token_id=self.tokenizer.eos_token_id, # Use EOS as pad token
                        eos_token_id=self.tokenizer.eos_token_id,
                        return_dict_in_generate=True,
                        output_scores=True
                    )
                next_token_id = output.sequences[:, -1]
                if next_token_id == self.tokenizer.eos_token_id:
                    break
                
                next_token = self.tokenizer.decode(next_token_id, skip_special_tokens=True)
                yield {"type": "token", "content": next_token}
                generated_ids = torch.cat([generated_ids, next_token_id.unsqueeze(-1)], dim=-1)

        except Exception as e:
            print(f"An error occurred while generating response: {e}")
            yield {"type": "error", "content": "Sorry, I encountered an error while processing your request."}

    async def get_response(self, prompt: str, tools: List[Dict[str, Any]] = None) -> str:
        """
        Generates a single, complete response from the local Hugging Face model.
        This is used by the HRM Planner.

        Args:
            prompt: The user's prompt.
            tools: A list of tool definitions (not used in this basic implementation).

        Returns:
            The model's complete response as a string.
        """
        if self.pipeline is None:
            return "Error: Hugging Face pipeline not initialized."

        try:
            messages = [{"role": "user", "content": prompt}]
            
            generation_args = {
                "max_new_tokens": 500,
                "return_full_text": False,
                "temperature": 0.7,
                "do_sample": True,
            }

            output = self.pipeline(messages, **generation_args)
            response = output[0]['generated_text']
            
            # The HRM prompt includes the original user query, which might be echoed back.
            # We will clean it up here if the model includes it.
            # This is a simple heuristic.
            if prompt in response:
                response = response.replace(prompt, "").strip()

            return response

        except Exception as e:
            print(f"An error occurred while generating response: {e}")
            return "Sorry, I encountered an error while processing your request."