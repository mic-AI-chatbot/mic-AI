import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SmartHomeSimulatorTool(BaseTool):
    """
    A tool that simulates smart home automation, allowing for adding devices,
    controlling them, creating and activating scenes, and getting device status.
    """

    def __init__(self, tool_name: str = "SmartHomeSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.devices_file = os.path.join(self.data_dir, "smart_home_devices.json")
        self.scenes_file = os.path.join(self.data_dir, "smart_home_scenes.json")
        
        # Devices structure: {device_name: {type: ..., status: ..., brightness: ...}}
        self.devices: Dict[str, Dict[str, Any]] = self._load_data(self.devices_file, default={})
        # Scenes structure: {scene_name: {device_actions: {device_name: {action: ..., value: ...}}}}
        self.scenes: Dict[str, Dict[str, Any]] = self._load_data(self.scenes_file, default={})

    @property
    def description(self) -> str:
        return "Simulates smart home automation: add/control devices, create/activate scenes, get device status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_device", "remove_device", "control_device", "create_scene", "activate_scene", "get_device_status"]},
                "device_name": {"type": "string"},
                "device_type": {"type": "string", "enum": ["light", "thermostat", "door_lock"]},
                "action": {"type": "string", "enum": ["turn_on", "turn_off", "set_brightness", "set_temperature", "lock", "unlock"]},
                "value": {"type": "number", "description": "Value for action (e.g., brightness percentage, temperature)."},
                "scene_name": {"type": "string"},
                "device_actions": {
                    "type": "object",
                    "description": "A dictionary of device actions for a scene (e.g., {'light_1': {'action': 'turn_on'}})."
                }
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_devices(self):
        with open(self.devices_file, 'w') as f: json.dump(self.devices, f, indent=2)

    def _save_scenes(self):
        with open(self.scenes_file, 'w') as f: json.dump(self.scenes, f, indent=2)

    def add_device(self, device_name: str, device_type: str) -> Dict[str, Any]:
        """Adds a new smart home device."""
        if device_name in self.devices: raise ValueError(f"Device '{device_name}' already exists.")
        
        initial_status = "off"
        if device_type == "thermostat": initial_status = "idle"
        
        self.devices[device_name] = {"type": device_type, "status": initial_status, "brightness": 0, "temperature": 22}
        self._save_devices()
        return {"status": "success", "message": f"Device '{device_name}' ({device_type}) added."}

    def remove_device(self, device_name: str) -> Dict[str, Any]:
        """Removes a smart home device."""
        if device_name not in self.devices: raise ValueError(f"Device '{device_name}' not found.")
        
        del self.devices[device_name]
        self._save_devices()
        return {"status": "success", "message": f"Device '{device_name}' removed."}

    def control_device(self, device_name: str, action: str, value: Optional[Union[int, float]] = None) -> Dict[str, Any]:
        """Controls a smart home device."""
        device = self.devices.get(device_name)
        if not device: raise ValueError(f"Device '{device_name}' not found.")
        
        if action == "turn_on": device["status"] = "on"
        elif action == "turn_off": device["status"] = "off"
        elif action == "set_brightness" and device["type"] == "light":
            if value is None or not 0 <= value <= 100: raise ValueError("Brightness value must be between 0 and 100.")
            device["brightness"] = value
        elif action == "set_temperature" and device["type"] == "thermostat":
            if value is None or not 15 <= value <= 30: raise ValueError("Temperature must be between 15 and 30 Celsius.")
            device["temperature"] = value
        elif action == "lock" and device["type"] == "door_lock": device["status"] = "locked"
        elif action == "unlock" and device["type"] == "door_lock": device["status"] = "unlocked"
        else: raise ValueError(f"Invalid action '{action}' for device '{device_name}' or device type.")
        
        self._save_devices()
        return {"status": "success", "message": f"Device '{device_name}' action '{action}' executed."}

    def create_scene(self, scene_name: str, device_actions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Creates a new smart home scene."""
        if scene_name in self.scenes: raise ValueError(f"Scene '{scene_name}' already exists.")
        
        # Validate devices in scene actions
        for dev_name in device_actions.keys():
            if dev_name not in self.devices: raise ValueError(f"Device '{dev_name}' in scene '{scene_name}' not found.")
        
        new_scene = {
            "name": scene_name, "device_actions": device_actions,
            "created_at": datetime.now().isoformat()
        }
        self.scenes[scene_name] = new_scene
        self._save_scenes()
        return new_scene

    def activate_scene(self, scene_name: str) -> Dict[str, Any]:
        """Activates a smart home scene."""
        scene = self.scenes.get(scene_name)
        if not scene: raise ValueError(f"Scene '{scene_name}' not found.")
        
        results = []
        for device_name, actions in scene["device_actions"].items():
            try:
                result = self.control_device(device_name, actions["action"], actions.get("value"))
                results.append({"device": device_name, "status": result["status"]})
            except ValueError as e:
                results.append({"device": device_name, "status": "error", "message": str(e)})
        
        return {"status": "success", "message": f"Scene '{scene_name}' activated.", "device_results": results}

    def get_device_status(self, device_name: str) -> Dict[str, Any]:
        """Retrieves the current status of a smart home device."""
        device = self.devices.get(device_name)
        if not device: raise ValueError(f"Device '{device_name}' not found.")
        return {"status": "success", "device_name": device_name, "current_state": device}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_device":
            device_name = kwargs.get('device_name')
            device_type = kwargs.get('device_type')
            if not all([device_name, device_type]):
                raise ValueError("Missing 'device_name' or 'device_type' for 'add_device' operation.")
            return self.add_device(device_name, device_type)
        elif operation == "remove_device":
            device_name = kwargs.get('device_name')
            if not device_name:
                raise ValueError("Missing 'device_name' for 'remove_device' operation.")
            return self.remove_device(device_name)
        elif operation == "control_device":
            device_name = kwargs.get('device_name')
            action = kwargs.get('action')
            if not all([device_name, action]):
                raise ValueError("Missing 'device_name' or 'action' for 'control_device' operation.")
            return self.control_device(device_name, action, kwargs.get('value'))
        elif operation == "create_scene":
            scene_name = kwargs.get('scene_name')
            device_actions = kwargs.get('device_actions')
            if not all([scene_name, device_actions]):
                raise ValueError("Missing 'scene_name' or 'device_actions' for 'create_scene' operation.")
            return self.create_scene(scene_name, device_actions)
        elif operation == "activate_scene":
            scene_name = kwargs.get('scene_name')
            if not scene_name:
                raise ValueError("Missing 'scene_name' for 'activate_scene' operation.")
            return self.activate_scene(scene_name)
        elif operation == "get_device_status":
            device_name = kwargs.get('device_name')
            if not device_name:
                raise ValueError("Missing 'device_name' for 'get_device_status' operation.")
            return self.get_device_status(device_name)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SmartHomeSimulatorTool functionality...")
    temp_dir = "temp_smart_home_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sm_tool = SmartHomeSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add devices
        print("\n--- Adding devices ---")
        sm_tool.execute(operation="add_device", device_name="living_room_light", device_type="light")
        sm_tool.execute(operation="add_device", device_name="thermostat_main", device_type="thermostat")
        sm_tool.execute(operation="add_device", device_name="front_door_lock", device_type="door_lock")
        print("Devices added.")

        # 2. Create a scene
        print("\n--- Creating scene 'Evening_Mode' ---")
        scene_actions = {
            "living_room_light": {"action": "set_brightness", "value": 50},
            "thermostat_main": {"action": "set_temperature", "value": 20},
            "front_door_lock": {"action": "lock"}
        }
        sm_tool.execute(operation="create_scene", scene_name="Evening_Mode", device_actions=scene_actions)
        print("Scene created.")

        # 3. Activate the scene
        print("\n--- Activating scene 'Evening_Mode' ---")
        activate_result = sm_tool.execute(operation="activate_scene", scene_name="Evening_Mode")
        print(json.dumps(activate_result, indent=2))

        # 4. Control a device directly
        print("\n--- Controlling 'living_room_light' to turn off ---")
        sm_tool.execute(operation="control_device", device_name="living_room_light", action="turn_off")
        print("Light turned off.")

        # 5. Get device status
        print("\n--- Getting status for 'living_room_light' ---")
        status = sm_tool.execute(operation="get_device_status", device_name="living_room_light")
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")