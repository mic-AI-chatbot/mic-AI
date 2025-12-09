import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated workflows and alerts
monitored_workflows: Dict[str, Dict[str, Any]] = {}
generated_alerts: List[Dict[str, Any]] = []

class WorkflowMonitorTool(BaseTool):
    """
    A tool to simulate monitoring and alerting for workflows.
    """
    def __init__(self, tool_name: str = "workflow_monitor_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates monitoring workflows, generating alerts, and resolving them."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'start_monitoring', 'update_status', 'get_alerts', 'resolve_alert', 'list_monitored_workflows'."
                },
                "workflow_id": {"type": "string", "description": "The unique ID of the workflow to monitor."},
                "current_status": {
                    "type": "string", 
                    "description": "The current status of the workflow ('running', 'failed', 'completed')."
                },
                "alert_id": {"type": "string", "description": "The ID of the alert to resolve."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            workflow_id = kwargs.get("workflow_id")
            alert_id = kwargs.get("alert_id")

            if action in ['start_monitoring', 'update_status'] and not workflow_id:
                raise ValueError(f"'workflow_id' is required for the '{action}' action.")
            if action == 'resolve_alert' and not alert_id:
                raise ValueError("'alert_id' is required for 'resolve_alert' action.")

            actions = {
                "start_monitoring": self._start_monitoring,
                "update_status": self._update_workflow_status,
                "get_alerts": self._get_alerts,
                "resolve_alert": self._resolve_alert,
                "list_monitored_workflows": self._list_monitored_workflows,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WorkflowMonitorTool: {e}")
            return {"error": str(e)}

    def _start_monitoring(self, workflow_id: str, **kwargs) -> Dict:
        if workflow_id in monitored_workflows:
            raise ValueError(f"Workflow '{workflow_id}' is already being monitored.")
        
        monitored_workflows[workflow_id] = {
            "id": workflow_id,
            "status": "running",
            "last_update": datetime.now(timezone.utc).isoformat(),
            "alerts": []
        }
        logger.info(f"Started monitoring workflow '{workflow_id}'.")
        return {"message": "Monitoring started.", "workflow_id": workflow_id}

    def _update_workflow_status(self, workflow_id: str, current_status: str, **kwargs) -> Dict:
        if workflow_id not in monitored_workflows:
            raise ValueError(f"Workflow '{workflow_id}' is not being monitored.")
        if current_status not in ["running", "failed", "completed"]:
            raise ValueError(f"Invalid status '{current_status}'.")
            
        workflow = monitored_workflows[workflow_id]
        workflow["status"] = current_status
        workflow["last_update"] = datetime.now(timezone.utc).isoformat()

        # Simulate alert generation
        if current_status == "failed":
            alert_id = f"ALERT-{random.randint(1000, 9999)}"  # nosec B311
            new_alert = {
                "id": alert_id,
                "workflow_id": workflow_id,
                "type": "failure",
                "message": f"Workflow '{workflow_id}' has failed!",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "resolved": False
            }
            generated_alerts.append(new_alert)
            workflow["alerts"].append(alert_id)
            logger.warning(f"Alert '{alert_id}' generated for workflow '{workflow_id}'.")
            return {"message": "Workflow status updated and alert generated.", "workflow_id": workflow_id, "new_status": current_status, "alert_id": alert_id}
        
        logger.info(f"Workflow '{workflow_id}' status updated to '{current_status}'.")
        return {"message": "Workflow status updated.", "workflow_id": workflow_id, "new_status": current_status}

    def _get_alerts(self, **kwargs) -> Dict:
        if not generated_alerts:
            return {"message": "No alerts currently active."}
        return {"active_alerts": [alert for alert in generated_alerts if not alert["resolved"]]}

    def _resolve_alert(self, alert_id: str, **kwargs) -> Dict:
        for alert in generated_alerts:
            if alert["id"] == alert_id:
                if alert["resolved"]:
                    return {"message": f"Alert '{alert_id}' is already resolved."}
                alert["resolved"] = True
                alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
                logger.info(f"Alert '{alert_id}' resolved.")
                return {"message": "Alert resolved successfully.", "alert_id": alert_id}
        raise ValueError(f"Alert '{alert_id}' not found.")

    def _list_monitored_workflows(self, **kwargs) -> Dict:
        if not monitored_workflows:
            return {"message": "No workflows are currently being monitored."}
        return {"monitored_workflows": list(monitored_workflows.values())}