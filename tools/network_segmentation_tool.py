import logging
import os
import json
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Predefined segmentation policies
POLICIES = {
    "isolation_policy": {
        "description": "Denies all inbound traffic from external sources.",
        "rules": [
            {"traffic_direction": "inbound", "source": "external", "action": "deny"}
        ]
    },
    "web_access_policy": {
        "description": "Allows outbound traffic to common web ports (80, 443).",
        "rules": [
            {"traffic_direction": "outbound", "destination_port": 80, "action": "allow"},
            {"traffic_direction": "outbound", "destination_port": 443, "action": "allow"}
        ]
    },
    "internal_only_policy": {
        "description": "Allows traffic only from internal sources.",
        "rules": [
            {"traffic_direction": "inbound", "source": "internal", "action": "allow"},
            {"traffic_direction": "inbound", "source": "external", "action": "deny"}
        ]
    }
}

class NetworkSegmentationSimulatorTool(BaseTool):
    """
    A tool that simulates network segmentation by managing network segments
    and applying policies to control traffic flow.
    """

    def __init__(self, tool_name: str = "NetworkSegmentationSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.segments_file = os.path.join(self.data_dir, "network_segments.json")
        # Segments structure: {segment_name: {description: "...", ip_ranges: [], devices: [], policies: []}}
        self.segments: Dict[str, Dict[str, Any]] = self._load_data(self.segments_file, default={})

    @property
    def description(self) -> str:
        return "Simulates network segmentation: create segments, apply policies, and check traffic flow."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_segment", "apply_policy", "check_traffic_flow", "list_segments"]},
                "segment_name": {"type": "string", "description": "The name of the network segment."},
                "description": {"type": "string", "description": "Description of the segment."},
                "ip_ranges": {"type": "array", "items": {"type": "string"}, "description": "List of IP ranges in CIDR format (e.g., ['192.168.1.0/24'])."},
                "devices": {"type": "array", "items": {"type": "string"}, "description": "List of device names in the segment."},
                "policy_name": {"type": "string", "enum": list(POLICIES.keys()), "description": "The name of the policy to apply."},
                "source_ip": {"type": "string", "description": "Source IP address for traffic flow check."},
                "destination_ip": {"type": "string", "description": "Destination IP address for traffic flow check."},
                "port": {"type": "integer", "description": "Destination port for traffic flow check."},
                "protocol": {"type": "string", "enum": ["TCP", "UDP", "ICMP"], "default": "TCP"}
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

    def _save_data(self):
        with open(self.segments_file, 'w') as f: json.dump(self.segments, f, indent=2)

    def _ip_in_range(self, ip: str, ip_ranges: List[str]) -> bool:
        """Helper to check if an IP is within any of the given CIDR ranges."""
        # This is a simplified check. A real implementation would use ipaddress module.
        # For simulation, we'll just check if the IP starts with the range prefix.
        for ip_range in ip_ranges:
            if ip_range.endswith('/24'): # Simple /24 check
                if ip.startswith(ip_range.split('/')[0].rsplit('.', 1)[0]):
                    return True
            elif ip_range.endswith('/16'): # Simple /16 check
                if ip.startswith(ip_range.split('/')[0].rsplit('.', 2)[0]):
                    return True
            elif ip.startswith(ip_range.split('/')[0]): # Direct prefix match
                return True
        return False

    def create_segment(self, segment_name: str, description: str, ip_ranges: Optional[List[str]] = None, devices: Optional[List[str]] = None) -> Dict[str, Any]:
        """Creates a new network segment."""
        if segment_name in self.segments: raise ValueError(f"Segment '{segment_name}' already exists.")
        
        new_segment = {
            "name": segment_name, "description": description,
            "ip_ranges": ip_ranges or [], "devices": devices or [],
            "associated_policies": []
        }
        self.segments[segment_name] = new_segment
        self._save_data()
        return {"status": "success", "message": f"Segment '{segment_name}' created."}

    def apply_policy(self, segment_name: str, policy_name: str) -> Dict[str, Any]:
        """Applies a predefined policy to a network segment."""
        segment = self.segments.get(segment_name)
        if not segment: raise ValueError(f"Segment '{segment_name}' not found.")
        
        policy = POLICIES.get(policy_name)
        if not policy: raise ValueError(f"Policy '{policy_name}' not found.")

        if policy_name not in segment["associated_policies"]:
            segment["associated_policies"].append(policy_name)
            self._save_data()
        return {"status": "success", "message": f"Policy '{policy_name}' applied to segment '{segment_name}'."}

    def check_traffic_flow(self, source_ip: str, destination_ip: str, port: int, protocol: str = "TCP") -> Dict[str, Any]:
        """Simulates checking if traffic flow is allowed based on segment policies."""
        source_segment = "external"
        dest_segment = "external"
        
        for seg_name, seg_data in self.segments.items():
            if self._ip_in_range(source_ip, seg_data["ip_ranges"]):
                source_segment = seg_name
            if self._ip_in_range(destination_ip, seg_data["ip_ranges"]):
                dest_segment = seg_name
        
        # Determine traffic direction relative to destination segment
        traffic_direction = "inbound" if source_segment != dest_segment else "internal"
        
        # Check policies on the destination segment
        allowed = True
        reason = "No explicit deny policy found."
        
        if dest_segment != "external" and dest_segment in self.segments:
            for policy_name in self.segments[dest_segment]["associated_policies"]:
                policy_rules = POLICIES[policy_name]["rules"]
                for rule in policy_rules:
                    rule_matches = True
                    if "traffic_direction" in rule and rule["traffic_direction"] != traffic_direction: rule_matches = False
                    if "source" in rule and rule["source"] == "external" and source_segment != "external": rule_matches = False
                    if "source" in rule and rule["source"] == "internal" and source_segment == "external": rule_matches = False
                    if "destination_port" in rule and rule["destination_port"] != port: rule_matches = False
                    if "protocol" in rule and rule["protocol"] != protocol: rule_matches = False

                    if rule_matches:
                        if rule["action"] == "deny":
                            allowed = False
                            reason = f"Denied by policy '{policy_name}' rule: {rule}"
                            break
                        elif rule["action"] == "allow":
                            allowed = True # Explicit allow overrides implicit deny
                            reason = f"Allowed by policy '{policy_name}' rule: {rule}"
                            break
                if not allowed: break # If denied, stop checking policies
        
        return {
            "source_ip": source_ip, "destination_ip": destination_ip, "port": port, "protocol": protocol,
            "source_segment": source_segment, "destination_segment": dest_segment,
            "traffic_direction": traffic_direction, "allowed": allowed, "reason": reason
        }

    def list_segments(self) -> Dict[str, Any]:
        """Lists all defined network segments."""
        return {"segments": list(self.segments.values())}

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "create_segment": self.create_segment,
            "apply_policy": self.apply_policy,
            "check_traffic_flow": self.check_traffic_flow,
            "list_segments": self.list_segments
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating NetworkSegmentationSimulatorTool functionality...")
    temp_dir = "temp_net_seg_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    segment_tool = NetworkSegmentationSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a segment for internal servers
        print("\n--- Creating 'Internal_Servers' segment ---")
        segment_tool.execute(operation="create_segment", segment_name="Internal_Servers",
                             description="Servers hosting internal applications.", ip_ranges=["192.168.1.0/24"])
        print("Segment 'Internal_Servers' created.")

        # 2. Apply an isolation policy to it
        print("\n--- Applying 'isolation_policy' to 'Internal_Servers' ---")
        segment_tool.execute(operation="apply_policy", segment_name="Internal_Servers", policy_name="isolation_policy")
        print("Policy applied.")

        # 3. Check traffic flow (external to internal, should be denied)
        print("\n--- Checking traffic: External (1.1.1.1) to Internal (192.168.1.100) on port 80 ---")
        traffic1 = segment_tool.execute(operation="check_traffic_flow", source_ip="1.1.1.1", destination_ip="192.168.1.100", port=80)
        print(json.dumps(traffic1, indent=2))

        # 4. Create a DMZ segment for web servers
        print("\n--- Creating 'DMZ_Web_Servers' segment ---")
        segment_tool.execute(operation="create_segment", segment_name="DMZ_Web_Servers",
                             description="Web servers accessible from external network.", ip_ranges=["10.0.0.0/24"])
        print("Segment 'DMZ_Web_Servers' created.")

        # 5. Apply web access policy to DMZ
        print("\n--- Applying 'web_access_policy' to 'DMZ_Web_Servers' ---")
        segment_tool.execute(operation="apply_policy", segment_name="DMZ_Web_Servers", policy_name="web_access_policy")
        print("Policy applied.")

        # 6. Check traffic flow (external to DMZ web server on port 80, should be allowed)
        print("\n--- Checking traffic: External (2.2.2.2) to DMZ (10.0.0.50) on port 80 ---")
        traffic2 = segment_tool.execute(operation="check_traffic_flow", source_ip="2.2.2.2", destination_ip="10.0.0.50", port=80)
        print(json.dumps(traffic2, indent=2))

        # 7. Check traffic flow (external to DMZ web server on a non-web port, should be denied by default)
        print("\n--- Checking traffic: External (2.2.2.2) to DMZ (10.0.0.50) on port 22 ---")
        traffic3 = segment_tool.execute(operation="check_traffic_flow", source_ip="2.2.2.2", destination_ip="10.0.0.50", port=22)
        print(json.dumps(traffic3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")