
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PlantDiseaseDetectorSimulatorTool(BaseTool):
    """
    A tool that simulates plant disease detection based on image paths
    and predefined disease symptoms, suggesting treatments.
    """

    def __init__(self, tool_name: str = "PlantDiseaseDetectorSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.diseases_file = os.path.join(self.data_dir, "disease_definitions.json")
        self.history_file = os.path.join(self.data_dir, "detection_history.json")
        
        # Disease definitions: {disease_id: {name: ..., plant_type: ..., symptoms: [], treatment: ...}}
        self.disease_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.diseases_file, default={})
        # Detection history: {plant_id: [{detection_id: ..., disease: ..., confidence: ...}]}
        self.detection_history: Dict[str, List[Dict[str, Any]]] = self._load_data(self.history_file, default={})

    @property
    def description(self) -> str:
        return "Simulates plant disease detection: defines diseases, detects from images, and suggests treatments."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_disease", "detect_disease", "get_detection_history"]},
                "disease_id": {"type": "string"},
                "name": {"type": "string"},
                "plant_type": {"type": "string"},
                "symptoms": {"type": "array", "items": {"type": "string"}},
                "treatment": {"type": "string"},
                "image_path": {"type": "string", "description": "Simulated image path (e.g., 'tomato_yellow_leaves.jpg')."},
                "plant_id": {"type": "string", "description": "ID of the plant being inspected."}
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

    def _save_diseases(self):
        with open(self.diseases_file, 'w') as f: json.dump(self.disease_definitions, f, indent=2)

    def _save_history(self):
        with open(self.history_file, 'w') as f: json.dump(self.detection_history, f, indent=2)

    def define_disease(self, disease_id: str, name: str, plant_type: str, symptoms: List[str], treatment: str) -> Dict[str, Any]:
        """Defines a new plant disease."""
        if disease_id in self.disease_definitions: raise ValueError(f"Disease '{disease_id}' already exists.")
        
        new_disease = {
            "id": disease_id, "name": name, "plant_type": plant_type.lower(),
            "symptoms": [s.lower() for s in symptoms], "treatment": treatment,
            "defined_at": datetime.now().isoformat()
        }
        self.disease_definitions[disease_id] = new_disease
        self._save_diseases()
        return new_disease

    def detect_disease(self, image_path: str, plant_type: str, plant_id: str) -> Dict[str, Any]:
        """Simulates detecting a disease from an image path."""
        # Simulate extracting symptoms from the image path
        filename = os.path.basename(image_path).lower()
        simulated_symptoms = []
        if "yellow_leaves" in filename: simulated_symptoms.append("yellow_leaves")
        if "spots" in filename: simulated_symptoms.append("spots")
        if "wilting" in filename: simulated_symptoms.append("wilting")
        
        detected_disease = None
        confidence = 0.0
        
        for disease_id, disease_data in self.disease_definitions.items():
            if disease_data["plant_type"] == plant_type.lower():
                match_count = sum(1 for s in simulated_symptoms if s in disease_data["symptoms"])
                if match_count > 0:
                    # Simple confidence: higher match count means higher confidence
                    current_confidence = match_count / len(disease_data["symptoms"])
                    if current_confidence > confidence:
                        confidence = current_confidence
                        detected_disease = disease_data
        
        detection_id = f"det_{plant_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        result = {
            "detection_id": detection_id, "plant_id": plant_id, "image_path": image_path,
            "detected_disease": detected_disease["name"] if detected_disease else "No disease detected",
            "confidence": round(confidence, 2),
            "treatment_suggestion": detected_disease["treatment"] if detected_disease else "Monitor plant health.",
            "detected_at": datetime.now().isoformat()
        }
        
        self.detection_history.setdefault(plant_id, []).append(result)
        self._save_history()
        return result

    def get_detection_history(self, plant_id: str) -> List[Dict[str, Any]]:
        """Retrieves the disease detection history for a specific plant."""
        history = self.detection_history.get(plant_id, [])
        if not history:
            return {"status": "info", "message": f"No detection history found for plant '{plant_id}'."}
        return history

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_disease":
            return self.define_disease(kwargs['disease_id'], kwargs['name'], kwargs['plant_type'], kwargs['symptoms'], kwargs['treatment'])
        elif operation == "detect_disease":
            return self.detect_disease(kwargs['image_path'], kwargs['plant_type'], kwargs['plant_id'])
        elif operation == "get_detection_history":
            return self.get_detection_history(kwargs['plant_id'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PlantDiseaseDetectorSimulatorTool functionality...")
    temp_dir = "temp_plant_disease_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    detector_tool = PlantDiseaseDetectorSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define some diseases
        print("\n--- Defining plant diseases ---")
        detector_tool.execute(operation="define_disease", disease_id="early_blight", name="Early Blight", plant_type="tomato", symptoms=["brown_spots", "yellow_leaves"], treatment="Fungicide application")
        detector_tool.execute(operation="define_disease", disease_id="powdery_mildew", name="Powdery Mildew", plant_type="rose", symptoms=["white_spots", "wilting"], treatment="Neem oil spray")
        print("Diseases defined.")

        # 2. Simulate detecting a disease from an image path
        print("\n--- Detecting disease for 'tomato_plant_01' from 'tomato_plant_yellow_leaves.jpg' ---")
        detection_result1 = detector_tool.execute(operation="detect_disease", image_path="tomato_plant_yellow_leaves.jpg", plant_type="tomato", plant_id="tomato_plant_01")
        print(json.dumps(detection_result1, indent=2))

        # 3. Simulate detecting another disease
        print("\n--- Detecting disease for 'rose_bush_01' from 'rose_bush_white_spots.png' ---")
        detection_result2 = detector_tool.execute(operation="detect_disease", image_path="rose_bush_white_spots.png", plant_type="rose", plant_id="rose_bush_01")
        print(json.dumps(detection_result2, indent=2))

        # 4. Get detection history for a plant
        print("\n--- Getting detection history for 'tomato_plant_01' ---")
        history = detector_tool.execute(operation="get_detection_history", plant_id="tomato_plant_01")
        print(json.dumps(history, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
