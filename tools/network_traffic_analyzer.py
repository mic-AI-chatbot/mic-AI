import logging
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class NetworkTrafficAnalyzerSimulatorTool(BaseTool):
    """
    A tool that simulates network traffic generation and analysis, providing
    insights into traffic patterns, top talkers, and protocol distribution.
    """

    def __init__(self, tool_name: str = "NetworkTrafficAnalyzerSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates network traffic generation and analysis to identify patterns and top talkers."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_traffic_data", "analyze_traffic_data"]},
                "num_packets": {"type": "integer", "description": "Number of packets to generate.", "default": 100},
                "duration_seconds": {"type": "integer", "description": "Duration over which to simulate traffic generation.", "default": 60},
                "traffic_data": {"type": "array", "items": {"type": "object"}, "description": "List of simulated traffic packets for analysis."}
            },
            "required": ["operation"]
        }

    def _generate_random_ip(self) -> str:
        return f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"  # nosec B311

    def generate_traffic_data(self, num_packets: int = 100, duration_seconds: int = 60) -> List[Dict[str, Any]]:
        """Generates simulated network traffic data."""
        traffic_data = []
        start_time = datetime.now()
        
        protocols = ["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS"]
        common_ports = {"HTTP": 80, "HTTPS": 443, "DNS": 53, "TCP": random.randint(1024, 65535), "UDP": random.randint(1024, 65535)}  # nosec B311

        for i in range(num_packets):
            protocol = random.choice(protocols)  # nosec B311
            source_ip = self._generate_random_ip()
            destination_ip = self._generate_random_ip()
            port = common_ports.get(protocol, random.randint(1, 65535))  # nosec B311
            size_bytes = random.randint(64, 1500)  # nosec B311
            timestamp = (start_time + timedelta(seconds=random.uniform(0, duration_seconds))).isoformat()  # nosec B311
            
            traffic_data.append({
                "source_ip": source_ip,
                "destination_ip": destination_ip,
                "protocol": protocol,
                "port": port,
                "size_bytes": size_bytes,
                "timestamp": timestamp
            })
        return traffic_data

    def analyze_traffic_data(self, traffic_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes simulated network traffic data."""
        if not traffic_data:
            return {"status": "info", "message": "No traffic data provided for analysis."}

        total_packets = len(traffic_data)
        total_bytes = sum(p["size_bytes"] for p in traffic_data)

        # Top Talkers (Source IP)
        source_ip_counts = Counter(p["source_ip"] for p in traffic_data)
        top_source_ips = source_ip_counts.most_common(5)

        # Top Talkers (Destination IP)
        dest_ip_counts = Counter(p["destination_ip"] for p in traffic_data)
        top_dest_ips = dest_ip_counts.most_common(5)

        # Protocol Distribution
        protocol_counts = Counter(p["protocol"] for p in traffic_data)
        protocol_distribution = {p: round((c / total_packets) * 100, 2) for p, c in protocol_counts.items()}

        # Port Usage
        port_counts = Counter(p["port"] for p in traffic_data)
        top_ports = port_counts.most_common(5)

        # Simple Anomaly Detection: High traffic from/to a single IP
        anomalies = []
        if top_source_ips and top_source_ips[0][1] > (total_packets * 0.3): # More than 30% from one source
            anomalies.append(f"High traffic volume from source IP: {top_source_ips[0][0]} ({top_source_ips[0][1]} packets).")
        if top_dest_ips and top_dest_ips[0][1] > (total_packets * 0.3): # More than 30% to one destination
            anomalies.append(f"High traffic volume to destination IP: {top_dest_ips[0][0]} ({top_dest_ips[0][1]} packets).")

        return {
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            "top_source_ips": top_source_ips,
            "top_destination_ips": top_dest_ips,
            "protocol_distribution_percent": protocol_distribution,
            "top_ports": top_ports,
            "anomalies_detected": anomalies
        }

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "generate_traffic_data":
            return self.generate_traffic_data(kwargs.get("num_packets", 100), kwargs.get("duration_seconds", 60))
        elif operation == "analyze_traffic_data":
            return self.analyze_traffic_data(kwargs["traffic_data"])
        else:
            raise ValueError(f"Unsupported operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating NetworkTrafficAnalyzerSimulatorTool functionality...")
    
    analyzer_tool = NetworkTrafficAnalyzerSimulatorTool()
    
    try:
        # 1. Generate some simulated traffic data
        print("\n--- Generating 200 packets over 30 seconds ---")
        simulated_traffic = analyzer_tool.execute(operation="generate_traffic_data", num_packets=200, duration_seconds=30)
        print(f"Generated {len(simulated_traffic)} packets.")

        # 2. Analyze the generated traffic data
        print("\n--- Analyzing the simulated traffic data ---")
        analysis_report = analyzer_tool.execute(operation="analyze_traffic_data", traffic_data=simulated_traffic)
        print(json.dumps(analysis_report, indent=2))

        # 3. Generate traffic with a clear anomaly (e.g., one IP sending a lot)
        print("\n--- Generating traffic with a simulated anomaly ---")
        anomalous_traffic = analyzer_tool.execute(operation="generate_traffic_data", num_packets=100, duration_seconds=10)
        # Manually inject an anomaly
        for _ in range(50): # 50% of traffic from one source
            anomalous_traffic.append({
                "source_ip": "192.168.1.10",
                "destination_ip": analyzer_tool._generate_random_ip(),
                "protocol": "TCP", "port": 80, "size_bytes": 100,
                "timestamp": datetime.now().isoformat()
            })
        
        print("\n--- Analyzing anomalous traffic data ---")
        anomaly_report = analyzer_tool.execute(operation="analyze_traffic_data", traffic_data=anomalous_traffic)
        print(json.dumps(anomaly_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")