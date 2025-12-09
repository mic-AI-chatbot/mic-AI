import psutil
import json
import logging
import subprocess  # nosec B404
import sys
import re
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SystemHealthCheckerTool(BaseTool):
    """
    A tool for performing various system health checks.
    """

    def __init__(self, tool_name: str = "system_health_checker_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Performs various system health checks, such as CPU, memory, disk, and network status."

    def _check_cpu_health(self) -> Dict[str, Any]:
        """
        Checks CPU load and core information.
        """
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_cores_physical": psutil.cpu_count(logical=False),
            "cpu_cores_logical": psutil.cpu_count(logical=True)
        }

    def _check_memory_health(self) -> Dict[str, Any]:
        """
        Checks memory usage and swap.
        """
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "memory_total_gb": round(mem.total / (1024**3), 2),
            "memory_available_gb": round(mem.available / (1024**3), 2),
            "memory_used_percent": mem.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_percent": swap.percent
        }

    def _check_disk_health(self) -> List[Dict[str, Any]]:
        """
        Checks disk space and I/O.
        """
        disk_info = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_percent": usage.percent
                })
            except Exception as e:
                self.logger.warning(f"Could not get disk info for {partition.mountpoint}: {e}")
        return disk_info

    def _check_network_health(self, host: str = "8.8.8.8", timeout: int = 5) -> Dict[str, Any]:
        """
        Checks network connectivity and latency by pinging a host.
        """
        try:
            # Use subprocess for cross-platform ping
            param = '-n' if 'win' in sys.platform else '-c'
            command = ['ping', param, '1', host]
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)  # nosec B603
            if result.returncode == 0:
                # Extract latency from ping output (example for Windows/Linux)
                latency_match = re.search(r'Average = (\d+)ms' if 'win' in sys.platform else r'time=(\d+\.\d+) ms', result.stdout)
                latency = float(latency_match.group(1)) if latency_match else None
                return {"status": "reachable", "host": host, "latency_ms": latency}
            else:
                return {"status": "unreachable", "host": host, "error": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "host": host}
        except Exception as e:
            return {"status": "error", "host": host, "message": str(e)}

    def _check_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Checks the status of a specific system service.
        (Supports systemd on Linux, sc query on Windows)
        """
        try:
            if 'win' in sys.platform:
                command = ["sc", "query", service_name]
                result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)  # nosec B603
                if "RUNNING" in result.stdout.upper():
                    status = "active"
                elif "STOPPED" in result.stdout.upper():
                    status = "inactive"
                else:
                    status = "not_found"
                return {"service": service_name, "status": status}
            else: # Assuming systemd for Linux
                command = ["systemctl", "is-active", service_name]
                result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)  # nosec B603
                if result.returncode == 0:
                    return {"service": service_name, "status": "active"}
                else:
                    # Distinguish between inactive and not-found
                    command = ["systemctl", "status", service_name]
                    status_result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)  # nosec B603
                    if "Loaded: not-found" in status_result.stderr:
                        return {"service": service_name, "status": "not_found"}
                    else:
                        return {"service": service_name, "status": "inactive"}
        except Exception as e:
            return {"service": service_name, "status": "error", "message": str(e)}

    def _run_all_checks(self) -> Dict[str, Any]:
        """
        Runs a comprehensive set of system health checks.
        """
        all_checks = {
            "cpu_health": self._check_cpu_health(),
            "memory_health": self._check_memory_health(),
            "disk_health": self._check_disk_health(),
            "network_health": self._check_network_health(), # Default host
            # Add more checks here as needed
        }
        return all_checks

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["check_cpu_health", "check_memory_health", "check_disk_health", "check_network_health", "check_service_status", "run_all_checks"]},
                "host": {"type": "string", "description": "Host to ping for network check (e.g., '8.8.8.8')."},
                "timeout": {"type": "integer", "minimum": 1, "default": 5, "description": "Timeout for network check in seconds."},
                "service_name": {"type": "string", "description": "Name of the system service to check (e.g., 'sshd', 'nginx')."},
                "output_format": {"type": "string", "enum": ["text", "json"], "default": "text"}
            },
            "required": ["operation"]
        }

    def execute(self, operation: str, output_format: str = "text", **kwargs: Any) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        operation = operation.lower()
        result = {}

        try:
            if operation == "check_cpu_health":
                result = self._check_cpu_health()
            elif operation == "check_memory_health":
                result = self._check_memory_health()
            elif operation == "check_disk_health":
                result = self._check_disk_health()
            elif operation == "check_network_health":
                host = kwargs.get('host', "8.8.8.8")
                timeout = kwargs.get('timeout', 5)
                return self._check_network_health(host, timeout)
            elif operation == "check_service_status":
                service_name = kwargs.get('service_name')
                if not service_name:
                    raise ValueError("'service_name' is required for 'check_service_status' operation.")
                result = self._check_service_status(service_name)
            elif operation == "run_all_checks":
                result = self._run_all_checks()
            else:
                raise ValueError(f"Invalid operation '{operation}'. Supported operations are 'check_cpu_health', 'check_memory_health', 'check_disk_health', 'check_network_health', 'check_service_status', 'run_all_checks'.")

            if output_format == "json":
                return json.dumps(result, indent=2)
            else: # text format
                if isinstance(result, dict):
                    # Special handling for nested dicts/lists in run_all_checks
                    if operation == "run_all_checks":
                        output_lines = []
                        for key, value in result.items():
                            output_lines.append(f"{key.replace('_', ' ').title()}:")
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    output_lines.append(f"  {sub_key}: {sub_value}")
                            elif isinstance(value, list):
                                for item in value:
                                    output_lines.append(f"  - {item}")
                            else:
                                output_lines.append(f"  {value}")
                        return "\n".join(output_lines)
                    else:
                        return "\n".join([f"  {k}: {v}" for k, v in result.items()])
                elif isinstance(result, list):
                    return "\n".join([str(item) for item in result])
                else:
                    return str(result)
        except Exception as e:
            self.logger.error(f"An error occurred during system health check: {e}")
            raise e

if __name__ == '__main__':
    print("Demonstrating SystemHealthCheckerTool functionality...")
    
    checker_tool = SystemHealthCheckerTool()
    
    try:
        # 1. Check CPU health
        print("\n--- Checking CPU Health ---")
        cpu_health = checker_tool.execute(operation="check_cpu_health", output_format="json")
        print(cpu_health)

        # 2. Check Memory health
        print("\n--- Checking Memory Health ---")
        memory_health = checker_tool.execute(operation="check_memory_health", output_format="text")
        print(memory_health)

        # 3. Check Network health
        print("\n--- Checking Network Health (pinging 8.8.8.8) ---")
        network_health = checker_tool.execute(operation="check_network_health", host="8.8.8.8", output_format="json")
        print(network_health)

        # 4. Run all checks
        print("\n--- Running All System Health Checks ---")
        all_checks_report = checker_tool.execute(operation="run_all_checks", output_format="text")
        print(all_checks_report)

    except Exception as e:
        print(f"\nAn error occurred: {e}")