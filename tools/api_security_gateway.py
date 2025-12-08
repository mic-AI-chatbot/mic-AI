import logging
import json
import random
import re
from typing import List, Dict, Any
from collections import Counter
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SimpleWAF:
    """A simple Web Application Firewall to manage security policies and detect threats."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimpleWAF, cls).__new__(cls)
            cls._instance.ip_blocklist: List[str] = ["1.2.3.4", "5.6.7.8"]
            cls._instance.rules: Dict[str, Dict[str, Any]] = {
                "SQLi_1": {"description": "Basic SQL injection attempt", "pattern": r"(\'|\"|\-|\s)*(union|select|insert|update|delete|drop)"},
                "XSS_1": {"description": "Basic XSS attempt", "pattern": r"<script>.*</script>"}
            }
        return cls._instance

    def add_ip_to_blocklist(self, ip_address: str):
        if ip_address not in self.ip_blocklist:
            self.ip_blocklist.append(ip_address)

    def add_rule(self, rule_name: str, description: str, pattern: str):
        self.rules[rule_name] = {"description": description, "pattern": pattern}

    def check_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Checks a request against the WAF policies."""
        ip = request.get("source_ip")
        if ip in self.ip_blocklist:
            return {"threat_type": "Blocked IP", "details": f"IP address {ip} is on the blocklist."}

        path = request.get("path", "")
        for rule_name, rule in self.rules.items():
            if re.search(rule["pattern"], path, re.IGNORECASE):
                return {"threat_type": rule["description"], "details": f"Request path '{path}' matched rule '{rule_name}'."}
        
        return None

waf = SimpleWAF()

def generate_mock_requests(num_requests: int, threat_prob: float = 0.1) -> List[Dict[str, Any]]:
    """Generates a stream of mock API requests, some potentially malicious."""
    requests = []
    for _ in range(num_requests):
        source_ip = f"10.0.0.{random.randint(1, 100)}"  # nosec B311
        path = f"/api/v1/users/{random.randint(1, 100)}"  # nosec B311
        
        if random.random() < threat_prob:  # nosec B311
            threat_type = random.choice(["blocked_ip", "sqli", "xss"])  # nosec B311
            if threat_type == "blocked_ip":
                source_ip = random.choice(waf.ip_blocklist)  # nosec B311
            elif threat_type == "sqli":
                path += "?id=' or 1=1--"
            elif threat_type == "xss":
                path += "?name=<script>alert('xss')</script>"
        
        requests.append({"source_ip": source_ip, "path": path})
    return requests

class AddIPToBlocklistTool(BaseTool):
    """Adds an IP address to the security blocklist."""
    def __init__(self, tool_name="add_ip_to_blocklist"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a specified IP address to the WAF's blocklist, immediately blocking all requests from it."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"ip_address": {"type": "string", "description": "The IP address to block."}},
            "required": ["ip_address"]
        }

    def execute(self, ip_address: str, **kwargs: Any) -> str:
        waf.add_ip_to_blocklist(ip_address)
        report = {
            "message": f"IP address {ip_address} added to the blocklist.",
            "current_blocklist": waf.ip_blocklist
        }
        return json.dumps(report, indent=2)

class AnalyzeRequestStreamForThreatsTool(BaseTool):
    """Analyzes a stream of mock API requests for security threats."""
    def __init__(self, tool_name="analyze_request_stream_for_threats"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates and analyzes a stream of API requests to detect security threats based on configured WAF rules."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "num_requests_to_simulate": {"type": "integer", "description": "The number of requests to simulate.", "default": 1000},
                "threat_probability": {"type": "number", "description": "The probability of a request being a threat.", "default": 0.05}
            },
            "required": []
        }

    def execute(self, num_requests_to_simulate: int = 1000, threat_probability: float = 0.05, **kwargs: Any) -> str:
        requests = generate_mock_requests(num_requests_to_simulate, threat_probability)
        
        detected_threats = []
        for req in requests:
            threat = waf.check_request(req)
            if threat:
                detected_threats.append({**req, "threat": threat})
        
        threat_summary = Counter(t["threat"]["threat_type"] for t in detected_threats)
        
        report = {
            "requests_analyzed": len(requests),
            "threats_detected": len(detected_threats),
            "threat_summary": dict(threat_summary),
            "detected_threats_sample": detected_threats[:5] # Show a sample of detected threats
        }
        return json.dumps(report, indent=2)