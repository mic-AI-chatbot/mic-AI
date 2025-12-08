import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataLineageTrackerTool(BaseTool):
    """
    A tool for tracking and visualizing data lineage.
    """

    def __init__(self, tool_name: str = "data_lineage_tracker"):
        super().__init__(tool_name)
        self.lineage_file = "data_lineage.json"
        self.lineage_data: Dict[str, List[Dict[str, Any]]] = self._load_lineage()
        if "transformations" not in self.lineage_data:
            self.lineage_data["transformations"] = []

    @property
    def description(self) -> str:
        return "Tracks data transformations and allows querying upstream/downstream lineage, and visualizing lineage graphs."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The lineage operation to perform.",
                    "enum": ["record_transformation", "get_lineage", "list_all_transformations", "visualize_lineage"]
                },
                "source_asset": {"type": "string"},
                "target_asset": {"type": "string"},
                "transformation_details": {"type": "object"},
                "asset_name": {"type": "string"},
                "direction": {"type": "string", "enum": ["upstream", "downstream"]},
                "output_file": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_lineage(self) -> Dict[str, List[Dict[str, Any]]]:
        if os.path.exists(self.lineage_file):
            with open(self.lineage_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted lineage file '{self.lineage_file}'. Starting fresh.")
                    return {"transformations": []}
        return {"transformations": []}

    def _save_lineage(self) -> None:
        with open(self.lineage_file, 'w') as f:
            json.dump(self.lineage_data, f, indent=4)

    def _record_transformation(self, source_asset: str, target_asset: str, transformation_details: Dict[str, Any]) -> Dict[str, Any]:
        if not all([source_asset, target_asset, transformation_details]):
            raise ValueError("Source asset, target asset, and transformation details cannot be empty.")

        transformation_id = f"TRANS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_transformation = {
            "transformation_id": transformation_id, "source_asset": source_asset, "target_asset": target_asset,
            "details": transformation_details, "recorded_at": datetime.now().isoformat()
        }
        self.lineage_data["transformations"].append(new_transformation)
        self._save_lineage()
        return new_transformation

    def _get_lineage(self, asset_name: str, direction: str = "downstream") -> List[Dict[str, Any]]:
        if direction not in ["upstream", "downstream"]:
            raise ValueError("Direction must be 'upstream' or 'downstream'.")

        relevant_transformations = []
        for trans in self.lineage_data["transformations"]:
            if direction == "downstream" and trans["source_asset"] == asset_name:
                relevant_transformations.append(trans)
            elif direction == "upstream" and trans["target_asset"] == asset_name:
                relevant_transformations.append(trans)
        return relevant_transformations

    def _visualize_lineage(self, asset_name: str, direction: str = "downstream", output_file: str = "lineage_graph.json") -> str:
        if direction not in ["upstream", "downstream"]:
            raise ValueError("Direction must be 'upstream' or 'downstream'.")

        nodes = set()
        edges = []
        nodes.add(asset_name)
        relevant_transformations = self._get_lineage(asset_name, direction)

        for trans in relevant_transformations:
            nodes.add(trans["source_asset"])
            nodes.add(trans["target_asset"])
            edges.append({
                "source": trans["source_asset"], "target": trans["target_asset"],
                "transformation_id": trans["transformation_id"], "details": trans["details"]
            })
        
        graph_data = {"nodes": [{"id": node} for node in sorted(list(nodes))], "edges": edges}
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=4)
        return f"Simulated lineage graph saved to '{output_file}'."

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "record_transformation":
            return self._record_transformation(kwargs.get("source_asset"), kwargs.get("target_asset"), kwargs.get("transformation_details"))
        elif operation == "get_lineage":
            return self._get_lineage(kwargs.get("asset_name"), kwargs.get("direction", "downstream"))
        elif operation == "list_all_transformations":
            return self.lineage_data["transformations"]
        elif operation == "visualize_lineage":
            return self._visualize_lineage(kwargs.get("asset_name"), kwargs.get("direction", "downstream"), kwargs.get("output_file", "lineage_graph.json"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataLineageTrackerTool functionality...")
    tool = DataLineageTrackerTool()
    
    output_graph_file = "lineage_graph.json"

    try:
        print("\n--- Recording Transformations ---")
        tool.execute(operation="record_transformation", source_asset="raw_data", target_asset="cleaned_data", transformation_details={"type": "ETL"})
        tool.execute(operation="record_transformation", source_asset="cleaned_data", target_asset="report_data", transformation_details={"type": "Aggregation"})
        
        print("\n--- Getting Downstream Lineage for 'raw_data' ---")
        downstream = tool.execute(operation="get_lineage", asset_name="raw_data", direction="downstream")
        print(json.dumps(downstream, indent=2))

        print("\n--- Visualizing Lineage for 'cleaned_data' ---")
        message = tool.execute(operation="visualize_lineage", asset_name="cleaned_data", output_file=output_graph_file)
        print(message)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.lineage_file): os.remove(tool.lineage_file)
        if os.path.exists(output_graph_file): os.remove(output_graph_file)
        print("\nCleanup complete.")