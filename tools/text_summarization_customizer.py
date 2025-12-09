import random
from tools.base_tool import BaseTool
from typing import Dict, Any
import json # Import json for printing results in main block

class TextSummarizationCustomizer(BaseTool):
    def __init__(self, tool_name):
        super().__init__('text_summarization_customizer')
        self.summarization_profiles: Dict[str, Dict[str, Any]] = {}
        self.logger.info("TextSummarizationCustomizer initialized.")
        # Add a default profile
        self.summarization_profiles["default"] = {
            "length": "medium",
            "style": "extractive",
            "status": "active"
        }

    def create_profile(self, profile_name: str, length_preference: str, style: str) -> str:
        self.logger.info(f"Attempting to create summarization profile: {profile_name}")
        if profile_name in self.summarization_profiles:
            self.logger.warning(f"Summarization profile '{profile_name}' already exists.")
            return f"Error: Summarization profile '{profile_name}' already exists."
        
        if length_preference.lower() not in ["short", "medium", "long"]:
            self.logger.error("Invalid length preference. Must be 'short', 'medium', or 'long'.")
            return "Error: Invalid length preference. Must be 'short', 'medium', or 'long'."
        
        if style.lower() not in ["extractive", "abstractive"]:
            self.logger.error("Invalid style. Must be 'extractive' or 'abstractive'.")
            return "Error: Invalid style. Must be 'extractive' or 'abstractive'."
        
        self.summarization_profiles[profile_name] = {
            "length": length_preference,
            "style": style,
            "status": "active"
        }
        self.logger.info(f"Summarization profile '{profile_name}' created successfully.")
        return f"Summarization profile '{profile_name}' created successfully (Length: {length_preference}, Style: {style})."

    def summarize_text(self, text: str, profile_name: str = "default") -> str:
        self.logger.info(f"Attempting to summarize text using profile: {profile_name}")
        if profile_name not in self.summarization_profiles:
            self.logger.error(f"Summarization profile '{profile_name}' not found.")
            return f"Error: Summarization profile '{profile_name}' not found. Create it first."
        
        profile = self.summarization_profiles[profile_name]
        
        # Simulate summarization based on profile
        original_length = len(text.split())
        if profile["length"] == "short":
            summary_length = int(original_length * 0.2)
        elif profile["length"] == "medium":
            summary_length = int(original_length * 0.4)
        else: # long
            summary_length = int(original_length * 0.6)
        
        simulated_summary = " ".join(text.split()[:summary_length]) + "... (Simulated Summary)"
        self.logger.info(f"Text summarized using profile '{profile_name}'.")
        return f"Text Summarization Customizer: Summarized text using profile '{profile_name}'.\nOriginal Length: {original_length} words.\nSummary Length: {summary_length} words.\nSummary: '{simulated_summary}'"

    def get_profile_status(self, profile_name: str) -> str:
        self.logger.info(f"Attempting to get profile status for: {profile_name}")
        if profile_name not in self.summarization_profiles:
            self.logger.error(f"Summarization profile '{profile_name}' not found.")
            return f"Error: Summarization profile '{profile_name}' not found."
        
        profile_info = self.summarization_profiles[profile_name]
        status_message = (
            f"Summarization Profile '{profile_name}' Status: {profile_info['status'].capitalize()}, "
            f"Length: {profile_info['length']}, Style: {profile_info['style']}."
        )
        self.logger.info(f"Profile status retrieved for '{profile_name}'.")
        return status_message

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_profile", "summarize_text", "get_profile_status"]},
                "profile_name": {"type": "string"},
                "length_preference": {"type": "string", "enum": ["short", "medium", "long"]},
                "style": {"type": "string", "enum": ["extractive", "abstractive"]},
                "text": {"type": "string", "description": "The text to summarize."}
            },
            "required": ["operation"]
        }

    def execute(self, operation: str, **kwargs: Dict[str, Any]) -> str:
        if operation == "create_profile":
            profile_name = kwargs.get('profile_name')
            length_preference = kwargs.get('length_preference')
            style = kwargs.get('style')
            if not all([profile_name, length_preference, style]):
                raise ValueError("Missing 'profile_name', 'length_preference', or 'style' for 'create_profile' operation.")
            return self.create_profile(profile_name, length_preference, style)
        elif operation == "summarize_text":
            text = kwargs.get('text')
            profile_name = kwargs.get('profile_name', 'default')
            if not text:
                raise ValueError("Missing 'text' for 'summarize_text' operation.")
            return self.summarize_text(text, profile_name)
        elif operation == "get_profile_status":
            profile_name = kwargs.get('profile_name')
            if not profile_name:
                raise ValueError("Missing 'profile_name' for 'get_profile_status' operation.")
            return self.get_profile_status(profile_name)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating TextSummarizationCustomizer functionality...")
    
    summarizer_customizer = TextSummarizationCustomizer()
    
    sample_text = "This is a very long sentence that needs to be summarized. It contains many words and ideas. We want to make it shorter and more concise."

    try:
        # 1. Create a summarization profile
        print("\n--- Creating summarization profile 'short_extractive' ---")
        print(summarizer_customizer.execute(operation="create_profile", profile_name="short_extractive", length_preference="short", style="extractive"))

        # 2. Summarize text using the new profile
        print("\n--- Summarizing text using 'short_extractive' profile ---")
        print(summarizer_customizer.execute(operation="summarize_text", text=sample_text, profile_name="short_extractive"))

        # 3. Get profile status
        print("\n--- Getting status for 'short_extractive' profile ---")
        print(summarizer_customizer.execute(operation="get_profile_status", profile_name="short_extractive"))

        # 4. Summarize text using default profile
        print("\n--- Summarizing text using default profile ---")
        print(summarizer_customizer.execute(operation="summarize_text", text=sample_text))

    except Exception as e:
        print(f"\nAn error occurred: {e}")