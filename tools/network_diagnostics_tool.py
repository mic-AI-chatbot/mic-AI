import logging
import json
import socket
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool
from scapy.all import sr1, IP, ICMP, TCP, UDP, DNS, DNSQR, conf, traceroute, RandShort # Import necessary Scapy modules

logger = logging.getLogger(__name__)

class NetworkDiagnosticsTool(BaseTool):
    """
    A tool for performing various network diagnostic operations like ping,
    traceroute, NS lookup, and port scanning.
    """

    def __init__(self, tool_name: str = "NetworkDiagnostics", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        conf.verb = 0 # Suppress Scapy verbose output

    @property
    def description(self) -> str:
        return "Performs network diagnostics: ping, traceroute, NS lookup, port scan, and gets local IP."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["ping", "traceroute", "nslookup", "port_scan", "get_local_ip_address"]},
                "host": {"type": "string", "description": "The target host (IP address or hostname)."},
                "count": {"type": "integer", "description": "Number of pings to send.", "default": 4},
                "max_hops": {"type": "integer", "description": "Maximum hops for traceroute.", "default": 30},
                "ports": {"type": "array", "items": {"type": "integer"}, "description": "List of ports to scan."},
                "output_format": {"type": "string", "enum": ["text", "json"], "default": "text"}
            },
            "required": ["operation"]
        }

    def _ping_host(self, host: str, count: int = 4) -> Dict[str, Any]:
        """Pings a host to check for network connectivity."""
        try:
            ans, unans = sr1(IP(dst=host)/ICMP(), timeout=2, retry=count, verbose=0)
            if ans:
                return {"host": host, "status": "reachable", "rtt_seconds": round(ans.time - ans.sent_time, 4)}
            else:
                return {"host": host, "status": "unreachable"}
        except Exception as e:
            return {"host": host, "status": "error", "message": str(e)}

    def _traceroute_host(self, host: str, max_hops: int = 30) -> Dict[str, Any]:
        """Traces the route to a host."""
        try:
            ans, unans = traceroute(host, maxttl=max_hops, timeout=1, verbose=0)
            trace_output = []
            for s, r in ans:
                trace_output.append({"ttl": s.ttl, "ip": r.src})
            return {"host": host, "trace": trace_output}
        except Exception as e:
            return {"host": host, "status": "error", "message": str(e)}

    def _nslookup_host(self, host: str) -> Dict[str, Any]:
        """Performs DNS lookups for a host."""
        try:
            ans = sr1(IP(dst="8.8.8.8")/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname=host)), timeout=2, verbose=0)
            if ans and ans.haslayer(DNS) and ans.an:
                answers = [str(ip) for ip in ans.an.rdata] if isinstance(ans.an.rdata, bytes) else [str(ans.an.rdata)]
                return {"host": host, "ip_addresses": answers}
            else:
                return {"host": host, "ip_addresses": []}
        except Exception as e:
            return {"host": host, "status": "error", "message": str(e)}

    def _port_scan_host(self, host: str, ports: List[int]) -> Dict[str, Any]:
        """Scans for open ports on a host."""
        open_ports = []
        try:
            for port in ports:
                ans = sr1(IP(dst=host)/TCP(dport=port, flags="S"), timeout=1, verbose=0)
                if ans and ans.haslayer(TCP) and ans.getlayer(TCP).flags == 0x12: # SYN-ACK
                    open_ports.append(port)
                    sr1(IP(dst=host)/TCP(dport=port, flags="R"), timeout=0.1, verbose=0) # Send RST to close
            return {"host": host, "open_ports": open_ports}
        except Exception as e:
            return {"host": host, "status": "error", "message": str(e)}

    def _get_local_ip_address(self) -> Dict[str, Any]:
        """Gets the local machine's IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            return {"local_ip_address": ip_address}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute(self, operation: str, output_format: str = "text", **kwargs: Any) -> Union[str, Dict[str, Any]]:
        """Executes a network diagnostic action."""
        result: Any = {}
        try:
            if operation == "ping":
                result = self._ping_host(kwargs['host'], kwargs.get('count', 4))
            elif operation == "traceroute":
                result = self._traceroute_host(kwargs['host'], kwargs.get('max_hops', 30))
            elif operation == "nslookup":
                result = self._nslookup_host(kwargs['host'])
            elif operation == "port_scan":
                result = self._port_scan_host(kwargs['host'], kwargs['ports'])
            elif operation == "get_local_ip_address":
                result = self._get_local_ip_address()
            else:
                raise ValueError(f"Invalid operation '{operation}'.")

            if output_format == "json":
                return json.dumps(result, indent=2)
            else: # text format
                if isinstance(result, dict):
                    return "\n".join([f"{k}: {v}" for k, v in result.items()])
                elif isinstance(result, list):
                    return "\n".join([str(item) for item in result])
                else:
                    return str(result)
        except Exception as e:
            self.logger.error(f"An error occurred during network diagnostics: {e}")
            return json.dumps({"status": "error", "message": str(e)}) if output_format == "json" else f"Error: {e}"

if __name__ == '__main__':
    print("Demonstrating NetworkDiagnosticsTool functionality...")
    
    diag_tool = NetworkDiagnosticsTool()
    
    try:
        # 1. Ping a host
        print("\n--- Pinging google.com ---")
        ping_result = diag_tool.execute(operation="ping", host="google.com")
        print(ping_result)

        # 2. Traceroute to a host
        print("\n--- Tracerouting to google.com ---")
        traceroute_result = diag_tool.execute(operation="traceroute", host="google.com", output_format="json")
        print(traceroute_result)

        # 3. NSLookup a host
        print("\n--- NSLookup for google.com ---")
        nslookup_result = diag_tool.execute(operation="nslookup", host="google.com")
        print(nslookup_result)

        # 4. Port scan a host (e.g., scan common web ports on localhost or a known test server)
        # Note: Port scanning can be slow and might trigger security alerts. Use with caution.
        print("\n--- Port scanning localhost (ports 80, 443, 22) ---")
        port_scan_result = diag_tool.execute(operation="port_scan", host="127.0.0.1", ports=[80, 443, 22])
        print(port_scan_result)

        # 5. Get local IP address
        print("\n--- Getting local IP address ---")
        local_ip_result = diag_tool.execute(operation="get_local_ip_address")
        print(local_ip_result)

    except Exception as e:
        print(f"\nAn error occurred: {e}")