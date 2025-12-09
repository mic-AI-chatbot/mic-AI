import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ServerlessFrameworkSimulatorTool(BaseTool):
    """
    A tool that simulates serverless framework integration, allowing for
    defining, deploying, invoking, and removing serverless functions.
    """

    def __init__(self, tool_name: str = "ServerlessFrameworkSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.functions_file = os.path.join(self.data_dir, "serverless_functions.json")
        self.logs_file = os.path.join(self.data_dir, "serverless_invocation_logs.json")
        
        # Function definitions: {function_id: {name: ..., runtime: ..., status: ..., code_snippet: ...}}
        self.function_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.functions_file, default={})
        # Invocation logs: {function_id: [{timestamp: ..., payload: ..., response: ..., latency_ms: ...}]}
        self.invocation_logs: Dict[str, List[Dict[str, Any]]] = self._load_data(self.logs_file, default={})

    @property
    def description(self) -> str:
        return "Simulates serverless framework integration: define, deploy, invoke, and remove functions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_function", "deploy_function", "invoke_function", "remove_function", "get_function_status"]},
                "function_id": {"type": "string"},
                "name": {"type": "string"},
                "runtime": {"type": "string", "enum": ["nodejs", "python", "java", "go"]},
                "code_snippet": {"type": "string", "description": "Simulated code for the function."},
                "payload": {"type": "object", "description": "Payload to send when invoking the function."}
            },
            "required": ["operation", "function_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_functions(self):
        with open(self.functions_file, 'w') as f: json.dump(self.function_definitions, f, indent=2)

    def _save_logs(self):
        with open(self.logs_file, 'w') as f: json.dump(self.invocation_logs, f, indent=2)

    def define_function(self, function_id: str, name: str, runtime: str, code_snippet: str) -> Dict[str, Any]:
        """Defines a new serverless function."""
        if function_id in self.function_definitions: raise ValueError(f"Function '{function_id}' already exists.")
        
        new_function = {
            "id": function_id, "name": name, "runtime": runtime, "code_snippet": code_snippet,
            "status": "defined", "created_at": datetime.now().isoformat()
        }
        self.function_definitions[function_id] = new_function
        self._save_functions()
        return new_function

    def deploy_function(self, function_id: str) -> Dict[str, Any]:
        """Simulates deploying a serverless function."""
        function = self.function_definitions.get(function_id)
        if not function: raise ValueError(f"Function '{function_id}' not found. Define it first.")
        
        function["status"] = "deployed"
        function["deployed_at"] = datetime.now().isoformat()
        self._save_functions()
        return {"status": "success", "message": f"Function '{function_id}' deployed."}

    def invoke_function(self, function_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates invoking a serverless function."""
        function = self.function_definitions.get(function_id)
        if not function: raise ValueError(f"Function '{function_id}' not found.")
        if function["status"] != "deployed": raise ValueError(f"Function '{function_id}' is not deployed. Status: {function['status']}.")
        
        simulated_response = {"message": f"Function '{function_id}' executed successfully with payload: {payload}"}
        simulated_latency_ms = random.randint(50, 500)  # nosec B311
        
        log_entry = {
            "timestamp": datetime.now().isoformat(), "payload": payload,
            "response": simulated_response, "latency_ms": simulated_latency_ms
        }
        self.invocation_logs.setdefault(function_id, []).append(log_entry)
        self._save_logs()
        return {"status": "success", "response": simulated_response, "latency_ms": simulated_latency_ms}

    def remove_function(self, function_id: str) -> Dict[str, Any]:
        """Simulates removing a serverless function."""
        function = self.function_definitions.get(function_id)
        if not function: raise ValueError(f"Function '{function_id}' not found.")
        
        function["status"] = "removed"
        function["removed_at"] = datetime.now().isoformat()
        self._save_functions()
        return {"status": "success", "message": f"Function '{function_id}' removed."}

    def get_function_status(self, function_id: str) -> Dict[str, Any]:
        """Retrieves the current status of a serverless function."""
        function = self.function_definitions.get(function_id)
        if not function: raise ValueError(f"Function '{function_id}' not found.")
        return function

    def execute(self, operation: str, function_id: str, **kwargs: Any) -> Any:
        if operation == "define_function":
            name = kwargs.get('name')
            runtime = kwargs.get('runtime')
            code_snippet = kwargs.get('code_snippet')
            if not all([name, runtime, code_snippet]):
                raise ValueError("Missing 'name', 'runtime', or 'code_snippet' for 'define_function' operation.")
            return self.define_function(function_id, name, runtime, code_snippet)
        elif operation == "deploy_function":
            # No additional kwargs required for deploy_function
            return self.deploy_function(function_id)
        elif operation == "invoke_function":
            payload = kwargs.get('payload')
            if not payload:
                raise ValueError("Missing 'payload' for 'invoke_function' operation.")
            return self.invoke_function(function_id, payload)
        elif operation == "remove_function":
            # No additional kwargs required for remove_function
            return self.remove_function(function_id)
        elif operation == "get_function_status":
            # No additional kwargs required for get_function_status
            return self.get_function_status(function_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ServerlessFrameworkSimulatorTool functionality...")
    temp_dir = "temp_serverless_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    serverless_tool = ServerlessFrameworkSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a function
        print("\n--- Defining function 'hello_world_python' ---")
        serverless_tool.execute(operation="define_function", function_id="hello_world_python", name="HelloWorld", runtime="python", code_snippet="def handler(event, context): return {'statusCode': 200, 'body': 'Hello from Python!'}")
        print("Function defined.")

        # 2. Deploy the function
        print("\n--- Deploying function 'hello_world_python' ---")
        serverless_tool.execute(operation="deploy_function", function_id="hello_world_python")
        print("Function deployed.")

        # 3. Invoke the function
        print("\n--- Invoking function 'hello_world_python' ---")
        invocation_result = serverless_tool.execute(operation="invoke_function", function_id="hello_world_python", payload={"name": "Alice"})
        print(json.dumps(invocation_result, indent=2))

        # 4. Get function status
        print("\n--- Getting status for 'hello_world_python' ---")
        status = serverless_tool.execute(operation="get_function_status", function_id="hello_world_python")
        print(json.dumps(status, indent=2))

        # 5. Remove the function
        print("\n--- Removing function 'hello_world_python' ---")
        serverless_tool.execute(operation="remove_function", function_id="hello_world_python")
        print("Function removed.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")