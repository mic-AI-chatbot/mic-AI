import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated endpoint devices
managed_devices: Dict[str, Dict[str, Any]] = {}

class UnifiedEndpointManagementTool(BaseTool):
    """
    A tool for simulating a Unified Endpoint Management (UEM) platform.
    """
    def __init__(self, tool_name: str = "unified_endpoint_management_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates a UEM platform for managing endpoint devices (enroll, apply policy, wipe, report)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'enroll', 'get_status', 'apply_policy', 'wipe', 'generate_report'."
                },
                "device_id": {"type": "string", "description": "The unique ID of the device (e.g., a MAC address or serial number)."},
                "device_type": {"type": "string", "description": "The type of device (e.g., 'laptop', 'mobile')."},
                "owner": {"type": "string", "description": "The user or owner of the device."},
                "policy_name": {"type": "string", "description": "The name of the policy to apply (e.g., 'password_required', 'encryption_enabled')."},
                "report_filter_status": {"type": "string", "description": "Filter report by status (e.g., 'enrolled', 'wiped')."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            device_id = kwargs.get("device_id")

            if action in ['enroll', 'get_status', 'apply_policy', 'wipe'] and not device_id:
                raise ValueError(f"'device_id' is required for the '{action}' action.")

            actions = {
                "enroll": self._enroll_device,
                "get_status": self._get_device_status,
                "apply_policy": self._apply_policy,
                "wipe": self._wipe_device,
                "generate_report": self._generate_report,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](device_id=device_id, **kwargs)

        except Exception as e:
            logger.error(f"An error occurred in UEM Tool: {e}")
            return {"error": str(e)}

    def _enroll_device(self, device_id: str, device_type: str, owner: str, **kwargs) -> Dict:
        if not device_type or not owner:
            raise ValueError("'device_type' and 'owner' are required for enrollment.")
        
        if device_id in managed_devices:
            raise ValueError(f"Device '{device_id}' is already enrolled.")

        logger.info(f"Enrolling new device: {device_id}")
        
        new_device = {
            "device_id": device_id,
            "device_type": device_type,
            "owner": owner,
            "status": "enrolled",
            "os_version": f"{random.choice(['Windows 11', 'macOS 14', 'Ubuntu 24.04'])}.{random.randint(1, 5)}",  # nosec B311
            "policies": ["default_security_profile"],
            "enrolled_at": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat()
        }
        managed_devices[device_id] = new_device
        
        return {"message": "Device enrolled successfully.", "details": new_device}

    def _get_device_status(self, device_id: str, **kwargs) -> Dict:
        if device_id not in managed_devices:
            raise ValueError(f"Device '{device_id}' not found.")
        
        # Simulate a device checking in
        device = managed_devices[device_id]
        device["last_seen"] = datetime.now(timezone.utc).isoformat()
        
        return {"device_status": device}

    def _apply_policy(self, device_id: str, policy_name: str, **kwargs) -> Dict:
        if not policy_name:
            raise ValueError("'policy_name' is required to apply a policy.")
            
        if device_id not in managed_devices:
            raise ValueError(f"Device '{device_id}' not found.")
        
        device = managed_devices[device_id]
        if policy_name not in device["policies"]:
            device["policies"].append(policy_name)
            logger.info(f"Applied policy '{policy_name}' to device '{device_id}'.")
            return {"message": f"Policy '{policy_name}' applied successfully.", "device_id": device_id, "current_policies": device["policies"]}
        else:
            return {"message": f"Policy '{policy_name}' was already applied.", "device_id": device_id, "current_policies": device["policies"]}

    def _wipe_device(self, device_id: str, **kwargs) -> Dict:
        if device_id not in managed_devices:
            raise ValueError(f"Device '{device_id}' not found.")
            
        device = managed_devices[device_id]
        if device["status"] == "wiped":
            return {"message": f"Device '{device_id}' has already been wiped."}

        device["status"] = "wiped"
        device["policies"] = []
        logger.warning(f"Initiated remote wipe for device '{device_id}'.")
        
        return {"message": f"Remote wipe command sent to device '{device_id}'. Its status is now 'wiped'."}

    def _generate_report(self, report_filter_status: Optional[str] = None, **kwargs) -> Dict:
        if not managed_devices:
            return {"message": "No devices are currently managed."}
            
        report_data = list(managed_devices.values())
        
        if report_filter_status:
            report_data = [dev for dev in report_data if dev["status"] == report_filter_status]
            
        return {"device_report": report_data, "total_devices": len(report_data)}