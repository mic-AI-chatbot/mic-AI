import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PricingOptimizationSimulatorTool(BaseTool):
    """
    A tool that simulates pricing optimization, recommending prices,
    analyzing price elasticity, and simulating pricing strategies.
    """

    def __init__(self, tool_name: str = "PricingOptimizationSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.products_file = os.path.join(self.data_dir, "product_pricing_data.json")
        # Product data structure: {product_id: {cost: ..., current_price: ..., demand_history: [{price: ..., demand: ...}]}}
        self.product_data: Dict[str, Dict[str, Any]] = self._load_data(self.products_file, default={})

    @property
    def description(self) -> str:
        return "Simulates pricing optimization: recommends prices, analyzes elasticity, and simulates strategies."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_product", "recommend_price", "analyze_elasticity", "simulate_pricing_strategy"]},
                "product_id": {"type": "string"},
                "cost": {"type": "number", "minimum": 0},
                "current_price": {"type": "number", "minimum": 0},
                "demand_history": {"type": "array", "items": {"type": "object", "properties": {"price": {"type": "number"}, "demand": {"type": "number"}}}},
                "strategy_name": {"type": "string", "enum": ["dynamic_pricing", "cost_plus", "value_based"]},
                "market_conditions": {"type": "object", "description": "e.g., {'competition_level': 'high', 'economic_growth': 'low'}"}
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
        with open(self.products_file, 'w') as f: json.dump(self.product_data, f, indent=2)

    def add_product(self, product_id: str, cost: float, current_price: float, demand_history: Optional[List[Dict[str, float]]] = None) -> Dict[str, Any]:
        """Adds a new product with its pricing and demand data."""
        if product_id in self.product_data: raise ValueError(f"Product '{product_id}' already exists.")
        
        new_product = {
            "id": product_id, "cost": cost, "current_price": current_price,
            "demand_history": demand_history or [], "added_at": datetime.now().isoformat()
        }
        self.product_data[product_id] = new_product
        self._save_data()
        return new_product

    def recommend_price(self, product_id: str) -> Dict[str, Any]:
        """Recommends an optimal price for a product based on simulated demand."""
        product = self.product_data.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        
        if not product["demand_history"]:
            return {"status": "info", "message": "No demand history available. Recommending base price.", "recommended_price": product["current_price"]}

        # Simple rule: if recent demand is high, suggest higher price; if low, lower price
        latest_demand = product["demand_history"][-1]["demand"] if product["demand_history"] else 0
        
        recommended_price = product["current_price"]
        reason = "Based on current price and available data."

        if latest_demand > 100: # High demand
            recommended_price = round(product["current_price"] * random.uniform(1.05, 1.15), 2)  # nosec B311
            reason = "High recent demand suggests a price increase is feasible."
        elif latest_demand < 50: # Low demand
            recommended_price = round(product["current_price"] * random.uniform(0.85, 0.95), 2)  # nosec B311
            reason = "Low recent demand suggests a price reduction to stimulate sales."
        
        return {"status": "success", "product_id": product_id, "recommended_price": recommended_price, "reason": reason}

    def analyze_elasticity(self, product_id: str) -> Dict[str, Any]:
        """Analyzes price elasticity of demand for a product."""
        product = self.product_data.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        
        if len(product["demand_history"]) < 2:
            return {"status": "info", "message": "Not enough demand history to calculate elasticity (min 2 points)."}

        # Use the last two data points for a simple elasticity calculation
        p1_data = product["demand_history"][-2]
        p2_data = product["demand_history"][-1]

        p1, q1 = p1_data["price"], p1_data["demand"]
        p2, q2 = p2_data["price"], p2_data["demand"]

        if p1 == p2 or q1 == q2:
            return {"status": "info", "message": "Price or demand did not change, cannot calculate elasticity."}

        # Price Elasticity of Demand (PED) formula: % Change in Quantity / % Change in Price
        # Using midpoint formula for better accuracy
        percent_change_q = ((q2 - q1) / ((q1 + q2) / 2))
        percent_change_p = ((p2 - p1) / ((p1 + p2) / 2))
        
        elasticity = percent_change_q / percent_change_p if percent_change_p != 0 else float('inf')
        
        interpretation = ""
        if elasticity < -1: interpretation = "Elastic (demand is sensitive to price changes)."
        elif elasticity > -1 and elasticity < 0: interpretation = "Inelastic (demand is not very sensitive to price changes)."
        elif elasticity == -1: interpretation = "Unit Elastic."
        else: interpretation = "Unusual or perfectly elastic/inelastic (check data)."

        return {"status": "success", "product_id": product_id, "price_elasticity": round(elasticity, 2), "interpretation": interpretation}

    def simulate_pricing_strategy(self, product_id: str, strategy_name: str, market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates the impact of different pricing strategies."""
        product = self.product_data.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        
        simulated_revenue_change = 0.0
        simulated_market_share_change = 0.0
        
        if strategy_name == "dynamic_pricing":
            # Simulate higher revenue in volatile markets
            if market_conditions.get("competition_level") == "high":
                simulated_revenue_change = random.uniform(0.05, 0.15)  # nosec B311
                simulated_market_share_change = random.uniform(-0.02, 0.03)  # nosec B311
            else:
                simulated_revenue_change = random.uniform(0.1, 0.25)  # nosec B311
                simulated_market_share_change = random.uniform(0.01, 0.05)  # nosec B311
        elif strategy_name == "cost_plus":
            # Stable but not always optimal
            simulated_revenue_change = random.uniform(0.02, 0.08)  # nosec B311
            simulated_market_share_change = random.uniform(-0.01, 0.01)  # nosec B311
        elif strategy_name == "value_based":
            # High potential if value is perceived
            simulated_revenue_change = random.uniform(0.1, 0.3)  # nosec B311
            simulated_market_share_change = random.uniform(0.02, 0.08)  # nosec B311
        
        return {
            "status": "success", "product_id": product_id, "strategy": strategy_name,
            "simulated_revenue_change_percent": round(simulated_revenue_change * 100, 2),
            "simulated_market_share_change_percent": round(simulated_market_share_change * 100, 2)
        }

    def execute(self, operation: str, product_id: str, **kwargs: Any) -> Any:
        if operation == "add_product":
            cost = kwargs.get('cost')
            current_price = kwargs.get('current_price')
            if cost is None or current_price is None:
                raise ValueError("Missing 'cost' or 'current_price' for 'add_product' operation.")
            return self.add_product(product_id, cost, current_price, kwargs.get('demand_history'))
        elif operation == "recommend_price":
            # No additional kwargs required for recommend_price
            return self.recommend_price(product_id)
        elif operation == "analyze_elasticity":
            # No additional kwargs required for analyze_elasticity
            return self.analyze_elasticity(product_id)
        elif operation == "simulate_pricing_strategy":
            strategy_name = kwargs.get('strategy_name')
            market_conditions = kwargs.get('market_conditions')
            if not all([strategy_name, market_conditions]):
                raise ValueError("Missing 'strategy_name' or 'market_conditions' for 'simulate_pricing_strategy' operation.")
            return self.simulate_pricing_strategy(product_id, strategy_name, market_conditions)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PricingOptimizationSimulatorTool functionality...")
    temp_dir = "temp_pricing_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    pricing_tool = PricingOptimizationSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add a product with demand history
        print("\n--- Adding product 'widget_pro' ---")
        pricing_tool.execute(operation="add_product", product_id="widget_pro", cost=10.0, current_price=20.0,
                             demand_history=[{"price": 20, "demand": 100}, {"price": 18, "demand": 120}, {"price": 22, "demand": 80}])
        print("Product added.")

        # 2. Recommend a price
        print("\n--- Recommending price for 'widget_pro' ---")
        recommended_price = pricing_tool.execute(operation="recommend_price", product_id="widget_pro")
        print(json.dumps(recommended_price, indent=2))

        # 3. Analyze elasticity
        print("\n--- Analyzing elasticity for 'widget_pro' ---")
        elasticity = pricing_tool.execute(operation="analyze_elasticity", product_id="widget_pro")
        print(json.dumps(elasticity, indent=2))

        # 4. Simulate a pricing strategy
        print("\n--- Simulating 'dynamic_pricing' strategy for 'widget_pro' ---")
        strategy_impact = pricing_tool.execute(operation="simulate_pricing_strategy", product_id="widget_pro", strategy_name="dynamic_pricing", market_conditions={"competition_level": "medium", "economic_growth": "high"})
        print(json.dumps(strategy_impact, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")