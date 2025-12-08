import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalCognitiveModelSimulatorTool(BaseTool):
    """
    A tool that simulates a personal cognitive model, capable of storing,
    querying, and simulating learning from knowledge with persistence.
    """

    def __init__(self, tool_name: str = "PersonalCognitiveModelSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.knowledge_file = os.path.join(self.data_dir, "cognitive_knowledge_base.json")
        # Knowledge base structure: {fact_id: {fact: str, confidence: float, source: str, created_at: str}}
        self.knowledge_base: Dict[str, Dict[str, Any]] = self._load_data(self.knowledge_file, default={})

    @property
    def description(self) -> str:
        return "Simulates a personal cognitive model: stores, queries, and learns from knowledge."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_knowledge", "query_knowledge", "simulate_learning", "forget_knowledge"]},
                "fact_id": {"type": "string"},
                "fact": {"type": "string", "description": "The piece of knowledge to add."},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.5},
                "source": {"type": "string", "description": "The source of the knowledge."},
                "query": {"type": "string", "description": "The query to search for in the knowledge base."},
                "new_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
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
        with open(self.knowledge_file, 'w') as f: json.dump(self.knowledge_base, f, indent=2)

    def add_knowledge(self, fact_id: str, fact: str, confidence: float = 0.5, source: str = "user_input") -> Dict[str, Any]:
        """Adds a piece of knowledge to the cognitive model."""
        if fact_id in self.knowledge_base: raise ValueError(f"Fact ID '{fact_id}' already exists. Use 'simulate_learning' to modify.")
        
        new_fact = {
            "fact": fact, "confidence": confidence, "source": source,
            "created_at": datetime.now().isoformat()
        }
        self.knowledge_base[fact_id] = new_fact
        self._save_data()
        return {"status": "success", "message": f"Knowledge '{fact_id}' added."}

    def query_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Queries the cognitive model for information related to the query."""
        if not self.knowledge_base: return {"status": "info", "message": "Cognitive model is empty. Add some knowledge first."}
        
        matching_facts = []
        query_lower = query.lower()
        for fact_id, fact_info in self.knowledge_base.items():
            if query_lower in fact_info["fact"].lower():
                matching_facts.append({"fact_id": fact_id, "fact": fact_info["fact"], "confidence": fact_info["confidence"]})
        
        return matching_facts

    def simulate_learning(self, fact_id: str, new_confidence: float, new_source: Optional[str] = None) -> Dict[str, Any]:
        """Simulates the model 'learning' by updating confidence in a fact."""
        fact_info = self.knowledge_base.get(fact_id)
        if not fact_info: raise ValueError(f"Fact ID '{fact_id}' not found.")
        
        old_confidence = fact_info["confidence"]
        fact_info["confidence"] = new_confidence
        if new_source: fact_info["source"] = new_source
        fact_info["last_learned_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Confidence for '{fact_id}' updated from {old_confidence:.2f} to {new_confidence:.2f}."}

    def forget_knowledge(self, fact_id: str) -> Dict[str, Any]:
        """Simulates forgetting a piece of knowledge."""
        if fact_id not in self.knowledge_base: raise ValueError(f"Fact ID '{fact_id}' not found.")
        
        del self.knowledge_base[fact_id]
        self._save_data()
        return {"status": "success", "message": f"Knowledge '{fact_id}' forgotten."}

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "add_knowledge": self.add_knowledge,
            "query_knowledge": self.query_knowledge,
            "simulate_learning": self.simulate_learning,
            "forget_knowledge": self.forget_knowledge
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating PersonalCognitiveModelSimulatorTool functionality...")
    temp_dir = "temp_cognitive_model_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    cognitive_model = PersonalCognitiveModelSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add some knowledge
        print("\n--- Adding knowledge ---")
        cognitive_model.execute(operation="add_knowledge", fact_id="fact_001", fact="The sky is blue.", confidence=0.8)
        cognitive_model.execute(operation="add_knowledge", fact_id="fact_002", fact="Water boils at 100 degrees Celsius.", confidence=0.95, source="science textbook")
        print("Knowledge added.")

        # 2. Query knowledge
        print("\n--- Querying for 'blue' ---")
        query_result = cognitive_model.execute(operation="query_knowledge", query="blue")
        print(json.dumps(query_result, indent=2))

        # 3. Simulate learning (update confidence)
        print("\n--- Simulating learning for 'fact_001' ---")
        cognitive_model.execute(operation="simulate_learning", fact_id="fact_001", new_confidence=0.99, new_source="personal observation")
        print("Confidence updated.")

        # 4. Query again to see updated confidence
        print("\n--- Querying for 'blue' again ---")
        query_result_updated = cognitive_model.execute(operation="query_knowledge", query="blue")
        print(json.dumps(query_result_updated, indent=2))

        # 5. Simulate forgetting
        print("\n--- Forgetting 'fact_002' ---")
        cognitive_model.execute(operation="forget_knowledge", fact_id="fact_002")
        print("Knowledge forgotten.")

        # 6. Query for forgotten fact
        print("\n--- Querying for 'water' (should not find fact_002) ---")
        query_result_forgotten = cognitive_model.execute(operation="query_knowledge", query="water")
        print(json.dumps(query_result_forgotten, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")