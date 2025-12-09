import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool
# from faker import Faker # Commented out for simulation, as Faker is an external dependency

logger = logging.getLogger(__name__)

class SyntheticDataGeneratorFromSchemaTool(BaseTool):
    """
    A tool that generates synthetic data based on a given schema.
    """

    def __init__(self, tool_name: str = "SyntheticDataGeneratorFromSchema", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.generated_data_file = os.path.join(self.data_dir, "synthetic_data_from_schema_records.json")
        
        # Generated data: {generation_id: {schema: {}, num_samples: ..., generated_samples: []}}
        self.generated_data_records: Dict[str, Dict[str, Any]] = self._load_data(self.generated_data_file, default={})
        # self.fake = Faker() # Initialize Faker if actually used

    @property
    def description(self) -> str:
        return "Generates synthetic data based on a given schema and number of samples."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_data_from_schema", "get_generated_data"]},
                "generation_id": {"type": "string"},
                "schema": {
                    "type": "object",
                    "description": "A dictionary defining the structure of the data to generate, e.g., {'name': 'name', 'email': 'email'}."
                },
                "num_samples": {"type": "integer", "minimum": 1, "default": 10}
            },
            "required": ["operation", "generation_id", "schema"]
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
        with open(self.generated_data_file, 'w') as f: json.dump(self.generated_data_records, f, indent=2)

    def _generate_single_record(self, schema: Dict[str, Any], record_index: int) -> Dict[str, Any]:
        """Simulates generating a single record based on a schema."""
        record = {}
        for field_name, field_type in schema.items():
            if isinstance(field_type, dict):
                record[field_name] = self._generate_single_record(field_type, record_index)
            elif isinstance(field_type, str):
                # Simulate data generation based on common Faker provider types
                if field_type == 'name':
                    record[field_name] = random.choice(["Alice Smith", "Bob Johnson", "Charlie Brown"])  # nosec B311
                elif field_type == 'email':
                    record[field_name] = f"{record.get('name', 'user').lower().replace(' ', '.')}{record_index}@example.com"
                elif field_type == 'address':
                    record[field_name] = f"{random.randint(1, 999)} {random.choice(['Main St', 'Oak Ave', 'Pine Ln'])}, City, State"  # nosec B311
                elif field_type == 'text':
                    record[field_name] = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
                elif field_type == 'date':
                    record[field_name] = datetime.now().strftime("%Y-%m-%d")
                elif field_type == 'uuid':
                    record[field_name] = f"uuid-{random.randint(1000, 9999)}"  # nosec B311
                elif field_type == 'integer':
                    record[field_name] = random.randint(1, 100)  # nosec B311
                elif field_type == 'float':
                    record[field_name] = round(random.uniform(0.0, 100.0), 2)  # nosec B311
                else:
                    record[field_name] = f"simulated_{field_type}_{record_index}"
            else:
                record[field_name] = None
        return record

    def generate_data_from_schema(self, generation_id: str, schema: Dict[str, Any], num_samples: int = 10) -> Dict[str, Any]:
        """
        Generates synthetic data based on a given schema.
        """
        if generation_id in self.generated_data_records: raise ValueError(f"Data with ID '{generation_id}' already exists.")

        synthetic_samples = []
        for i in range(num_samples):
            synthetic_samples.append(self._generate_single_record(schema, i))
        
        new_record = {
            "id": generation_id, "schema": schema, "num_samples": num_samples,
            "generated_samples": synthetic_samples, "generated_at": datetime.now().isoformat()
        }
        self.generated_data_records[generation_id] = new_record
        self._save_data()
        return new_record

    def get_generated_data(self, generation_id: str) -> Dict[str, Any]:
        """Retrieves previously generated synthetic data."""
        data = self.generated_data_records.get(generation_id)
        if not data: raise ValueError(f"Generated data '{generation_id}' not found.")
        return data

    def execute(self, operation: str, generation_id: str, schema: Dict[str, Any], **kwargs: Any) -> Any:
        if operation == "generate_data_from_schema":
            return self.generate_data_from_schema(generation_id, schema, kwargs.get('num_samples', 10))
        elif operation == "get_generated_data":
            # schema is not used for get_generated_data
            return self.get_generated_data(generation_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SyntheticDataGeneratorFromSchemaTool functionality...")
    temp_dir = "temp_synthetic_schema_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    generator_tool = SyntheticDataGeneratorFromSchemaTool(data_dir=temp_dir)
    
    try:
        # 1. Generate synthetic user data from schema
        print("\n--- Generating synthetic user data from schema 'user_schema_data_1' ---")
        user_schema = {
            'user_id': 'uuid',
            'name': 'name',
            'email': 'email',
            'age': 'integer',
            'address': 'address',
            'registration_date': 'date'
        }
        generated_users = generator_tool.execute(operation="generate_data_from_schema", generation_id="user_schema_data_1", schema=user_schema, num_samples=3)
        print(json.dumps(generated_users, indent=2))

        # 2. Get generated data
        print(f"\n--- Getting generated data for '{generated_users['id']}' ---")
        retrieved_data = generator_tool.execute(operation="get_generated_data", generation_id=generated_users["id"], schema={}) # schema is not used for get_generated_data
        print(json.dumps(retrieved_data, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")