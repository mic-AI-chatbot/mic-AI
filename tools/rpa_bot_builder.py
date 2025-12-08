import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RPABotDebuggerTool(BaseTool):
    """
    A tool that simulates debugging and troubleshooting for RPA bots,
    allowing for defining bots, simulating debug runs with injected errors,
    and generating debug reports.
    """

    def __init__(self, tool_name: str = "RPABotDebugger", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.bots_file = os.path.join(self.data_dir, "rpa_bot_definitions.json")
        self.debug_logs_file = os.path.join(self.data_dir, "rpa_debug_logs.json")
        
        # Bot definitions: {bot_id: {name: ..., actions: []}}
        self.bot_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.bots_file, default={})
        # Debug logs: {log_id: {bot_id: ..., execution_path: [], error_type: ..., suggested_fix: ...}}
        self.debug_logs: Dict[str, Dict[str, Any]] = self._load_data(self.debug_logs_file, default={})

    @property
    def description(self) -> str:
        return "Simulates RPA bot debugging: define bots, simulate debug runs with errors, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_bot", "simulate_debug_run", "get_debug_report"]},
                "bot_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "actions": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"type": {"type": "string"}, "details": {"type": "string"}}},
                    "description": "List of actions for the bot (e.g., [{'type': 'open_app', 'details': 'Excel'}])."
                },
                "log_id": {"type": "string", "description": "ID of the debug log to retrieve."}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_bots(self):
        with open(self.bots_file, 'w') as f: json.dump(self.bot_definitions, f, indent=2)

    def _save_logs(self):
        with open(self.debug_logs_file, 'w') as f: json.dump(self.debug_logs, f, indent=2)

    def define_bot(self, bot_id: str, name: str, description: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Defines a new RPA bot."""
        if bot_id in self.bot_definitions: raise ValueError(f"Bot '{bot_id}' already exists.")
        
        new_bot = {
            "id": bot_id, "name": name, "description": description, "actions": actions,
            "defined_at": datetime.now().isoformat()
        }
        self.bot_definitions[bot_id] = new_bot
        self._save_bots()
        return new_bot

    def simulate_debug_run(self, bot_id: str) -> Dict[str, Any]:
        """Simulates a debug run of a bot, injecting a random error."""
        bot = self.bot_definitions.get(bot_id)
        if not bot: raise ValueError(f"Bot '{bot_id}' not found. Define it first.")
        
        log_id = f"debug_log_{bot_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        execution_path = []
        error_type = "No error"
        suggested_fix = "Bot completed successfully."
        
        # Inject error at a random step
        error_step_index = random.randint(0, len(bot["actions"]) - 1)  # nosec B311
        
        for i, action in enumerate(bot["actions"]):
            execution_path.append({"step": i + 1, "action": action})
            
            if i == error_step_index:
                error_type = random.choice(["ElementNotFound", "TimeoutError", "DataMismatchError", "ApplicationCrash"])  # nosec B311
                suggested_fix = f"Check action {i+1} ('{action['type']}: {action['details']}') for '{error_type}'."
                execution_path.append({"step": i + 1, "error": error_type, "message": suggested_fix})
                break # Stop execution after error
        
        debug_log = {
            "id": log_id, "bot_id": bot_id, "execution_path": execution_path,
            "error_type": error_type, "suggested_fix": suggested_fix,
            "simulated_at": datetime.now().isoformat()
        }
        self.debug_logs[log_id] = debug_log
        self._save_logs()
        return debug_log

    def get_debug_report(self, log_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated debug report."""
        log = self.debug_logs.get(log_id)
        if not log: raise ValueError(f"Debug log '{log_id}' not found.")
        return log

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_bot":
            bot_id = kwargs.get('bot_id')
            name = kwargs.get('name')
            description = kwargs.get('description')
            actions = kwargs.get('actions')
            if not all([bot_id, name, description, actions]):
                raise ValueError("Missing 'bot_id', 'name', 'description', or 'actions' for 'define_bot' operation.")
            return self.define_bot(bot_id, name, description, actions)
        elif operation == "simulate_debug_run":
            bot_id = kwargs.get('bot_id')
            if not bot_id:
                raise ValueError("Missing 'bot_id' for 'simulate_debug_run' operation.")
            return self.simulate_debug_run(bot_id)
        elif operation == "get_debug_report":
            log_id = kwargs.get('log_id')
            if not log_id:
                raise ValueError("Missing 'log_id' for 'get_debug_report' operation.")
            return self.get_debug_report(log_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RPABotDebuggerTool functionality...")
    temp_dir = "temp_rpa_debug_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    rpa_debugger = RPABotDebuggerTool(data_dir=temp_dir)
    
    try:
        # 1. Define a bot
        print("\n--- Defining bot 'data_extractor_bot' ---")
        actions = [
            {"type": "open_browser", "details": "https://example.com"},
            {"type": "navigate_to", "details": "/data_page"},
            {"type": "click_element", "details": "download_button"},
            {"type": "wait_for_download", "details": "report.csv"},
            {"type": "close_browser", "details": ""}
        ]
        rpa_debugger.execute(operation="define_bot", bot_id="data_extractor_bot", name="Data Extractor", description="Extracts data from a website.", actions=actions)
        print("Bot defined.")

        # 2. Simulate a debug run
        print("\n--- Simulating debug run for 'data_extractor_bot' ---")
        debug_report = rpa_debugger.execute(operation="simulate_debug_run", bot_id="data_extractor_bot")
        print(json.dumps(debug_report, indent=2))

        # 3. Get the debug report
        print(f"\n--- Getting debug report for '{debug_report['id']}' ---")
        retrieved_report = rpa_debugger.execute(operation="get_debug_report", bot_id="any", log_id=debug_report["id"]) # bot_id is not used for get_debug_report
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")