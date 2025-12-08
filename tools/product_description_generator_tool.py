
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ProductDescriptionGeneratorTool(BaseTool):
    """
    A tool that generates compelling product descriptions based on product
    details, features, benefits, target audience, and desired tone.
    """

    def __init__(self, tool_name: str = "ProductDescriptionGenerator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.descriptions_file = os.path.join(self.data_dir, "generated_product_descriptions.json")
        # Descriptions structure: {product_id: {product_name: ..., description: ..., generated_text: ...}}
        self.generated_descriptions: Dict[str, Dict[str, Any]] = self._load_data(self.descriptions_file, default={})

    @property
    def description(self) -> str:
        return "Generates compelling product descriptions based on product details, features, benefits, audience, and tone."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_description", "get_generated_description"]},
                "product_id": {"type": "string"},
                "product_name": {"type": "string"},
                "features": {"type": "array", "items": {"type": "string"}, "description": "Key features of the product."},
                "benefits": {"type": "array", "items": {"type": "string"}, "description": "Benefits the product offers."},
                "target_audience": {"type": "string", "enum": ["tech_enthusiasts", "busy_parents", "gamers", "general"], "default": "general"},
                "tone": {"type": "string", "enum": ["formal", "casual", "exciting", "informative"], "default": "informative"}
            },
            "required": ["operation", "product_id"]
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
        with open(self.descriptions_file, 'w') as f: json.dump(self.generated_descriptions, f, indent=2)

    def generate_description(self, product_id: str, product_name: str, features: List[str], benefits: List[str], target_audience: str = "general", tone: str = "informative") -> Dict[str, Any]:
        """Generates a compelling product description."""
        if product_id in self.generated_descriptions: raise ValueError(f"Description for product '{product_id}' already exists.")
        
        description_parts = []
        
        # Opening
        if tone == "exciting":
            description_parts.append(f"Get ready to experience the future with the {product_name}!")
        elif tone == "casual":
            description_parts.append(f"Meet the {product_name}, your new favorite gadget.")
        else: # formal, informative
            description_parts.append(f"Introducing the {product_name}, a cutting-edge solution designed for optimal performance.")
        
        # Features
        if features:
            description_parts.append(f"Packed with innovative features like {', '.join(features[:-1])} and {features[-1]}, the {product_name} stands out.")
        
        # Benefits
        if benefits:
            description_parts.append(f"Enjoy unparalleled benefits such as {', '.join(benefits[:-1])} and {benefits[-1]}.")
        
        # Call to action based on audience
        if target_audience == "tech_enthusiasts":
            description_parts.append("Dive deep into its capabilities and revolutionize your workflow.")
        elif target_audience == "busy_parents":
            description_parts.append("Simplify your daily routine and reclaim precious time.")
        elif target_audience == "gamers":
            description_parts.append("Dominate the competition and immerse yourself in next-level gaming.")
        else: # general
            description_parts.append("Discover how the {product_name} can enhance your life today.")
        
        generated_text = " ".join(description_parts)

        new_description = {
            "id": product_id, "product_name": product_name, "features": features,
            "benefits": benefits, "target_audience": target_audience, "tone": tone,
            "generated_text": generated_text, "generated_at": datetime.now().isoformat()
        }
        self.generated_descriptions[product_id] = new_description
        self._save_data()
        return new_description

    def get_generated_description(self, product_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated product description."""
        description = self.generated_descriptions.get(product_id)
        if not description: raise ValueError(f"Description for product '{product_id}' not found.")
        return description

    def execute(self, operation: str, product_id: str, **kwargs: Any) -> Any:
        if operation == "generate_description":
            return self.generate_description(product_id, kwargs['product_name'], kwargs['features'], kwargs['benefits'], kwargs.get('target_audience', 'general'), kwargs.get('tone', 'informative'))
        elif operation == "get_generated_description":
            return self.get_generated_description(product_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ProductDescriptionGeneratorTool functionality...")
    temp_dir = "temp_product_desc_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    desc_generator = ProductDescriptionGeneratorTool(data_dir=temp_dir)
    
    try:
        # 1. Generate a description for a new smartphone
        print("\n--- Generating description for 'QuantumPhone X' (exciting tone, tech enthusiasts) ---")
        product_id_1 = "QPX-001"
        desc_generator.execute(operation="generate_description", product_id=product_id_1, product_name="QuantumPhone X",
                               features=["Quantum Processor", "Holographic Display", "AI Camera"],
                               benefits=["Blazing fast performance", "Immersive visuals", "Stunning photos"],
                               target_audience="tech_enthusiasts", tone="exciting")
        print("Description generated.")

        # 2. Get the generated description
        print(f"\n--- Getting description for '{product_id_1}' ---")
        description1 = desc_generator.execute(operation="get_generated_description", product_id=product_id_1)
        print(json.dumps(description1, indent=2))

        # 3. Generate a description for a new smart home device
        print("\n--- Generating description for 'EcoHome Hub' (informative tone, busy parents) ---")
        product_id_2 = "EHH-001"
        desc_generator.execute(operation="generate_description", product_id=product_id_2, product_name="EcoHome Hub",
                               features=["Energy Monitoring", "Voice Control", "Automated Routines"],
                               benefits=["Save on bills", "Convenient home management", "Peace of mind"],
                               target_audience="busy_parents", tone="informative")
        print("Description generated.")

        # 4. Get the generated description
        print(f"\n--- Getting description for '{product_id_2}' ---")
        description2 = desc_generator.execute(operation="get_generated_description", product_id=product_id_2)
        print(json.dumps(description2, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
