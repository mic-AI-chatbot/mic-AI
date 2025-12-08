
import logging
import os
from typing import Dict, Any, List
import networkx as nx
import matplotlib.pyplot as plt

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MicroserviceDependencyVisualizerTool(BaseTool):
    """
    A tool to visualize the dependency graph of a microservice architecture
    and save it as an image.
    """

    def __init__(self, tool_name: str = "MicroserviceDependencyVisualizer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.output_dir = os.path.join(data_dir, "visualizations")
        os.makedirs(self.output_dir, exist_ok=True)

    @property
    def description(self) -> str:
        return "Generates a dependency graph visualization for a microservice architecture."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "services": {
                    "type": "array",
                    "description": "A list of service dictionaries, each with 'name' and 'dependencies'.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dependencies": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["name", "dependencies"]
                    }
                },
                "output_filename": {"type": "string", "description": "The filename for the output graph image (e.g., 'architecture.png')."}
            },
            "required": ["services", "output_filename"]
        }

    def execute(self, services: List[Dict[str, Any]], output_filename: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Builds and saves a dependency graph visualization from a list of services.
        """
        if not services:
            raise ValueError("The 'services' list cannot be empty.")
        if not output_filename:
            raise ValueError("The 'output_filename' cannot be empty.")

        graph = nx.DiGraph()

        # Add nodes
        for service in services:
            graph.add_node(service["name"])

        # Add edges
        for service in services:
            for dependency in service.get("dependencies", []):
                if graph.has_node(dependency):
                    graph.add_edge(service["name"], dependency)
                else:
                    logger.warning(f"Dependency '{dependency}' for service '{service['name']}' not found as a defined service. It will be missed from the graph.")

        # Create visualization
        plt.figure(figsize=(12, 12))
        pos = nx.spring_layout(graph, k=0.9, iterations=50)
        
        nx.draw(graph, pos, with_labels=True, node_size=3000, node_color="skyblue",
                font_size=10, font_weight="bold", arrows=True, arrowstyle="->",
                arrowsize=20, edge_color="gray", width=1.5)
        
        plt.title("Microservice Dependency Graph", size=15)

        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            plt.savefig(output_path, format="png", bbox_inches="tight")
            plt.close()
            logger.info(f"Dependency graph saved to {output_path}")
            return {"status": "success", "graph_image_path": output_path}
        except Exception as e:
            logger.error(f"Failed to save graph image: {e}")
            plt.close()
            raise

if __name__ == '__main__':
    print("Demonstrating MicroserviceDependencyVisualizerTool functionality...")
    temp_dir = "temp_microservice_viz"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    visualizer_tool = MicroserviceDependencyVisualizerTool(data_dir=temp_dir)
    
    # Define a sample microservice architecture
    architecture = [
        {"name": "api-gateway", "dependencies": ["auth-service", "order-service", "product-service"]},
        {"name": "auth-service", "dependencies": ["user-db"]},
        {"name": "order-service", "dependencies": ["auth-service", "product-service", "order-db"]},
        {"name": "product-service", "dependencies": ["product-db"]},
        {"name": "user-db", "dependencies": []},
        {"name": "order-db", "dependencies": []},
        {"name": "product-db", "dependencies": []}
    ]
    
    try:
        print("\n--- Generating dependency graph ---")
        result = visualizer_tool.execute(services=architecture, output_filename="service_dependencies.png")
        
        if os.path.exists(result["graph_image_path"]):
            print(f"Success! Graph image created at: {result['graph_image_path']}")
        else:
            print("Error: Graph image file was not created.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
