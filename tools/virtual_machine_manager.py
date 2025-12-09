import logging
import random
import time
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated virtual machines
virtual_machines: Dict[str, Dict[str, Any]] = {}

class VirtualMachineManagerTool(BaseTool):
    """
    A tool to simulate the management of virtual machines (VMs).
    """
    def __init__(self, tool_name: str = "virtual_machine_manager_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates a VM manager: create, start, stop, and get status of virtual machines."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'create', 'start', 'stop', 'status', 'list_all'."
                },
                "vm_name": {"type": "string", "description": "The unique name for the VM."},
                "image": {
                    "type": "string", 
                    "description": "The OS image to use for creation (e.g., 'ubuntu-22.04', 'windows-server-2022').",
                    "default": "ubuntu-22.04"
                },
                "flavor": {
                    "type": "string",
                    "description": "The size of the VM (e.g., 'small', 'medium', 'large').",
                    "default": "small"
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            vm_name = kwargs.get("vm_name")

            if action in ['create', 'start', 'stop', 'status'] and not vm_name:
                raise ValueError(f"'vm_name' is required for the '{action}' action.")

            actions = {
                "create": self._create_vm,
                "start": self._start_vm,
                "stop": self._stop_vm,
                "status": self._get_vm_status,
                "list_all": self._list_vms,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VirtualMachineManagerTool: {e}")
            return {"error": str(e)}

    def _create_vm(self, vm_name: str, image: str, flavor: str, **kwargs) -> Dict:
        if vm_name in virtual_machines:
            raise ValueError(f"A VM with the name '{vm_name}' already exists.")

        logger.info(f"Creating VM '{vm_name}' with image '{image}'.")
        
        flavors = {
            "small": {"vcpus": 2, "ram_gb": 4},
            "medium": {"vcpus": 4, "ram_gb": 16},
            "large": {"vcpus": 8, "ram_gb": 32}
        }
        
        new_vm = {
            "name": vm_name,
            "image": image,
            "flavor": flavors.get(flavor, flavors["small"]),
            "status": "stopped",
            "ip_address": None,
            "created_at": time.time()
        }
        virtual_machines[vm_name] = new_vm
        
        return {"message": "VM created successfully.", "details": new_vm}

    def _start_vm(self, vm_name: str, **kwargs) -> Dict:
        if vm_name not in virtual_machines:
            raise ValueError(f"VM '{vm_name}' not found.")
        
        vm = virtual_machines[vm_name]
        if vm["status"] == "running":
            return {"message": f"VM '{vm_name}' is already running."}

        vm["status"] = "running"
        vm["ip_address"] = f"192.168.1.{random.randint(100, 200)}"  # nosec B311
        logger.info(f"VM '{vm_name}' started.")
        return {"message": "VM started successfully.", "name": vm_name, "status": "running", "ip_address": vm["ip_address"]}

    def _stop_vm(self, vm_name: str, **kwargs) -> Dict:
        if vm_name not in virtual_machines:
            raise ValueError(f"VM '{vm_name}' not found.")
            
        vm = virtual_machines[vm_name]
        if vm["status"] == "stopped":
            return {"message": f"VM '{vm_name}' is already stopped."}

        vm["status"] = "stopped"
        vm["ip_address"] = None
        logger.info(f"VM '{vm_name}' stopped.")
        return {"message": "VM stopped successfully.", "name": vm_name, "status": "stopped"}

    def _get_vm_status(self, vm_name: str, **kwargs) -> Dict:
        if vm_name not in virtual_machines:
            raise ValueError(f"VM '{vm_name}' not found.")
        return {"vm_status": virtual_machines[vm_name]}

    def _list_vms(self, **kwargs) -> Dict:
        if not virtual_machines:
            return {"message": "No virtual machines have been created."}
        return {"virtual_machines": list(virtual_machines.values())}