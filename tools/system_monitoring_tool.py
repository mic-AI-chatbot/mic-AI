import psutil
import json
import logging
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool
import datetime

logger = logging.getLogger(__name__)

class SystemMonitoringTool(BaseTool):
    """
    A tool for monitoring various system resources.
    """

    def __init__(self, tool_name: str = "system_monitoring_tool"):
        super().__init__(tool_name)

    def _get_cpu_memory_usage(self) -> Dict[str, Any]:
        """
        Provides a snapshot of the current system CPU and memory usage.
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_info.percent,
            "memory_available_mb": round(memory_info.available / (1024**2), 2)
        }

    def _get_disk_usage(self) -> List[Dict[str, Any]]:
        """
        Provides disk usage information for all mounted partitions.
        """
        disk_partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_partitions.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
            except Exception as e:
                self.logger.error(f"Could not get disk usage for {partition.mountpoint}: {e}")
        return disk_partitions

    def _get_network_stats(self) -> Dict[str, Any]:
        """
        Provides network I/O statistics.
        """
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }

    def _get_process_list(self) -> List[Dict[str, Any]]:
        """
        Lists basic information about all running processes.
        """
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes

    def _get_system_uptime(self) -> str:
        """
        Returns the system uptime.
        """
        boot_time_timestamp = psutil.boot_time()
        boot_time_datetime = datetime.datetime.fromtimestamp(boot_time_timestamp)
        now = datetime.datetime.now()
        uptime = now - boot_time_datetime
        return str(uptime)

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["cpu_memory_usage", "disk_usage", "network_stats", "process_list", "system_uptime"]},
                "output_format": {"type": "string", "enum": ["text", "json"], "default": "text"}
            },
            "required": ["operation"]
        }

    def execute(self, operation: str, output_format: str = "text", **kwargs: Any) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        operation = operation.lower()
        result = {}

        try:
            if operation == "cpu_memory_usage":
                result = self._get_cpu_memory_usage()
            elif operation == "disk_usage":
                result = self._get_disk_usage()
            elif operation == "network_stats":
                result = self._get_network_stats()
            elif operation == "process_list":
                result = self._get_process_list()
            elif operation == "system_uptime":
                result = self._get_system_uptime()
            else:
                raise ValueError(f"Invalid operation '{operation}'. Supported operations are 'cpu_memory_usage', 'disk_usage', 'network_stats', 'process_list', 'system_uptime'.")

            if output_format == "json":
                return json.dumps(result, indent=2)
            else: # text format
                if isinstance(result, dict):
                    return "\n".join([f"  {k}: {v}" for k, v in result.items()])
                elif isinstance(result, list):
                    return "\n".join([str(item) for item in result])
                else:
                    return str(result)
        except Exception as e:
            self.logger.error(f"An error occurred during system monitoring: {e}")
            raise e

if __name__ == '__main__':
    print("Demonstrating SystemMonitoringTool functionality...")
    
    checker_tool = SystemMonitoringTool()
    
    try:
        # 1. Check CPU health
        print("\n--- Checking CPU Health ---")
        cpu_health = checker_tool.execute(operation="cpu_memory_usage", output_format="json")
        print(cpu_health)

        # 2. Check Memory health
        print("\n--- Checking Memory Health ---")
        memory_health = checker_tool.execute(operation="cpu_memory_usage", output_format="text")
        print(memory_health)

        # 3. Check Network health
        print("\n--- Checking Network Health ---")
        network_health = checker_tool.execute(operation="network_stats", output_format="json")
        print(network_health)

        # 4. Get process list
        print("\n--- Getting Process List ---")
        process_list = checker_tool.execute(operation="process_list", output_format="text")
        print(process_list)

        # 5. Get system uptime
        print("\n--- Getting System Uptime ---")
        uptime = checker_tool.execute(operation="system_uptime", output_format="text")
        print(uptime)

    except Exception as e:
        print(f"\nAn error occurred: {e}")