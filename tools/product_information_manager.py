import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ProductInformationManagerTool(BaseTool):
    """
    A tool for managing product information, including adding, retrieving,
    updating, and deleting product records.
    """

    def __init__(self, tool_name: str = "ProductInformationManager", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.products_file = os.path.join(self.data_dir, "products.json")
        # Products structure: {product_id: {name: ..., description: ..., price: ..., attributes: {}}}
        self.products: Dict[str, Dict[str, Any]] = self._load_data(self.products_file, default={})

    @property
    def description(self) -> str:
        return "Manages product information: add, get, update, list, and delete product records."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_product", "get_product", "update_product", "delete_product", "list_products"]},
                "product_id": {"type": "string"},
                "product_data": {"type": "object", "description": "Full product data for adding/updating."},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "price": {"type": "number"},
                "attributes": {"type": "object", "description": "Additional product attributes."},
                "updates": {"type": "object", "description": "Partial product data for updating."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Starting with empty data.")
                    return default
        return default

    def _save_data(self) -> None:
        with open(self.products_file, 'w') as f: json.dump(self.products, f, indent=2)

    def add_product(self, product_id: str, name: str, description: str, price: float, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Adds a new product to the system."""
        if product_id in self.products: raise ValueError(f"Product '{product_id}' already exists. Use 'update_product'.")
        
        new_product = {
            "id": product_id, "name": name, "description": description, "price": price,
            "attributes": attributes or {}, "created_at": datetime.now().isoformat()
        }
        self.products[product_id] = new_product
        self._save_data()
        return new_product

    def get_product(self, product_id: str) -> Dict[str, Any]:
        """Retrieves details of a specific product."""
        product = self.products.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        return product

    def update_product(self, product_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates information for an existing product."""
        product = self.products.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        
        product.update(updates)
        product["last_updated_at"] = datetime.now().isoformat()
        self._save_data()
        return product

    def delete_product(self, product_id: str) -> Dict[str, Any]:
        """Deletes a product from the system."""
        if product_id not in self.products: raise ValueError(f"Product '{product_id}' not found.")
        
        del self.products[product_id]
        self._save_data()
        return {"status": "success", "message": f"Product '{product_id}' deleted successfully."}

    def list_products(self) -> List[Dict[str, Any]]:
        """Lists all products in the system."""
        return list(self.products.values())

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_product":
            product_id = kwargs.get('product_id')
            name = kwargs.get('name')
            description = kwargs.get('description')
            price = kwargs.get('price')
            if not all([product_id, name, description, price is not None]): # price can be 0, so check for not None
                raise ValueError("Missing 'product_id', 'name', 'description', or 'price' for 'add_product' operation.")
            return self.add_product(product_id, name, description, price, kwargs.get('attributes'))
        elif operation == "get_product":
            product_id = kwargs.get('product_id')
            if not product_id:
                raise ValueError("Missing 'product_id' for 'get_product' operation.")
            return self.get_product(product_id)
        elif operation == "update_product":
            product_id = kwargs.get('product_id')
            updates = kwargs.get('updates')
            if not all([product_id, updates]):
                raise ValueError("Missing 'product_id' or 'updates' for 'update_product' operation.")
            return self.update_product(product_id, updates)
        elif operation == "delete_product":
            product_id = kwargs.get('product_id')
            if not product_id:
                raise ValueError("Missing 'product_id' for 'delete_product' operation.")
            return self.delete_product(product_id)
        elif operation == "list_products":
            return self.list_products()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ProductInformationManagerTool functionality...")
    temp_dir = "temp_pim_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    pim_tool = ProductInformationManagerTool(data_dir=temp_dir)
    
    try:
        # 1. Add a new product
        print("\n--- Adding product 'SMART_WATCH_001' ---")
        pim_tool.execute(operation="add_product", product_id="SMART_WATCH_001", name="SmartWatch Pro", description="Advanced smartwatch with health tracking.", price=299.99, attributes={"color": "black", "storage_gb": 16})
        print("Product added.")

        # 2. Get product details
        print("\n--- Getting details for 'SMART_WATCH_001' ---")
        product_details = pim_tool.execute(operation="get_product", product_id="SMART_WATCH_001")
        print(json.dumps(product_details, indent=2))

        # 3. Update product information
        print("\n--- Updating 'SMART_WATCH_001' price ---")
        pim_tool.execute(operation="update_product", product_id="SMART_WATCH_001", updates={"price": 279.99})
        print("Product updated.")

        # 4. Add another product
        print("\n--- Adding product 'WIRELESS_EARBUDS_001' ---")
        pim_tool.execute(operation="add_product", product_id="WIRELESS_EARBUDS_001", name="AeroBuds", description="High-fidelity wireless earbuds.", price=149.99, attributes={"color": "white", "noise_cancellation": True})
        print("Product added.")

        # 5. List all products
        print("\n--- Listing all products ---")
        all_products = pim_tool.execute(operation="list_products")
        print(json.dumps(all_products, indent=2))

        # 6. Delete a product
        print("\n--- Deleting 'WIRELESS_EARBUDS_001' ---")
        pim_tool.execute(operation="delete_product", product_id="WIRELESS_EARBUDS_001")
        print("Product deleted.")

        # 7. List all products again
        print("\n--- Listing all products after deletion ---")
        all_products_after_delete = pim_tool.execute(operation="list_products")
        print(json.dumps(all_products_after_delete, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")