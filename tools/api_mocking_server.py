import logging
import json
import uvicorn
from fastapi import FastAPI, Response
from multiprocessing import Process
from typing import Dict, Any
from tools.base_tool import BaseTool

# This tool depends on the 'designed_apis' state and the 'generate_sample_from_schema' function
# from the 'api_design_tool'. For this simulation, we import them directly.
try:
    from .api_design_tool import designed_apis, generate_sample_from_schema
except (ImportError, ModuleNotFoundError):
    designed_apis = {}
    def generate_sample_from_schema(schema: Dict[str, Any]) -> Any:
        return {"error": "Schema generation function not available."}
    logging.warning("Could not import from api_design_tool. Mock server functionality will be limited.")

logger = logging.getLogger(__name__)

class MockServerManager:
    """Manages the state and processes of running mock servers."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockServerManager, cls).__new__(cls)
            cls._instance.servers: Dict[str, Process] = {}
        return cls._instance

    def start_server(self, server_name: str, app: FastAPI, port: int) -> bool:
        if server_name in self.servers and self.servers[server_name].is_alive():
            return False
        
        # Using a daemon process allows the main program to exit even if the mock server is running
        process = Process(target=uvicorn.run, args=(app,), kwargs={"host": "127.0.0.1", "port": port, "log_level": "warning"}, daemon=True)
        process.start()
        self.servers[server_name] = process
        return True

    def stop_server(self, server_name: str) -> bool:
        if server_name in self.servers and self.servers[server_name].is_alive():
            self.servers[server_name].terminate()
            self.servers[server_name].join(timeout=5)
            del self.servers[server_name]
            return True
        return False

mock_server_manager = MockServerManager()

def create_fastapi_app_from_spec(spec: Dict[str, Any]) -> FastAPI:
    """Dynamically creates a FastAPI application from an OpenAPI specification."""
    app = FastAPI(title=spec.get("info", {}).get("title", "Mock API"))

    for path, path_item in spec.get("paths", {}).items():
        for method, endpoint_spec in path_item.items():
            
            # Use a closure to capture the response schema for each endpoint
            def create_endpoint_func(response_schema):
                def endpoint_func():
                    mock_response = generate_sample_from_schema(response_schema)
                    return Response(content=json.dumps(mock_response, indent=2), media_type="application/json")
                return endpoint_func

            response_schema = endpoint_spec.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema", {})
            
            app.add_api_route(
                path,
                create_endpoint_func(response_schema),
                methods=[method.upper()],
                summary=endpoint_spec.get("summary", "Mocked endpoint")
            )
    return app

class StartMockServerTool(BaseTool):
    """Starts a live API mocking server based on an API design."""
    def __init__(self, tool_name="start_mock_server"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Starts a live API mocking server in a background process based on an API design from the API Design tool."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server_name": {"type": "string", "description": "A unique name for the mock server."},
                "api_id": {"type": "string", "description": "The ID of the API design to mock."},
                "port": {"type": "integer", "description": "The port number for the server.", "default": 8080}
            },
            "required": ["server_name", "api_id"]
        }

    def execute(self, server_name: str, api_id: str, port: int = 8080, **kwargs: Any) -> str:
        if not designed_apis:
            return json.dumps({"error": "No API designs are available. Please define an API first."})
        if api_id not in designed_apis:
            return json.dumps({"error": f"API design with ID '{api_id}' not found."})

        api_spec = designed_apis[api_id]
        app = create_fastapi_app_from_spec(api_spec)
        
        if mock_server_manager.start_server(server_name, app, port):
            report = {
                "message": f"Mock server '{server_name}' starting in the background.",
                "url": f"http://127.0.0.1:{port}"
            }
        else:
            report = {"error": f"A mock server with the name '{server_name}' is already running."}
            
        return json.dumps(report, indent=2)

class StopMockServerTool(BaseTool):
    """Stops a running API mocking server."""
    def __init__(self, tool_name="stop_mock_server"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Stops a running API mocking server process."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"server_name": {"type": "string", "description": "The name of the mock server to stop."}},
            "required": ["server_name"]
        }

    def execute(self, server_name: str, **kwargs: Any) -> str:
        if mock_server_manager.stop_server(server_name):
            report = {"message": f"Mock server '{server_name}' stopped successfully."}
        else:
            report = {"error": f"Mock server '{server_name}' not found or not running."}
            
        return json.dumps(report, indent=2)