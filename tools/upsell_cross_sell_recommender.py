import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated product catalog
product_catalog = {
    "standard_software_license": {
        "price": 100,
        "tier": "standard",
        "upsell_to": "premium_software_license",
        "cross_sells": ["support_package", "training_webinar"]
    },
    "premium_software_license": {
        "price": 250,
        "tier": "premium",
        "upsell_to": "enterprise_software_suite",
        "cross_sells": ["priority_support_package", "advanced_training_session"]
    },
    "enterprise_software_suite": {
        "price": 1000,
        "tier": "enterprise",
        "upsell_to": None,
        "cross_sells": ["dedicated_account_manager", "on-site_training"]
    },
    "support_package": {"price": 50},
    "training_webinar": {"price": 75},
    "priority_support_package": {"price": 150},
    "advanced_training_session": {"price": 200},
    "dedicated_account_manager": {"price": 500},
    "on-site_training": {"price": 1500}
}

class UpsellCrossSellRecommenderTool(BaseTool):
    """
    A tool for generating upsell and cross-sell recommendations based on a product catalog.
    """
    def __init__(self, tool_name: str = "upsell_cross_sell_recommender_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Recommends upsell and cross-sell products from a simulated catalog."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "The ID of the customer."},
                "current_product_id": {
                    "type": "string", 
                    "description": f"The product the customer owns or is viewing. Available products: {list(product_catalog.keys())}"
                }
            },
            "required": ["customer_id", "current_product_id"]
        }

    def execute(self, customer_id: str, current_product_id: str, **kwargs) -> Dict:
        """
        Generates upsell and cross-sell recommendations for a customer and product.
        """
        try:
            if current_product_id not in product_catalog:
                raise ValueError(f"Product '{current_product_id}' not found in catalog.")

            product_info = product_catalog[current_product_id]
            
            upsell_rec = self._recommend_upsell(product_info)
            cross_sell_recs = self._recommend_cross_sell(product_info)

            return {
                "message": "Recommendations generated successfully.",
                "customer_id": customer_id,
                "current_product": current_product_id,
                "upsell_recommendation": upsell_rec,
                "cross_sell_recommendations": cross_sell_recs
            }

        except Exception as e:
            logger.error(f"An error occurred in UpsellCrossSellRecommenderTool: {e}")
            return {"error": str(e)}

    def _recommend_upsell(self, product_info: Dict) -> Dict:
        upsell_product_id = product_info.get("upsell_to")
        if not upsell_product_id:
            return {"message": "No higher-tier product available for upsell."}
            
        upsell_product_info = product_catalog.get(upsell_product_id, {})
        return {
            "product_id": upsell_product_id,
            "reason": f"Upgrade from '{product_info.get('tier')}' to '{upsell_product_info.get('tier')}' tier for more features.",
            "price_increase": upsell_product_info.get("price", 0) - product_info.get("price", 0)
        }

    def _recommend_cross_sell(self, product_info: Dict) -> List[Dict]:
        cross_sell_ids = product_info.get("cross_sells", [])
        if not cross_sell_ids:
            return []
            
        recommendations = []
        for product_id in cross_sell_ids:
            cross_sell_info = product_catalog.get(product_id, {})
            recommendations.append({
                "product_id": product_id,
                "reason": "Complements your existing product.",
                "price": cross_sell_info.get("price", "N/A")
            })
        return recommendations