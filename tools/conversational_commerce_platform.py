import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

PRODUCTS_FILE = Path("products.json")
CARTS_FILE = Path("carts.json")

class ProductManager:
    """Manages product catalog, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = PRODUCTS_FILE):
        if cls._instance is None:
            cls._instance = super(ProductManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.products: Dict[str, Any] = cls._instance._load_products()
        return cls._instance

    def _load_products(self) -> Dict[str, Any]:
        """Loads products from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty products.")
                return {}
            except Exception as e:
                logger.error(f"Error loading products from {self.file_path}: {e}")
                return {}
        # Initial dummy data if file doesn't exist
        return {
            "prod_1": {"name": "Laptop Pro", "price": 1200.00, "description": "High-performance laptop.", "stock": 10},
            "prod_2": {"name": "Wireless Mouse", "price": 25.00, "description": "Ergonomic wireless mouse.", "stock": 50},
            "prod_3": {"name": "USB-C Hub", "price": 45.00, "description": "Multi-port USB-C adapter.", "stock": 20}
        }

    def _save_products(self) -> None:
        """Saves products to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving products to {self.file_path}: {e}")

    def add_product(self, product_id: str, name: str, price: float, description: str, stock: int) -> bool:
        if product_id in self.products:
            return False
        self.products[product_id] = {
            "name": name,
            "price": price,
            "description": description,
            "stock": stock,
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._save_products()
        return True

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        return self.products.get(product_id)

    def list_products(self) -> List[Dict[str, Any]]:
        return [{"product_id": p_id, "name": details['name'], "price": details['price'], "stock": details['stock']} for p_id, details in self.products.items()]

    def update_stock(self, product_id: str, quantity_change: int) -> bool:
        if product_id not in self.products:
            return False
        self.products[product_id]["stock"] += quantity_change
        self._save_products()
        return True

product_manager = ProductManager()

class CartManager:
    """Manages user shopping carts, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CARTS_FILE):
        if cls._instance is None:
            cls._instance = super(CartManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.carts: Dict[str, Dict[str, int]] = cls._instance._load_carts()
        return cls._instance

    def _load_carts(self) -> Dict[str, Dict[str, int]]:
        """Loads carts from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty carts.")
                return {}
            except Exception as e:
                logger.error(f"Error loading carts from {self.file_path}: {e}")
                return {}
        return {}

    def _save_carts(self) -> None:
        """Saves carts to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.carts, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving carts to {self.file_path}: {e}")

    def add_to_cart(self, user_id: str, product_id: str, quantity: int) -> bool:
        if user_id not in self.carts:
            self.carts[user_id] = {}
        self.carts[user_id][product_id] = self.carts[user_id].get(product_id, 0) + quantity
        self._save_carts()
        return True

    def remove_from_cart(self, user_id: str, product_id: str, quantity: int) -> bool:
        if user_id not in self.carts or product_id not in self.carts[user_id]:
            return False
        
        self.carts[user_id][product_id] -= quantity
        if self.carts[user_id][product_id] <= 0:
            del self.carts[user_id][product_id]
        self._save_carts()
        return True

    def get_cart(self, user_id: str) -> Dict[str, int]:
        return self.carts.get(user_id, {})

    def clear_cart(self, user_id: str) -> bool:
        if user_id in self.carts:
            del self.carts[user_id]
            self._save_carts()
            return True
        return False

cart_manager = CartManager()

class AddProductTool(BaseTool):
    """Adds a new product to the product catalog."""
    def __init__(self, tool_name="add_product"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new product to the product catalog with its name, price, description, and initial stock."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "A unique ID for the product."},
                "name": {"type": "string", "description": "The name of the product."},
                "price": {"type": "number", "description": "The price of the product."},
                "description": {"type": "string", "description": "A brief description of the product."},
                "stock": {"type": "integer", "description": "The initial stock quantity."}
            },
            "required": ["product_id", "name", "price", "description", "stock"]
        }

    def execute(self, product_id: str, name: str, price: float, description: str, stock: int, **kwargs: Any) -> str:
        success = product_manager.add_product(product_id, name, price, description, stock)
        if success:
            report = {"message": f"Product '{name}' (ID: {product_id}) added to catalog."}
        else:
            report = {"error": f"Product '{product_id}' already exists. Use update if you want to modify it."}
        return json.dumps(report, indent=2)

