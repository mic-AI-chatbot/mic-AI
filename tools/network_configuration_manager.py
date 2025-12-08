

import logging
import os
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class NetworkConfigurationManagerSimulatorTool(BaseTool):
    """
    A tool that simulates network configuration management, allowing for applying,
    backing up, and restoring configurations for network devices.
    """

    def __init__(self, tool_name: str = "NetworkConfigManagerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.devices_file = os.path.join(self.data_dir, "network_devices.json")
        # Devices structure: {device_name: {status: "online", config: "..."}}
        self.devices: Dict[str, Dict[str, Any]] = self._load_data(self.devices_file, default={})

    @property
    def description(self) -> str:
        return "Simulates network configuration management: apply, backup, restore configs for devices."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["apply_config", "backup_config", "restore_config", "get_device_status"]},
                "device_name": {"type": "string", "description": "The name of the network device."},
                "config_content": {"type": "string", "description": "The configuration content (for apply/restore operations)."}
            },
            "required": ["operation", "device_name"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.devices_file, 'w') as f: json.dump(self.devices, f, indent=2)

    def _get_device_info(self, device_name: str) -> Dict[str, Any]:
        """Helper to get device info, creating a default if not exists."""
        if device_name not in self.devices:
            self.devices[device_name] = {"status": "online", "config": "empty_config", "last_updated": datetime.now().isoformat()}
            self._save_data()
        return self.devices[device_name]

    def apply_config(self, device_name: str, config_content: str) -> Dict[str, Any]:
        """Applies a new configuration to a network device."""
        device = self._get_device_info(device_name)
        
        # Simulate potential failure
        if random.random() < 0.1:  # nosec B311
            return {"status": "error", "message": f"Simulated: Failed to apply config to '{device_name}' due to network error."}

        device["config"] = config_content
        device["last_updated"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Configuration successfully applied to '{device_name}'."}

    def backup_config(self, device_name: str) -> Dict[str, Any]:
        """Backs up the current configuration of a network device."""
        device = self._get_device_info(device_name)
        if device["status"] == "offline":
            return {"status": "error", "message": f"Device '{device_name}' is offline. Cannot backup configuration."}
        
        return {"status": "success", "device_name": device_name, "backed_up_config": device["config"]}

    def restore_config(self, device_name: str, config_content: str) -> Dict[str, Any]:
        """Restores a configuration to a network device."""
        device = self._get_device_info(device_name)
        
        # Simulate potential failure
        if random.random() < 0.15:  # nosec B311
            return {"status": "error", "message": f"Simulated: Failed to restore config to '{device_name}' due to compatibility issue."}

        device["config"] = config_content
        device["last_updated"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Configuration successfully restored to '{device_name}'."}

    def get_device_status(self, device_name: str) -> Dict[str, Any]:
        """Retrieves the current status and configuration of a network device."""
        device = self.devices.get(device_name)
        if not device:
            return {"status": "error", "message": f"Device '{device_name}' not found."}
        return {"status": "success", "device_name": device_name, "current_status": device["status"], "current_config": device["config"]}

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "apply_config": self.apply_config,
            "backup_config": self.backup_config,
            "restore_config": self.restore_config,
            "get_device_status": self.get_device_status
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating NetworkConfigurationManagerSimulatorTool functionality...")
    temp_dir = "temp_net_config_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    config_manager = NetworkConfigurationManagerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Apply an initial configuration
        print("\n--- Applying initial config to 'router_1' ---")
        initial_config = "interface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0\n no shutdown"
        config_manager.execute(operation="apply_config", device_name="router_1", config_content=initial_config)
        print("Initial config applied.")

        # 2. Get device status
        print("\n--- Getting status for 'router_1' ---")
        status1 = config_manager.execute(operation="get_device_status", device_name="router_1")
        print(json.dumps(status1, indent=2))

        # 3. Backup configuration
        print("\n--- Backing up config for 'router_1' ---")
        backup = config_manager.execute(operation="backup_config", device_name="router_1")
        print(json.dumps(backup, indent=2))

        # 4. Apply a new configuration
        print("\n--- Applying new config to 'router_1' ---")
        new_config = "interface GigabitEthernet0/1\n ip address 10.0.0.1 255.255.255.0\n no shutdown\n access-group 101 in"
        config_manager.execute(operation="apply_config", device_name="router_1", config_content=new_config)
        print("New config applied.")

        # 5. Get device status again to see new config
        print("\n--- Getting status for 'router_1' after new config ---")
        status2 = config_manager.execute(operation="get_device_status", device_name="router_1")
        print(json.dumps(status2, indent=2))

        # 6. Restore the old configuration
        print("\n--- Restoring old config to 'router_1' ---")
        config_manager.execute(operation="restore_config", device_name="router_1", config_content=backup["backed_up_config"])
        print("Old config restored.")

        # 7. Get device status one last time
        print("\n--- Getting status for 'router_1' after restore ---")
        status3 = config_manager.execute(operation="get_device_status", device_name="router_1")
        print(json.dumps(status3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
