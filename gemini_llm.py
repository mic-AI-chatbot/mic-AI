import os
import json
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool
from typing import Any, Dict, List, AsyncGenerator

from .base_llm import BaseLLM

class GeminiLLM(BaseLLM):
    """
    A class to interact with the Google Gemini Large Language Model.
    """

    def __init__(self, api_key: str = None, model_name: str = 'gemini-1.5-pro-latest'):
        """
        Initializes the GeminiLLM.

        Args:
            api_key: The API key for the LLM service. If not provided,
                     it will be read from the GEMINI_API_KEY environment variable.
            model_name: The name of the Gemini model to use.
        """
        super().__init__(api_key, model_name)
        if self.api_key is None:
            self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Please set the GEMINI_API_KEY environment variable or pass it to the constructor.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    async def stream_response(self, prompt: str, tools: List[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generates a response from the Gemini model and streams the output.

        Args:
            prompt: The user's prompt.
            tools: A list of tool definitions in a dictionary format.

        Yields:
            A dictionary for each event in the stream (e.g., token, tool_call).
        """
        try:
            generation_config = GenerationConfig(temperature=0.7)
            
            # Convert dictionary tool definitions to the format expected by the Gemini API
            api_tools = [Tool.from_dict(t) for t in tools] if tools else None

            stream = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config,
                tools=api_tools,
                stream=True
            )

            async for chunk in stream:
                if chunk.candidates and chunk.candidates[0].content.parts:
                    for part in chunk.candidates[0].content.parts:
                        if part.function_call:
                            yield {
                                "type": "tool_call",
                                "tool_name": part.function_call.name,
                                "args": dict(part.function_call.args),
                            }
                        elif part.text:
                            yield {"type": "token", "content": part.text}

        except Exception as e:
            print(f"An error occurred while generating response: {e}")
            yield {"type": "error", "content": "Sorry, I encountered an error while processing your request."}

    async def get_response(self, prompt: str, tools: List[Dict[str, Any]] = None) -> str:
        """
        Generates a single, complete response from the Gemini model.
        This is used by the HRM Planner.

        Args:
            prompt: The user's prompt.
            tools: A list of tool definitions (not used by the planner).

        Returns:
            The model's complete response as a string.
        """
        try:
            generation_config = GenerationConfig(temperature=0.1) # Lower temperature for more deterministic planning
            
            # The planner decides if a tool should be used. We provide the tool definitions.
            api_tools = [Tool.from_dict(t) for t in tools] if tools else None

            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config,
                tools=api_tools
            )

            if response.candidates and response.candidates[0].content.parts:
                first_part = response.candidates[0].content.parts[0]
                if first_part.function_call:
                    # The planner decided to call a tool. We format this as the JSON string
                    # our HRM dispatcher expects.
                    # The input to the tool might be a single value or a dict of args.
                    # We'll pass the whole dict.
                    args = dict(first_part.function_call.args)
                    # A simple heuristic: if there's only one argument, and it's named 'query' or 'input',
                    # just pass that value. Otherwise, pass the whole dict as a JSON string.
                    tool_input = args
                    if len(args) == 1 and ('query' in args or 'input' in args):
                        tool_input = args.get('query') or args.get('input')

                    return json.dumps({
                        "tool": first_part.function_call.name,
                        "input": tool_input
                    })
                else:
                    return response.text
            else:
                # If there's no response, return the text part which might contain safety ratings etc.
                return response.text

        except Exception as e:
            print(f"An error occurred while generating non-streaming response: {e}")
            return f"Sorry, an error occurred: {e}"