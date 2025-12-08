import logging
import json
import random
import string
from typing import Dict, Any
from tools.base_tool import BaseTool

# This tool depends on the 'designed_apis' state from the 'api_design_tool'.
# In a real application, this state would be managed via a shared database or service.
# For this simulation, we will import it directly to demonstrate inter-tool functionality.
try:
    from .api_design_tool import designed_apis
except (ImportError, ModuleNotFoundError):
    designed_apis = {}
    logging.warning("Could not import 'designed_apis' from api_design_tool. API creation will be limited.")

logger = logging.getLogger(__name__)

class APIGatewayManager:
    """Manages the state of a simulated API Gateway, including APIs, stages, and keys."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APIGatewayManager, cls).__new__(cls)
            cls._instance.apis: Dict[str, Any] = {}
            cls._instance.api_keys: Dict[str, Any] = {}
        return cls._instance

    def create_api(self, api_id: str, api_spec: Dict[str, Any]) -> bool:
        if api_id in self.apis:
            return False
        
        self.apis[api_id] = {
            "spec": api_spec,
            "stages": {},
            "rate_limiting": {"burst_limit": 200, "rate_limit": 100}, # Default limits
            "usage_plans": {}
        }
        return True

    def deploy_api(self, api_id: str, stage_name: str) -> bool:
        if api_id not in self.apis:
            return False
        
        self.apis[api_id]["stages"][stage_name] = {
            "deployment_id": f"dep_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}",  # nosec B311
            "invoke_url": f"https://{api_id}.execute-api.us-east-1.amazonaws.com/{stage_name}"
        }
        return True

    def configure_rate_limiting(self, api_id: str, burst_limit: int, rate_limit: int) -> bool:
        if api_id not in self.apis:
            return False
        
        self.apis[api_id]["rate_limiting"] = {"burst_limit": burst_limit, "rate_limit": rate_limit}
        return True

    def create_api_key(self, api_id: str, key_name: str) -> str:
        if api_id not in self.apis:
            return None
            
        api_key = f"key_{''.join(random.choices(string.ascii_letters + string.digits, k=32))}"  # nosec B311
        self.api_keys[key_name] = {
            "api_id": api_id,
            "key": api_key,
            "enabled": True
        }
        return api_key

gateway_manager = APIGatewayManager()

class ImportAndCreateAPITool(BaseTool):
    """Imports an API design and creates it on the simulated API Gateway."""
    def __init__(self, tool_name="import_and_create_api"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Imports an API design from the API Design tool and creates it on the simulated API Gateway."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"api_id": {"type": "string", "description": "The ID of the API design to import."}},
            "required": ["api_id"]
        }

    def execute(self, api_id: str, **kwargs: Any) -> str:
        if not designed_apis:
            return json.dumps({"error": "No API designs are available to import. Please define an API first."})
        if api_id not in designed_apis:
            return json.dumps({"error": f"API design with ID '{api_id}' not found."})
        
        if gateway_manager.create_api(api_id, designed_apis[api_id]):
            report = {"message": f"API '{api_id}' created successfully on the gateway from its design."}
        else:
            report = {"error": f"API with ID '{api_id}' already exists on the gateway."}
            
        return json.dumps(report, indent=2)

class DeployAPITool(BaseTool):
    """Deploys an API to a specified stage."""
    def __init__(self, tool_name="deploy_api"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deploys a managed API to a new or existing stage (e.g., 'dev', 'prod') and returns its invoke URL."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_id": {"type": "string", "description": "The ID of the API to deploy."},
                "stage_name": {"type": "string", "description": "The name of the stage to deploy to (e.g., 'dev', 'prod')."}
            },
            "required": ["api_id", "stage_name"]
        }

    def execute(self, api_id: str, stage_name: str, **kwargs: Any) -> str:
        if gateway_manager.deploy_api(api_id, stage_name):
            stage_info = gateway_manager.apis[api_id]["stages"][stage_name]
            report = {
                "message": f"API '{api_id}' successfully deployed to stage '{stage_name}'.",
                "invoke_url": stage_info["invoke_url"]
            }
        else:
            report = {"error": f"API with ID '{api_id}' not found on the gateway."}
            
        return json.dumps(report, indent=2)

class ConfigureRateLimitingTool(BaseTool):
    """Configures rate limiting for an API."""
    def __init__(self, tool_name="configure_rate_limiting"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Configures the rate limiting (requests per second) and burst capacity for a given API."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_id": {"type": "string", "description": "The ID of the API to configure."},
                "rate_limit": {"type": "integer", "description": "The steady-state rate limit in requests per second."},
                "burst_limit": {"type": "integer", "description": "The burst capacity (the maximum number of concurrent requests)."}
            },
            "required": ["api_id", "rate_limit", "burst_limit"]
        }

    def execute(self, api_id: str, rate_limit: int, burst_limit: int, **kwargs: Any) -> str:
        if gateway_manager.configure_rate_limiting(api_id, burst_limit, rate_limit):
            report = {"message": f"Rate limiting for API '{api_id}' updated successfully."}
        else:
            report = {"error": f"API with ID '{api_id}' not found."}
            
        return json.dumps(report, indent=2)

class CreateAPIKeyTool(BaseTool):
    """Creates an API key for a given API."""
    def __init__(self, tool_name="create_api_key"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new API key for a specified API to track and control access."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_id": {"type": "string", "description": "The ID of the API to associate the key with."},
                "key_name": {"type": "string", "description": "A descriptive name for the key (e.g., 'partner_x_key')."}
            },
            "required": ["api_id", "key_name"]
        }

    def execute(self, api_id: str, key_name: str, **kwargs: Any) -> str:
        api_key = gateway_manager.create_api_key(api_id, key_name)
        if api_key:
            report = {
                "message": f"API key '{key_name}' created successfully for API '{api_id}'.",
                "api_key": api_key
            }
        else:
            report = {"error": f"API with ID '{api_id}' not found."}
            
        return json.dumps(report, indent=2)