class ListProductsTool(BaseTool):
    """Lists all available products in the catalog."""
    def __init__(self, tool_name="list_products"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all available products in the catalog, showing their ID, name, price, and current stock."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        products = product_manager.list_products()
        if not products:
            return json.dumps({"message": "No products found in the catalog."})
        
        return json.dumps({"total_products": len(products), "products": products}, indent=2)

class AddToCartTool(BaseTool):
    """Adds a product to a user's shopping cart."""
    def __init__(self, tool_name="add_to_cart"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a specified quantity of a product to a user's shopping cart."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user."},
                "product_id": {"type": "string", "description": "The ID of the product to add."},
                "quantity": {"type": "integer", "description": "The quantity to add.", "default": 1}
            },
            "required": ["user_id", "product_id"]
        }

    def execute(self, user_id: str, product_id: str, quantity: int = 1, **kwargs: Any) -> str:
        product = product_manager.get_product(product_id)
        if not product:
            return json.dumps({"error": f"Product '{product_id}' not found in catalog."})
        if product["stock"] < quantity:
            return json.dumps({"error": f"Not enough stock for product '{product_id}'. Available: {product['stock']}."})
        
        success = cart_manager.add_to_cart(user_id, product_id, quantity)
        if success:
            product_manager.update_stock(product_id, -quantity) # Decrease stock
            report = {"message": f"{quantity} of '{product['name']}' added to {user_id}'s cart."}
        else:
            report = {"error": f"Failed to add product '{product_id}' to cart. An unexpected error occurred."}
        return json.dumps(report, indent=2)

class RemoveFromCartTool(BaseTool):
    """Removes a product from a user's shopping cart."""
    def __init__(self, tool_name="remove_from_cart"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Removes a specified quantity of a product from a user's shopping cart."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user."},
                "product_id": {"type": "string", "description": "The ID of the product to remove."},
                "quantity": {"type": "integer", "description": "The quantity to remove.", "default": 1}
            },
            "required": ["user_id", "product_id"]
        }

    def execute(self, user_id: str, product_id: str, quantity: int = 1, **kwargs: Any) -> str:
        cart = cart_manager.get_cart(user_id)
        if product_id not in cart or cart[product_id] < quantity:
            return json.dumps({"error": f"Not enough '{product_id}' in {user_id}'s cart to remove {quantity}."})
        
        success = cart_manager.remove_from_cart(user_id, product_id, quantity)
        if success:
            product_manager.update_stock(product_id, quantity) # Increase stock
            report = {"message": f"{quantity} of '{product_id}' removed from {user_id}'s cart."}
        else:
            report = {"error": f"Failed to remove product '{product_id}' from cart. An unexpected error occurred."}
        return json.dumps(report, indent=2)

class ViewCartTool(BaseTool):
    """Views the contents of a user's shopping cart."""
    def __init__(self, tool_name="view_cart"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Views the current contents of a user's shopping cart, including product details and total price."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"user_id": {"type": "string", "description": "The ID of the user whose cart to view."}},
            "required": ["user_id"]
        }

    def execute(self, user_id: str, **kwargs: Any) -> str:
        cart_contents_raw = cart_manager.get_cart(user_id)
        if not cart_contents_raw:
            return json.dumps({"user_id": user_id, "cart_contents": [], "total_price": 0.0, "message": "Cart is empty."})
            
        cart_contents = []
        total_price = 0.0
        
        for product_id, quantity in cart_contents_raw.items():
            prod_info = product_manager.get_product(product_id)
            if prod_info:
                item_total = prod_info["price"] * quantity
                cart_contents.append({
                    "product_id": product_id,
                    "name": prod_info["name"],
                    "price": prod_info["price"],
                    "quantity": quantity,
                    "item_total": round(item_total, 2)
                })
                total_price += item_total
            else:
                cart_contents.append({
                    "product_id": product_id,
                    "name": "Unknown Product",
                    "price": 0.0,
                    "quantity": quantity,
                    "item_total": 0.0,
                    "warning": "Product not found in catalog."
                })
        
        return json.dumps({
            "user_id": user_id,
            "cart_contents": cart_contents,
            "total_price": round(total_price, 2),
            "message": "Cart retrieved successfully."
        }, indent=2)

class CheckoutTool(BaseTool):
    """Simulates the checkout process for a user's shopping cart."""
    def __init__(self, tool_name="checkout"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates the checkout process for a user's shopping cart, clearing the cart upon successful checkout."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user checking out."},
                "payment_method": {"type": "string", "description": "The payment method to use.", "enum": ["credit_card", "paypal", "bank_transfer"]},
                "shipping_address": {"type": "string", "description": "The shipping address for the order."}
            },
            "required": ["user_id", "payment_method", "shipping_address"]
        }

    def execute(self, user_id: str, payment_method: str, shipping_address: str, **kwargs: Any) -> str:
        cart = cart_manager.get_cart(user_id)
        if not cart:
            return json.dumps({"error": f"User '{user_id}'s cart is empty. Cannot checkout."})
        
        # Simulate payment processing
        payment_success = random.choice([True, False])  # nosec B311
        
        if payment_success:
            cart_manager.clear_cart(user_id)
            report = {
                "message": f"Checkout successful for user '{user_id}'. Order placed.",
                "payment_method": payment_method,
                "shipping_address": shipping_address,
                "order_id": f"order_{random.randint(10000, 99999)}"  # nosec B311
            }
        else:
            report = {"error": f"Payment failed for user '{user_id}'. Please try again."}
        return json.dumps(report, indent=2)
