import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated warranties and claims
warranties: Dict[str, Dict[str, Any]] = {}
claims: Dict[str, Dict[str, Any]] = {}

class WarrantyManagementTool(BaseTool):
    """
    A tool to simulate a warranty management system.
    """
    def __init__(self, tool_name: str = "warranty_management_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates warranty management: register, check status, process claims, and list."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'register_warranty', 'check_status', 'submit_claim', 'update_claim_status', 'list_warranties', 'list_claims'."
                },
                "product_id": {"type": "string", "description": "The unique ID of the product."},
                "customer_name": {"type": "string", "description": "Name of the customer."},
                "customer_email": {"type": "string", "description": "Email of the customer."},
                "purchase_date": {"type": "string", "description": "The purchase date (YYYY-MM-DD)."},
                "warranty_period_days": {"type": "integer", "description": "Duration of warranty in days.", "default": 365},
                "claim_id": {"type": "string", "description": "The unique ID of the claim."},
                "issue_description": {"type": "string", "description": "Description of the issue for the claim."},
                "new_claim_status": {
                    "type": "string",
                    "description": "The new status for a claim ('submitted', 'under_review', 'approved', 'rejected', 'resolved')."
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            product_id = kwargs.get("product_id")
            claim_id = kwargs.get("claim_id")

            if action in ['register_warranty', 'check_status', 'submit_claim'] and not product_id:
                raise ValueError(f"'product_id' is required for the '{action}' action.")
            if action in ['update_claim_status'] and not claim_id:
                raise ValueError(f"'claim_id' is required for the '{action}' action.")

            actions = {
                "register_warranty": self._register_warranty,
                "check_status": self._check_warranty_status,
                "submit_claim": self._submit_claim,
                "update_claim_status": self._update_claim_status,
                "list_warranties": self._list_warranties,
                "list_claims": self._list_claims,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WarrantyManagementTool: {e}")
            return {"error": str(e)}

    def _register_warranty(self, product_id: str, customer_name: str, customer_email: str, purchase_date: str, warranty_period_days: int = 365, **kwargs) -> Dict:
        if not all([customer_name, customer_email, purchase_date]):
            raise ValueError("'customer_name', 'customer_email', and 'purchase_date' are required.")
        if product_id in warranties:
            raise ValueError(f"Warranty for product '{product_id}' already registered.")
        
        try:
            purchase_dt = datetime.strptime(purchase_date, "%Y-%m-%d")
            expiry_dt = purchase_dt + timedelta(days=warranty_period_days)
        except ValueError:
            raise ValueError("Invalid 'purchase_date' format. Use YYYY-MM-DD.")

        new_warranty = {
            "product_id": product_id,
            "customer_info": {"name": customer_name, "email": customer_email},
            "purchase_date": purchase_date,
            "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
            "status": "active"
        }
        warranties[product_id] = new_warranty
        logger.info(f"Warranty for product '{product_id}' registered.")
        return {"message": "Warranty registered successfully.", "details": new_warranty}

    def _check_warranty_status(self, product_id: str, **kwargs) -> Dict:
        if product_id not in warranties:
            return {"error": f"Warranty for product '{product_id}' not found."}
        
        details = warranties[product_id]
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if current_date > details["expiry_date"]:
            details["status"] = "expired"
        
        return {"warranty_status": details}

    def _submit_claim(self, product_id: str, issue_description: str, **kwargs) -> Dict:
        if product_id not in warranties:
            raise ValueError(f"Warranty for product '{product_id}' not found. Cannot submit claim.")
        if not issue_description:
            raise ValueError("'issue_description' is required to submit a claim.")
            
        claim_id = f"CLAIM-{random.randint(10000, 99999)}"  # nosec B311
        new_claim = {
            "claim_id": claim_id,
            "product_id": product_id,
            "issue_description": issue_description,
            "status": "submitted",
            "submitted_at": datetime.now().isoformat()
        }
        claims[claim_id] = new_claim
        logger.info(f"Claim '{claim_id}' submitted for product '{product_id}'.")
        return {"message": "Claim submitted successfully.", "details": new_claim}

    def _update_claim_status(self, claim_id: str, new_claim_status: str, **kwargs) -> Dict:
        if claim_id not in claims:
            raise ValueError(f"Claim '{claim_id}' not found.")
        if new_claim_status not in ["submitted", "under_review", "approved", "rejected", "resolved"]:
            raise ValueError(f"Invalid claim status '{new_claim_status}'.")
            
        claim = claims[claim_id]
        claim["status"] = new_claim_status
        claim["last_updated"] = datetime.now().isoformat()
        logger.info(f"Claim '{claim_id}' status updated to '{new_claim_status}'.")
        return {"message": "Claim status updated successfully.", "claim_id": claim_id, "new_status": new_claim_status}

    def _list_warranties(self, **kwargs) -> Dict:
        if not warranties:
            return {"message": "No warranties registered yet."}
        return {"warranties": list(warranties.values())}

    def _list_claims(self, **kwargs) -> Dict:
        if not claims:
            return {"message": "No claims submitted yet."}
        return {"claims": list(claims.values())}