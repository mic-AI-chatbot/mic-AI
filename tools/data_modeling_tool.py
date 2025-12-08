import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataModelingTool(BaseTool):
    """
    A tool for managing data models, allowing for their creation, validation,
    and retrieval.
    """

    def __init__(self, tool_name: str = "data_modeling_tool"):
        super().__init__(tool_name)
        self.models_file = "data_models.json"
        self.data_models: Dict[str, Dict[str, Any]] = self._load_data_models()

    @property
    def description(self) -> str:
        return "Manages data models, including creation, validation, and retrieval of model definitions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data modeling operation to perform.",
                    "enum": ["create_data_model", "validate_data_model", "get_data_model_details", "list_data_models"]
                },
                "model_id": {"type": "string"},
                "model_name": {"type": "string"},
                "model_type": {"type": "string"},
                "entities": {"type": "array", "items": {"type": "object"}},
                "relationships": {"type": "array", "items": {"type": "object"}},
                "description": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_data_models(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.models_file):
            with open(self.models_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted data models file '{self.models_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_data_models(self) -> None:
        with open(self.models_file, 'w') as f:
            json.dump(self.data_models, f, indent=4)

    def _create_data_model(self, model_id: str, model_name: str, model_type: str, entities: List[Dict[str, Any]], relationships: Optional[List[Dict[str, Any]]] = None, description: Optional[str] = None) -> Dict[str, Any]:
        if not all([model_id, model_name, model_type, entities]):
            raise ValueError("Model ID, name, type, and entities cannot be empty.")
        if model_id in self.data_models:
            raise ValueError(f"Data model '{model_id}' already exists.")

        new_model = {
            "model_id": model_id, "model_name": model_name, "model_type": model_type,
            "entities": entities, "relationships": relationships or [], "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.data_models[model_id] = new_model
        self._save_data_models()
        return new_model

    def _validate_data_model(self, model_id: str) -> Dict[str, Any]:
        model = self.data_models.get(model_id)
        if not model: raise ValueError(f"Data model '{model_id}' not found.")

        validation_status = "compliant"
        issues = []

        if not model["entities"]:
            issues.append("Model has no defined entities.")
            validation_status = "non_compliant"
        
        for entity in model["entities"]:
            if "name" not in entity or not entity["name"]:
                issues.append("An entity is missing a 'name'.")
                validation_status = "non_compliant"
            if "attributes" not in entity or not entity["attributes"]:
                issues.append(f"Entity '{entity.get('name', 'Unnamed')}' has no defined attributes.")
                validation_status = "non_compliant"
        
        for rel in model["relationships"]:
            if rel.get("from_entity") not in [e["name"] for e in model["entities"]]:
                issues.append(f"Relationship source entity '{rel.get('from_entity')}' not found.")
                validation_status = "non_compliant"
            if rel.get("to_entity") not in [e["name"] for e in model["entities"]]:
                issues.append(f"Relationship target entity '{rel.get('to_entity')}' not found.")
                validation_status = "non_compliant"

        validation_result = {
            "model_id": model_id, "model_name": model["model_name"], "validation_status": validation_status,
            "issues": issues, "validated_at": datetime.now().isoformat()
        }
        return validation_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_data_model":
            return self._create_data_model(kwargs.get("model_id"), kwargs.get("model_name"), kwargs.get("model_type"), kwargs.get("entities"), kwargs.get("relationships"), kwargs.get("description"))
        elif operation == "validate_data_model":
            return self._validate_data_model(kwargs.get("model_id"))
        elif operation == "get_data_model_details":
            return self.data_models.get(kwargs.get("model_id"))
        elif operation == "list_data_models":
            return list(self.data_models.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataModelingTool functionality...")
    tool = DataModelingTool()
    
    try:
        print("\n--- Creating Data Model ---")
        tool.execute(operation="create_data_model", model_id="customer_orders", model_name="Customer Orders", model_type="relational", entities=[{"name": "Customers", "attributes": ["id", "name"]}])
        
        print("\n--- Validating Data Model ---")
        validation_result = tool.execute(operation="validate_data_model", model_id="customer_orders")
        print(json.dumps(validation_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.models_file):
            os.remove(tool.models_file)
        print("\nCleanup complete.")
