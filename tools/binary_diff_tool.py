import logging
import json
import random
import os
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class BinaryDiffManager:
    """Manages the storage of binary diff reports, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BinaryDiffManager, cls).__new__(cls)
            cls._instance.diff_reports: Dict[str, Any] = {}
        return cls._instance

    def add_report(self, diff_id: str, report: Dict[str, Any]):
        self.diff_reports[diff_id] = report

    def get_report(self, diff_id: str) -> Dict[str, Any]:
        return self.diff_reports.get(diff_id)

diff_manager = BinaryDiffManager()

class GenerateMockBinaryFileTool(BaseTool):
    """Generates mock binary files for testing purposes."""
    def __init__(self, tool_name="generate_mock_binary_file"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates two mock binary files, one of which can be a slightly modified version of the other, for testing binary comparison."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file1_path": {"type": "string", "description": "The absolute path for the first mock binary file."},
                "file2_path": {"type": "string", "description": "The absolute path for the second mock binary file."},
                "size_bytes": {"type": "integer", "description": "The size of the files in bytes.", "default": 1024},
                "num_differences": {"type": "integer", "description": "The number of bytes to randomly change in file2 to create differences.", "default": 5}
            },
            "required": ["file1_path", "file2_path"]
        }

    def execute(self, file1_path: str, file2_path: str, size_bytes: int = 1024, num_differences: int = 5, **kwargs: Any) -> str:
        try:
            # Ensure output directories exist
            os.makedirs(os.path.dirname(file1_path), exist_ok=True)
            os.makedirs(os.path.dirname(file2_path), exist_ok=True)

            # Generate random bytes for file1
            file1_content = bytearray(random.getrandbits(8) for _ in range(size_bytes))  # nosec B311
            
            # Create file2 as a copy of file1
            file2_content = bytearray(file1_content)
            
            # Introduce random differences in file2
            for _ in range(num_differences):
                if size_bytes > 0:
                    offset = random.randint(0, size_bytes - 1)  # nosec B311
                    file2_content[offset] = random.getrandbits(8) # Change a byte  # nosec B311
            
            with open(file1_path, "wb") as f:
                f.write(file1_content)
            with open(file2_path, "wb") as f:
                f.write(file2_content)
            
            report = {
                "message": f"Mock binary files generated: '{os.path.abspath(file1_path)}' and '{os.path.abspath(file2_path)}'.",
                "file1_path": os.path.abspath(file1_path),
                "file2_path": os.path.abspath(file2_path),
                "file_size_bytes": size_bytes,
                "simulated_differences_count": num_differences
            }
            return json.dumps(report, indent=2)
        except Exception as e:
            logger.error(f"Failed to generate mock binary files: {e}")
            return json.dumps({"error": f"Failed to generate mock binary files: {e}"})

class CompareBinariesTool(BaseTool):
    """Compares two binary files byte by byte and generates a detailed diff report."""
    def __init__(self, tool_name="compare_binaries"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Compares two binary files byte by byte and generates a detailed diff report, highlighting the number and locations of differences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file1_path": {"type": "string", "description": "The absolute path to the first binary file."},
                "file2_path": {"type": "string", "description": "The absolute path to the second binary file."}
            },
            "required": ["file1_path", "file2_path"]
        }

    def execute(self, file1_path: str, file2_path: str, **kwargs: Any) -> str:
        if not os.path.exists(file1_path):
            return json.dumps({"error": f"File not found at '{file1_path}'."})
        if not os.path.exists(file2_path):
            return json.dumps({"error": f"File not found at '{file2_path}'."})

        differences = []
        try:
            with open(file1_path, "rb") as f1, open(file2_path, "rb") as f2:
                offset = 0
                while True:
                    byte1 = f1.read(1)
                    byte2 = f2.read(1)

                    if not byte1 and not byte2: # End of both files
                        break
                    
                    if byte1 != byte2:
                        differences.append({
                            "offset": offset,
                            "file1_byte": byte1.hex() if byte1 else "EOF",
                            "file2_byte": byte2.hex() if byte2 else "EOF"
                        })
                    offset += 1
        except Exception as e:
            logger.error(f"Error comparing files '{file1_path}' and '{file2_path}': {e}")
            return json.dumps({"error": f"Error comparing files: {e}"})

        diff_id = f"diff_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}"  # nosec B311
        
        report = {
            "diff_report_id": diff_id,
            "file1_path": os.path.abspath(file1_path),
            "file2_path": os.path.abspath(file2_path),
            "num_differences": len(differences),
            "summary": f"Found {len(differences)} differences between '{os.path.basename(file1_path)}' and '{os.path.basename(file2_path)}'.",
            "details_sample": differences[:10], # Show first 10 differences for brevity
            "timestamp": datetime.now().isoformat()
        }
        diff_manager.add_report(diff_id, report)
        
        return json.dumps({"message": f"Binary comparison completed. Diff Report ID: '{diff_id}'.", "diff_report_id": diff_id}, indent=2)

class GetBinaryDiffReportTool(BaseTool):
    """Retrieves a previously generated binary diff report."""
    def __init__(self, tool_name="get_binary_diff_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves a previously generated binary diff report using its unique ID."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"diff_id": {"type": "string", "description": "The ID of the diff report to retrieve."}},
            "required": ["diff_id"]
        }

    def execute(self, diff_id: str, **kwargs: Any) -> str:
        report = diff_manager.get_report(diff_id)
        if not report:
            return json.dumps({"error": f"Diff report with ID '{diff_id}' not found."})
            
        return json.dumps(report, indent=2)