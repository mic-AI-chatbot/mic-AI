import logging
import os
import shutil
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataReplicationTool(BaseTool):
    """
    A tool for simulating data replication processes.
    """

    def __init__(self, tool_name: str = "data_replication_tool"):
        super().__init__(tool_name)
        self.replications_file = "data_replications.json"
        self.replications: Dict[str, Dict[str, Any]] = self._load_replications()

    @property
    def description(self) -> str:
        return "Simulates data replication processes, including starting, stopping, and monitoring status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The replication operation to perform.",
                    "enum": ["start_replication", "get_replication_status", "list_replications", "stop_replication"]
                },
                "replication_id": {"type": "string"},
                "source_path": {"type": "string", "description": "Absolute path to the source directory or file."},
                "target_path": {"type": "string", "description": "Absolute path to the target directory."},
                "replication_type": {"type": "string", "enum": ["full", "incremental"], "default": "full"}
            },
            "required": ["operation"]
        }

    def _load_replications(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.replications_file):
            with open(self.replications_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted replications file '{self.replications_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_replications(self) -> None:
        with open(self.replications_file, 'w') as f:
            json.dump(self.replications, f, indent=4)

    def _start_replication(self, replication_id: str, source_path: str, target_path: str, replication_type: str = "full") -> Dict[str, Any]:
        if not os.path.isabs(source_path) or not os.path.isabs(target_path):
            raise ValueError("Source and target paths must be absolute paths.")
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source '{source_path}' not found.")
        if replication_id in self.replications:
            raise ValueError(f"Replication with ID '{replication_id}' already exists.")

        os.makedirs(target_path, exist_ok=True)

        replication_record = {
            "replication_id": replication_id, "source_path": source_path, "target_path": target_path,
            "replication_type": replication_type, "status": "in_progress", "started_at": datetime.now().isoformat(),
            "completed_at": None, "files_replicated": 0, "total_files_in_source": 0, "errors": []
        }
        self.replications[replication_id] = replication_record
        self._save_replications()

        try:
            if os.path.isfile(source_path):
                shutil.copy2(source_path, target_path)
                replication_record["files_replicated"] = 1
                replication_record["total_files_in_source"] = 1
            elif os.path.isdir(source_path):
                source_files = [f for f in os.listdir(source_path) if os.path.isfile(os.path.join(source_path, f))]
                replication_record["total_files_in_source"] = len(source_files)

                for item in source_files:
                    s = os.path.join(source_path, item)
                    d = os.path.join(target_path, item)
                    
                    if replication_type == "full":
                        shutil.copy2(s, d)
                        replication_record["files_replicated"] += 1
                    elif replication_type == "incremental":
                        if not os.path.exists(d) or os.path.getmtime(s) > os.path.getmtime(d):
                            shutil.copy2(s, d)
                            replication_record["files_replicated"] += 1
                    else:
                        raise ValueError(f"Unsupported replication type: {replication_type}")
            
            replication_record["status"] = "completed"
            replication_record["completed_at"] = datetime.now().isoformat()
        except Exception as e:
            replication_record["status"] = "failed"
            replication_record["errors"].append(str(e))
        finally:
            self._save_replications()
        
        return replication_record

    def _get_replication_status(self, replication_id: str) -> Optional[Dict[str, Any]]:
        return self.replications.get(replication_id)

    def _list_replications(self) -> List[Dict[str, Any]]:
        return list(self.replications.values())

    def _stop_replication(self, replication_id: str) -> Dict[str, Any]:
        replication = self.replications.get(replication_id)
        if not replication: raise ValueError(f"Replication '{replication_id}' not found.")
        
        if replication["status"] == "in_progress":
            replication["status"] = "stopped"
            replication["completed_at"] = datetime.now().isoformat()
            self._save_replications()
        else:
            logger.warning(f"Replication '{replication_id}' is not in 'in_progress' state, cannot stop.")
        
        return replication

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "start_replication":
            return self._start_replication(kwargs.get("replication_id"), kwargs.get("source_path"), kwargs.get("target_path"), kwargs.get("replication_type", "full"))
        elif operation == "get_replication_status":
            return self._get_replication_status(kwargs.get("replication_id"))
        elif operation == "list_replications":
            return self._list_replications()
        elif operation == "stop_replication":
            return self._stop_replication(kwargs.get("replication_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataReplicationTool functionality...")
    tool = DataReplicationTool()
    
    source_dir = os.path.abspath("source_data_rep")
    target_dir = os.path.abspath("target_data_rep")
    
    try:
        os.makedirs(source_dir, exist_ok=True)
        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(source_dir, "file_a.txt"), "w") as f: f.write("content A")

        print("\n--- Starting Full Replication ---")
        replication_result = tool.execute(operation="start_replication", replication_id="rep_001", source_path=source_dir, target_path=target_dir, replication_type="full")
        print(json.dumps(replication_result, indent=2))

        print("\n--- Getting Replication Status ---")
        status = tool.execute(operation="get_replication_status", replication_id="rep_001")
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(source_dir): shutil.rmtree(source_dir)
        if os.path.exists(target_dir): shutil.rmtree(target_dir)
        if os.path.exists(tool.replications_file): os.remove(tool.replications_file)
        print("\nCleanup complete.")