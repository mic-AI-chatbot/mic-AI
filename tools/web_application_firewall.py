import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated WAF rules and blocked requests
waf_rules: Dict[str, Dict[str, Any]] = {}
blocked_requests: List[Dict[str, Any]] = []

class WebApplicationFirewallTool(BaseTool):
    """
    A tool to simulate a Web Application Firewall (WAF) for configuring rules,
    monitoring traffic, and managing blocked requests.
    """
    def __init__(self, tool_name: str = "web_application_firewall_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates a WAF: configure rules, monitor traffic, block requests, and view logs."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'configure_rule', 'monitor_traffic', 'block_request', 'list_rules', 'list_blocked_requests'."
                },
                "rule_id": {"type": "string", "description": "The unique ID for the WAF rule."},
                "rule_type": {
                    "type": "string", 
                    "description": "Type of rule (e.g., 'ip_blacklist', 'sql_injection', 'xss')."
                },
                "rule_action": {
                    "type": "string", 
                    "description": "Action to take when rule matches ('block', 'alert', 'allow')."
                },
                "criteria": {"type": "object", "description": "Criteria for the rule (e.g., {'ip_address': '1.2.3.4'})."},
                "request_id": {"type": "string", "description": "The ID of the request to block."},
                "block_reason": {"type": "string", "description": "The reason for blocking the request."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            rule_id = kwargs.get("rule_id")
            request_id = kwargs.get("request_id")

            if action == 'configure_rule' and not rule_id:
                raise ValueError("'rule_id' is required for 'configure_rule' action.")
            if action == 'block_request' and not request_id:
                raise ValueError("'request_id' is required for 'block_request' action.")

            actions = {
                "configure_rule": self._configure_rule,
                "monitor_traffic": self._monitor_traffic,
                "block_request": self._block_request,
                "list_rules": self._list_rules,
                "list_blocked_requests": self._list_blocked_requests,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WebApplicationFirewallTool: {e}")
            return {"error": str(e)}

    def _configure_rule(self, rule_id: str, rule_type: str, rule_action: str, criteria: Dict[str, Any], **kwargs) -> Dict:
        if not all([rule_type, rule_action, criteria]):
            raise ValueError("'rule_type', 'rule_action', and 'criteria' are required to configure a rule.")
        if rule_id in waf_rules:
            raise ValueError(f"Rule '{rule_id}' already exists.")
        
        new_rule = {
            "id": rule_id,
            "type": rule_type,
            "action": rule_action,
            "criteria": criteria,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        waf_rules[rule_id] = new_rule
        logger.info(f"WAF rule '{rule_id}' configured.")
        return {"message": "Rule configured successfully.", "details": new_rule}

    def _monitor_traffic(self, **kwargs) -> Dict:
        logger.info("Simulating traffic monitoring.")
        
        # Generate some simulated traffic data
        simulated_traffic = []
        for _ in range(random.randint(5, 15)):  # nosec B311
            status = random.choice(["allowed", "blocked", "alerted"])  # nosec B311
            simulated_traffic.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": f"192.168.1.{random.randint(1, 254)}",  # nosec B311
                "request_path": random.choice(["/login", "/products", "/admin", "/search"]),  # nosec B311
                "status": status,
                "rule_id": random.choice(list(waf_rules.keys())) if waf_rules and status == "blocked" else None  # nosec B311
            })
        return {"monitored_traffic": simulated_traffic}

    def _block_request(self, request_id: str, block_reason: str, **kwargs) -> Dict:
        if not block_reason:
            raise ValueError("'block_reason' is required to block a request.")
            
        new_blocked_request = {
            "request_id": request_id,
            "reason": block_reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        blocked_requests.append(new_blocked_request)
        logger.info(f"Request '{request_id}' blocked due to '{block_reason}'.")
        return {"message": "Request blocked successfully.", "details": new_blocked_request}

    def _list_rules(self, **kwargs) -> Dict:
        if not waf_rules:
            return {"message": "No WAF rules configured yet."}
        return {"waf_rules": list(waf_rules.values())}

    def _list_blocked_requests(self, **kwargs) -> Dict:
        if not blocked_requests:
            return {"message": "No requests have been blocked yet."}
        return {"blocked_requests": blocked_requests}