import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated connected devices
connected_devices: Dict[str, Dict[str, Any]] = {}

class WearableTechIntegratorTool(BaseTool):
    """
    A tool to simulate integration with wearable devices for data retrieval and command sending.
    """
    def __init__(self, tool_name: str = "wearable_tech_integrator_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates wearable tech integration: connect, get sensor data, send commands, and list devices."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'connect', 'disconnect', 'get_sensor_data', 'send_command', 'list_devices'."
                },
                "device_id": {"type": "string", "description": "The unique ID of the wearable device."},
                "device_type": {"type": "string", "description": "The type of wearable device (e.g., 'smartwatch', 'fitness_tracker')."},
                "sensor_type": {
                    "type": "string", 
                    "description": "The type of sensor data to retrieve ('heart_rate', 'steps', 'sleep_data')."
                },
                "command_name": {"type": "string", "description": "The command to send to the device (e.g., 'vibrate', 'display_message')."},
                "command_payload": {"type": "string", "description": "Optional payload for the command (e.g., 'Hello World')."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            device_id = kwargs.get("device_id")

            if action in ['connect', 'disconnect', 'get_sensor_data', 'send_command'] and not device_id:
                raise ValueError(f"'device_id' is required for the '{action}' action.")

            actions = {
                "connect": self._connect_device,
                "disconnect": self._disconnect_device,
                "get_sensor_data": self._get_sensor_data,
                "send_command": self._send_command,
                "list_devices": self._list_devices,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WearableTechIntegratorTool: {e}")
            return {"error": str(e)}

    def _connect_device(self, device_id: str, device_type: str, **kwargs) -> Dict:
        if not device_type:
            raise ValueError("'device_type' is required to connect a device.")
        if device_id in connected_devices:
            raise ValueError(f"Device '{device_id}' is already connected.")
        
        new_device = {
            "id": device_id,
            "type": device_type,
            "status": "connected",
            "battery_level": random.randint(50, 100),  # nosec B311
            "last_sync": datetime.now(timezone.utc).isoformat()
        }
        connected_devices[device_id] = new_device
        logger.info(f"Device '{device_id}' connected.")
        return {"message": "Device connected successfully.", "details": new_device}

    def _disconnect_device(self, device_id: str, **kwargs) -> Dict:
        if device_id not in connected_devices:
            raise ValueError(f"Device '{device_id}' not found or not connected.")
            
        del connected_devices[device_id]
        logger.info(f"Device '{device_id}' disconnected.")
        return {"message": "Device disconnected successfully.", "device_id": device_id}

    def _get_sensor_data(self, device_id: str, sensor_type: str, **kwargs) -> Dict:
        if device_id not in connected_devices:
            raise ValueError(f"Device '{device_id}' not connected.")
        if not sensor_type:
            raise ValueError("'sensor_type' is required to get sensor data.")
            
        logger.info(f"Getting '{sensor_type}' data from device '{device_id}'.")
        
        data = {}
        if sensor_type == "heart_rate":
            data = {"value": random.randint(60, 120), "unit": "bpm"}  # nosec B311
        elif sensor_type == "steps":
            data = {"value": random.randint(1000, 10000), "unit": "steps"}  # nosec B311
        elif sensor_type == "sleep_data":
            data = {"deep_sleep_hours": round(random.uniform(1, 4), 1), "light_sleep_hours": round(random.uniform(3, 6), 1)}  # nosec B311
        else:
            raise ValueError(f"Unsupported sensor type: '{sensor_type}'.")
            
        return {"sensor_data": data, "device_id": device_id, "sensor_type": sensor_type}

    def _send_command(self, device_id: str, command_name: str, command_payload: Optional[str] = None, **kwargs) -> Dict:
        if device_id not in connected_devices:
            raise ValueError(f"Device '{device_id}' not connected.")
        if not command_name:
            raise ValueError("'command_name' is required to send a command.")
            
        logger.info(f"Sending command '{command_name}' to device '{device_id}'.")
        return {"message": f"Command '{command_name}' sent to device '{device_id}'.", "command_payload": command_payload}

    def _list_devices(self, **kwargs) -> Dict:
        if not connected_devices:
            return {"message": "No wearable devices are currently connected."}
        return {"connected_devices": list(connected_devices.values())}