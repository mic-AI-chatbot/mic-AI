import logging
import json
import random
import networkx as nx
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ProcessModel:
    """Represents a business process model as a directed graph using NetworkX."""
    def __init__(self, model_name: str, steps: List[str], transitions: List[Dict[str, str]]):
        self.model_name = model_name
        self.steps = steps
        self.transitions = transitions
        self.graph = nx.DiGraph()
        self._build_graph()

    def _build_graph(self):
        self.graph.add_nodes_from(self.steps)
        for t in self.transitions:
            if t["from"] in self.steps and t["to"] in self.steps:
                self.graph.add_edge(t["from"], t["to"])
            else:
                logging.warning(f"Invalid transition: '{t['from']}' or '{t['to']}' not in defined steps for model '{self.model_name}'.")

    def validate(self) -> Dict[str, Any]:
        issues = []
        
        # Check if all steps are reachable from a (simulated) start node
        # Assuming the first step in the list is the start node
        if self.steps:
            start_node = self.steps[0]
            if not nx.is_connected(self.graph.to_undirected()):
                issues.append("The process graph is not fully connected. Some steps might be isolated.")
            
            # Check for unreachable nodes from the start node
            reachable_nodes = nx.descendants(self.graph, start_node) | {start_node}
            unreachable_nodes = set(self.steps) - reachable_nodes
            if unreachable_nodes:
                issues.append(f"The following steps are unreachable from the start: {', '.join(unreachable_nodes)}.")

        # Check for cycles (potential infinite loops)
        if list(nx.simple_cycles(self.graph)):
            issues.append("Cycles detected in the process. This might indicate infinite loops or require explicit loop conditions.")
        
        # Check for dead ends (nodes with no outgoing transitions, not being an end node)
        end_nodes = [node for node in self.graph.nodes if self.graph.out_degree(node) == 0]
        if not end_nodes and self.steps:
            issues.append("No clear end nodes detected. The process might not have a defined completion point.")
        
        return {"is_valid": not issues, "issues": issues}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "steps": self.steps,
            "transitions": self.transitions,
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges()
        }

class ModelManager:
    """Manages all created business process models, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance.models: Dict[str, ProcessModel] = {}
        return cls._instance

    def create_model(self, model_name: str, steps: List[str], transitions: List[Dict[str, str]]) -> ProcessModel:
        model = ProcessModel(model_name, steps, transitions)
        self.models[model_name] = model
        return model

    def get_model(self, model_name: str) -> ProcessModel:
        return self.models.get(model_name)

model_manager = ModelManager()

class CreateBusinessProcessModelTool(BaseTool):
    """Creates a new business process model based on steps and transitions."""
    def __init__(self, tool_name="create_business_process_model"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new business process model with a specified name, a list of steps, and transitions between them."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model_name": {"type": "string", "description": "A unique name for the business process model."},
                "steps": {"type": "array", "items": {"type": "string"}, "description": "A list of unique step names in the process."},
                "transitions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "from": {"type": "string", "description": "The source step of the transition."},
                            "to": {"type": "string", "description": "The target step of the transition."}
                        },
                        "required": ["from", "to"]
                    },
                    "description": "A list of transitions, each specifying a 'from' step and a 'to' step."
                }
            },
            "required": ["model_name", "steps", "transitions"]
        }

    def execute(self, model_name: str, steps: List[str], transitions: List[Dict[str, str]], **kwargs: Any) -> str:
        if model_name in model_manager.models:
            return json.dumps({"error": f"Business process model '{model_name}' already exists. Please choose a unique name."})