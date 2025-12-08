import logging
from typing import Dict, Any, List
from collections import Counter
import json

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# A simple knowledge base of common molecules and their properties
MOLECULE_KNOWLEDGE_BASE = {
    "water": {
        "components": {"H": 2, "O": 1},
        "structure": "Bent (H-O-H)",
        "properties": {"state": "liquid", "polarity": "polar", "molecular_weight": 18.015}
    },
    "methane": {
        "components": {"C": 1, "H": 4},
        "structure": "Tetrahedral (CH4)",
        "properties": {"state": "gas", "flammability": "high", "molecular_weight": 16.04}
    },
    "carbon_dioxide": {
        "components": {"C": 1, "O": 2},
        "structure": "Linear (O=C=O)",
        "properties": {"state": "gas", "greenhouse_gas": True, "molecular_weight": 44.01}
    },
    "ammonia": {
        "components": {"N": 1, "H": 3},
        "structure": "Trigonal Pyramidal (NH3)",
        "properties": {"state": "gas", "odor": "pungent", "molecular_weight": 17.031}
    }
}

class MolecularAssemblerSimulatorTool(BaseTool):
    """
    A tool that simulates molecular assembly based on provided atomic components
    and instructions, predicting the resulting molecular structure and properties.
    """
    def __init__(self, tool_name: str = "MolecularAssemblerSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates molecular assembly from atomic components and predicts properties for common molecules."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "atomic_components": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of atomic components (e.g., ['H', 'H', 'O'] for water)."
                },
                "assembly_instructions": {"type": "string", "description": "Instructions for assembly (e.g., 'form water molecule')."}
            },
            "required": ["atomic_components", "assembly_instructions"]
        }

    def execute(self, atomic_components: List[str], assembly_instructions: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Simulates molecular assembly and predicts properties based on a rule-based knowledge base.
        """
        if not atomic_components or not assembly_instructions:
            raise ValueError("Atomic components and assembly instructions are required.")

        # Count available atoms
        available_atoms = Counter(atomic_components)
        
        # Normalize instructions for matching
        normalized_instructions = assembly_instructions.lower().replace("form ", "").replace(" molecule", "").strip()

        for mol_name, mol_data in MOLECULE_KNOWLEDGE_BASE.items():
            if normalized_instructions == mol_name.replace("_", " "):
                required_components = mol_data["components"]
                
                # Check if available atoms are sufficient
                sufficient = True
                for atom, count in required_components.items():
                    if available_atoms.get(atom, 0) < count:
                        sufficient = False
                        break
                
                if sufficient:
                    return {
                        "status": "success",
                        "assembled_molecule": mol_name.replace("_", " ").title(),
                        "predicted_structure": mol_data["structure"],
                        "predicted_properties": mol_data["properties"]
                    }
                else:
                    return {
                        "status": "failed",
                        "message": f"Insufficient atomic components to form {mol_name.replace('_', ' ')}. Required: {required_components}, Available: {dict(available_atoms)}."
                    }
        
        return {
            "status": "failed",
            "message": f"Could not understand assembly instructions '{assembly_instructions}' or molecule not in knowledge base."
        }

if __name__ == '__main__':
    print("Demonstrating MolecularAssemblerSimulatorTool functionality...")
    
    assembler_tool = MolecularAssemblerSimulatorTool()
    
    try:
        # 1. Assemble a water molecule
        print("\n--- Assembling a water molecule ---")
        result1 = assembler_tool.execute(atomic_components=["H", "H", "O"], assembly_instructions="form water molecule")
        print(json.dumps(result1, indent=2))

        # 2. Try to assemble methane with insufficient components
        print("\n--- Assembling methane with insufficient components ---")
        result2 = assembler_tool.execute(atomic_components=["C", "H", "H"], assembly_instructions="create methane molecule")
        print(json.dumps(result2, indent=2))
        
        # 3. Assemble carbon dioxide
        print("\n--- Assembling carbon dioxide ---")
        result3 = assembler_tool.execute(atomic_components=["C", "O", "O"], assembly_instructions="form carbon dioxide")
        print(json.dumps(result3, indent=2))

        # 4. Unknown molecule
        print("\n--- Assembling an unknown molecule ---")
        result4 = assembler_tool.execute(atomic_components=["X", "Y"], assembly_instructions="create unknown molecule")
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")