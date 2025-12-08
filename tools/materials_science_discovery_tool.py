import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simple atomic weights and properties for our model
ELEMENT_PROPERTIES = {
    'iron': {'atomic_weight': 55.8, 'base_strength': 5, 'base_density': 7.8},
    'carbon': {'atomic_weight': 12.0, 'base_strength': 50, 'base_density': 2.2},
    'chromium': {'atomic_weight': 52.0, 'base_strength': 20, 'base_density': 7.1},
    'aluminum': {'atomic_weight': 27.0, 'base_strength': 2, 'base_density': 2.7},
}

class MaterialPropertiesSimulatorTool(BaseTool):
    """
    A tool to simulate and predict material properties based on chemical
    composition using a formula-based model.
    """

    def __init__(self, tool_name: str = "MaterialSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "material_compositions.json")
        self.materials: Dict[str, Dict[str, Any]] = self._load_data(self.data_file, default={})

    @property
    def description(self) -> str:
        return "Predicts material properties based on its chemical composition."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_composition", "predict_properties", "validate_with_experimental_data"]},
                "material_id": {"type": "string"},
                "composition": {"type": "object", "description": "e.g., {'iron': 98, 'carbon': 2}"},
                "experimental_results": {"type": "object", "description": "e.g., {'strength_gpa': 1.5}"}
            },
            "required": ["operation", "material_id"]
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
        with open(self.data_file, 'w') as f: json.dump(self.materials, f, indent=4)

    def define_composition(self, material_id: str, composition: Dict[str, float]) -> Dict[str, Any]:
        """Defines a new material with its chemical composition."""
        if material_id in self.materials:
            raise ValueError(f"Material '{material_id}' already exists.")
        if sum(composition.values()) != 100:
            raise ValueError("Composition percentages must sum to 100.")
        
        new_material = {"material_id": material_id, "composition": composition, "predictions": {}}
        self.materials[material_id] = new_material
        self._save_data()
        return new_material

    def predict_properties(self, material_id: str) -> Dict[str, Any]:
        """Predicts material properties using a formula-based model."""
        material = self.materials.get(material_id)
        if not material: raise ValueError(f"Material '{material_id}' not found.")
        
        composition = material["composition"]
        predicted_strength = 0
        predicted_density = 0
        
        for element, percentage in composition.items():
            if element not in ELEMENT_PROPERTIES: continue
            props = ELEMENT_PROPERTIES[element]
            # Weighted average for properties
            predicted_strength += (percentage / 100) * props['base_strength']
            predicted_density += (percentage / 100) * props['base_density']
            
        predictions = {
            "strength_gpa": round(predicted_strength, 2),
            "density_g_cm3": round(predicted_density, 2)
        }
        material["predictions"] = predictions
        self._save_data()
        return predictions

    def validate_with_experimental_data(self, material_id: str, experimental_results: Dict[str, float]) -> Dict[str, Any]:
        """Compares predicted properties with experimental results."""
        material = self.materials.get(material_id)
        if not material or not material.get("predictions"):
            raise ValueError(f"Predictions for material '{material_id}' not found. Run prediction first.")
        
        predicted = material["predictions"]
        validation_report = {"errors": {}}
        
        for prop, exp_value in experimental_results.items():
            if prop in predicted:
                pred_value = predicted[prop]
                error = abs(pred_value - exp_value) / exp_value * 100 if exp_value != 0 else 0
                validation_report["errors"][prop] = f"{round(error, 2)}%"
        
        return validation_report

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "define_composition": self.define_composition,
            "predict_properties": self.predict_properties,
            "validate_with_experimental_data": self.validate_with_experimental_data
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MaterialPropertiesSimulatorTool functionality...")
    temp_dir = "temp_material_simulator_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    simulator_tool = MaterialPropertiesSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a material's composition
        print("\n--- Defining a new steel alloy ---")
        steel_comp = {'iron': 98.5, 'carbon': 1.5}
        simulator_tool.execute(operation="define_composition", material_id="steel_101", composition=steel_comp)
        print("Steel alloy 'steel_101' defined.")

        # 2. Predict its properties based on the composition
        print("\n--- Predicting properties for 'steel_101' ---")
        predicted_props = simulator_tool.execute(operation="predict_properties", material_id="steel_101")
        print(json.dumps(predicted_props, indent=2))

        # 3. Validate the prediction with some "experimental" data
        print("\n--- Validating prediction with experimental results ---")
        exp_data = {"strength_gpa": 50.0, "density_g_cm3": 7.8}
        validation = simulator_tool.execute(
            operation="validate_with_experimental_data", 
            material_id="steel_101", 
            experimental_results=exp_data
        )
        print("Validation Report (prediction error %):")
        print(json.dumps(validation, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")