import logging
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for the assistant's configuration
assistant_commands: Dict[str, Dict[str, Any]] = {}

class VirtualPersonalAssistantBuilderTool(BaseTool):
    """
    A tool to simulate building a virtual personal assistant by defining its commands.
    """
    def __init__(self, tool_name: str = "virtual_personal_assistant_builder_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates building a personal assistant: define commands, list them, and simulate their execution."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'define_command', 'list_commands', 'run_command'."
                },
                "command_name": {"type": "string", "description": "The name of the command to define or run."},
                "command_description": {"type": "string", "description": "A description of what the command does."},
                "target_tool": {"type": "string", "description": "The name of the tool to call for this command (e.g., 'EmailSendingTool')."},
                "target_tool_params": {"type": "object", "description": "A dictionary of parameters to pass to the target tool."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            actions = {
                "define_command": self._define_command,
                "list_commands": self._list_commands,
                "run_command": self._run_command,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VirtualPersonalAssistantBuilderTool: {e}")
            return {"error": str(e)}

    def _define_command(self, command_name: str, command_description: str, target_tool: str, target_tool_params: Dict = None, **kwargs) -> Dict:
        if not all([command_name, command_description, target_tool]):
            raise ValueError("'command_name', 'command_description', and 'target_tool' are required.")
        
        if command_name in assistant_commands:
            raise ValueError(f"Command '{command_name}' already exists.")
        
        assistant_commands[command_name] = {
            "description": command_description,
            "target_tool": target_tool,
            "target_tool_params": target_tool_params or {}
        }
        logger.info(f"Command '{command_name}' defined successfully.")
        return {"message": "Command defined successfully.", "command": {command_name: assistant_commands[command_name]}}

    def _list_commands(self, **kwargs) -> Dict:
        if not assistant_commands:
            return {"message": "No commands have been defined for the assistant yet."}
        return {"defined_commands": assistant_commands}

    def _run_command(self, command_name: str, **kwargs) -> Dict:
        if not command_name:
            raise ValueError("'command_name' is required to run a command.")
        
        command = assistant_commands.get(command_name)
        if not command:
            raise ValueError(f"Command '{command_name}' is not defined.")
            
        logger.info(f"Simulating execution of command '{command_name}'.")
        
        # This is a simulation. A real implementation would use the ToolManager to dispatch the call.
        return {
            "message": "Command execution simulated successfully.",
            "simulation_details": {
                "would_call_tool": command["target_tool"],
                "with_parameters": command["target_tool_params"]
            }
        }