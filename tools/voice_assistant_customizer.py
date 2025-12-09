import logging
import random
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated voice assistants
voice_assistants: Dict[str, Dict[str, Any]] = {}

class VoiceAssistantCustomizerTool(BaseTool):
    """
    A tool to simulate customizing and managing virtual voice assistants.
    """
    def __init__(self, tool_name: str = "voice_assistant_customizer_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates customizing voice assistants: create, customize voice/commands, and test."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'create_assistant', 'customize_voice', 'add_command', 'set_response', 'test_assistant', 'list_assistants'."
                },
                "assistant_name": {"type": "string", "description": "The unique name of the voice assistant."},
                "voice_type": {
                    "type": "string", 
                    "description": "The type of voice (e.g., 'male_british', 'female_american')."
                },
                "command_phrase": {"type": "string", "description": "The phrase that triggers a command."},
                "response_text": {"type": "string", "description": "The response text for a command."},
                "test_phrase": {"type": "string", "description": "The phrase to test the assistant with."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            assistant_name = kwargs.get("assistant_name")

            if action != 'list_assistants' and not assistant_name:
                raise ValueError(f"'assistant_name' is required for the '{action}' action.")

            actions = {
                "create_assistant": self._create_assistant,
                "customize_voice": self._customize_voice,
                "add_command": self._add_command,
                "set_response": self._set_response,
                "test_assistant": self._test_assistant,
                "list_assistants": self._list_assistants,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VoiceAssistantCustomizerTool: {e}")
            return {"error": str(e)}

    def _create_assistant(self, assistant_name: str, **kwargs) -> Dict:
        if assistant_name in voice_assistants:
            raise ValueError(f"Voice Assistant '{assistant_name}' already exists.")
        
        new_assistant = {
            "name": assistant_name,
            "voice": "default_female",
            "commands": {},
            "responses": {}
        }
        voice_assistants[assistant_name] = new_assistant
        logger.info(f"Voice Assistant '{assistant_name}' created.")
        return {"message": "Assistant created successfully.", "details": new_assistant}

    def _customize_voice(self, assistant_name: str, voice_type: str, **kwargs) -> Dict:
        if assistant_name not in voice_assistants:
            raise ValueError(f"Assistant '{assistant_name}' not found.")
        if not voice_type:
            raise ValueError("'voice_type' is required for voice customization.")
            
        voice_assistants[assistant_name]["voice"] = voice_type
        logger.info(f"Voice for '{assistant_name}' set to '{voice_type}'.")
        return {"message": "Voice customized successfully.", "assistant": assistant_name, "new_voice": voice_type}

    def _add_command(self, assistant_name: str, command_phrase: str, **kwargs) -> Dict:
        if assistant_name not in voice_assistants:
            raise ValueError(f"Assistant '{assistant_name}' not found.")
        if not command_phrase:
            raise ValueError("'command_phrase' is required to add a command.")
            
        if command_phrase in voice_assistants[assistant_name]["commands"]:
            return {"message": f"Command '{command_phrase}' already exists for '{assistant_name}'."}

        voice_assistants[assistant_name]["commands"][command_phrase] = {"action": "unspecified"}
        logger.info(f"Command '{command_phrase}' added to '{assistant_name}'.")
        return {"message": "Command added successfully.", "assistant": assistant_name, "command": command_phrase}

    def _set_response(self, assistant_name: str, command_phrase: str, response_text: str, **kwargs) -> Dict:
        if assistant_name not in voice_assistants:
            raise ValueError(f"Assistant '{assistant_name}' not found.")
        if not command_phrase or not response_text:
            raise ValueError("'command_phrase' and 'response_text' are required to set a response.")
            
        if command_phrase not in voice_assistants[assistant_name]["commands"]:
            raise ValueError(f"Command '{command_phrase}' not defined for '{assistant_name}'. Add it first.")

        voice_assistants[assistant_name]["responses"][command_phrase] = response_text
        logger.info(f"Response for command '{command_phrase}' set for '{assistant_name}'.")
        return {"message": "Response set successfully.", "assistant": assistant_name, "command": command_phrase, "response": response_text}

    def _test_assistant(self, assistant_name: str, test_phrase: str, **kwargs) -> Dict:
        if assistant_name not in voice_assistants:
            raise ValueError(f"Assistant '{assistant_name}' not found.")
        if not test_phrase:
            raise ValueError("'test_phrase' is required to test the assistant.")
            
        assistant = voice_assistants[assistant_name]
        
        # Simple matching for simulation
        if test_phrase in assistant["commands"]:
            response = assistant["responses"].get(test_phrase, f"Okay, I heard '{test_phrase}'. (Default response)")
            return {"message": "Assistant recognized command.", "assistant_response": response}
        else:
            return {"message": "Assistant did not recognize command.", "assistant_response": "I'm sorry, I don't understand that command."}

    def _list_assistants(self, **kwargs) -> Dict:
        if not voice_assistants:
            return {"message": "No voice assistants have been created yet."}
        
        summary = {
            name: {
                "voice": details["voice"],
                "num_commands": len(details["commands"])
            } for name, details in voice_assistants.items()
        }
        return {"voice_assistants": summary}