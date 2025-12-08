import logging
import json
import random
import re
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Chatbot personality tools will not be fully functional.")

logger = logging.getLogger(__name__)

class ChatbotPersonality:
    """Represents a chatbot's personality profile."""
    def __init__(self, chatbot_id: str, traits: Dict[str, float], role: str, personality_description: str, sample_dialogue: str):
        self.chatbot_id = chatbot_id
        self.traits = traits
        self.role = role
        self.personality_description = personality_description
        self.sample_dialogue = sample_dialogue
        self.creation_date = datetime.now().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chatbot_id": self.chatbot_id,
            "traits": self.traits,
            "role": self.role,
            "personality_description": self.personality_description,
            "sample_dialogue": self.sample_dialogue,
            "creation_date": self.creation_date
        }

class ChatbotManager:
    """Manages all created chatbot personalities, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatbotManager, cls).__new__(cls)
            cls._instance.chatbots: Dict[str, ChatbotPersonality] = {}
        return cls._instance

    def add_chatbot(self, chatbot: ChatbotPersonality):
        self.chatbots[chatbot.chatbot_id] = chatbot

    def get_chatbot(self, chatbot_id: str) -> ChatbotPersonality:
        return self.chatbots.get(chatbot_id)

chatbot_manager = ChatbotManager()

class PersonalityModel:
    """Manages the text generation model for personality tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PersonalityModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for personality generation are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for personality generation...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

personality_model_instance = PersonalityModel()

class GenerateChatbotPersonalityTool(BaseTool):
    """Generates a detailed chatbot personality profile and sample dialogue using an AI model."""
    def __init__(self, tool_name="generate_chatbot_personality"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a new chatbot personality based on specified traits (e.g., friendly, formal) and a defined role, using an AI model to create a detailed profile and sample dialogue."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chatbot_id": {"type": "string", "description": "A unique ID for the chatbot."},
                "traits": {
                    "type": "object",
                    "description": "A dictionary of personality traits and their values (e.g., {'friendly': 0.8, 'formal': 0.2}). Values should be between 0 and 1."
                },
                "role": {"type": "string", "description": "The role of the chatbot (e.g., 'customer support', 'personal assistant', 'sales bot')."}
            },
            "required": ["chatbot_id", "traits", "role"]
        }

    def execute(self, chatbot_id: str, traits: Dict[str, float], role: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})
        if chatbot_id in chatbot_manager.chatbots:
            return json.dumps({"error": f"Chatbot with ID '{chatbot_id}' already exists. Please choose a unique ID."})

        traits_str = ", ".join([f"{k}: {v}" for k, v in traits.items()])
        prompt = f"Generate a detailed personality description and a short sample dialogue for a chatbot with the following traits: {traits_str} and role: {role}. Personality Description and Sample Dialogue:"
        
        generated_text = personality_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        # Attempt to parse description and dialogue
        description_match = re.search(r"Personality Description: (.*?)(Sample Dialogue:|$)", generated_text, re.DOTALL)
        dialogue_match = re.search(r"Sample Dialogue: (.*)", generated_text, re.DOTALL)

        personality_description = description_match.group(1).strip() if description_match else "Could not extract description."
        sample_dialogue = dialogue_match.group(1).strip() if dialogue_match else "Could not extract sample dialogue."

        chatbot = ChatbotPersonality(chatbot_id, traits, role, personality_description, sample_dialogue)
        chatbot_manager.add_chatbot(chatbot)
        
        report = {
            "message": f"Chatbot '{chatbot_id}' personality generated successfully.",
            "chatbot_details": chatbot.to_dict()
        }
        return json.dumps(report, indent=2)

class AnalyzeChatbotPersonalityTool(BaseTool):
    """Analyzes a chatbot's personality based on its defined traits and interaction history using an AI model."""
    def __init__(self, tool_name="analyze_chatbot_personality"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a chatbot's personality based on its defined traits and interaction history, providing insights into its perceived persona using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chatbot_id": {"type": "string", "description": "The ID of the chatbot to analyze."},
                "interaction_history_summary": {"type": "string", "description": "A summary of the chatbot's interaction history (optional)."}
            },
            "required": ["chatbot_id"]
        }

    def execute(self, chatbot_id: str, interaction_history_summary: str = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        chatbot = chatbot_manager.get_chatbot(chatbot_id)
        if not chatbot:
            return json.dumps({"error": f"Chatbot with ID '{chatbot_id}' not found. Please generate its personality first."})
        
        prompt = f"Analyze the perceived persona of a chatbot with the following personality description: '{chatbot.personality_description}' and role: '{chatbot.role}'. Its traits are: {json.dumps(chatbot.traits)}. "
        if interaction_history_summary:
            prompt += f"Consider its interaction history: {interaction_history_summary}. "
        prompt += "Provide insights into its perceived persona and any potential discrepancies. Personality Analysis:"

        generated_analysis = personality_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 300)
        
        report = {
            "chatbot_id": chatbot_id,
            "personality_analysis": generated_analysis
        }
        return json.dumps(report, indent=2)

class SimulateChatbotInteractionTool(BaseTool):
    """Simulates an interaction with a chatbot, generating a response based on its personality."""
    def __init__(self, tool_name="simulate_chatbot_interaction"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates an interaction with a chatbot, generating a response based on its defined personality and a user query."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "chatbot_id": {"type": "string", "description": "The ID of the chatbot to interact with."},
                "user_query": {"type": "string", "description": "The user's query to the chatbot."}
            },
            "required": ["chatbot_id", "user_query"]
        }

    def execute(self, chatbot_id: str, user_query: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        chatbot = chatbot_manager.get_chatbot(chatbot_id)
        if not chatbot:
            return json.dumps({"error": f"Chatbot with ID '{chatbot_id}' not found. Please generate its personality first."})
        
        prompt = f"The following chatbot has the personality: '{chatbot.personality_description}' and role: '{chatbot.role}'. Its traits are: {json.dumps(chatbot.traits)}. User asks: '{user_query}'. Chatbot responds:"
        
        chatbot_response = personality_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 150)
        
        report = {
            "chatbot_id": chatbot_id,
            "user_query": user_query,
            "chatbot_response": chatbot_response
        }
        return json.dumps(report, indent=2)