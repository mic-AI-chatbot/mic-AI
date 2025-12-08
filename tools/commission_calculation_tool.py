import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import CommissionPlan, CommissionTier
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class DefineCommissionPlanTool(BaseTool):
    """Defines a new commission plan with a base rate and optional tiered rates."""
    def __init__(self, tool_name="define_commission_plan"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Defines a new commission plan with a unique ID, a base rate, and optional tiered rates based on sales volume."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "A unique ID for the new commission plan."},
                "base_rate": {"type": "number", "description": "The base commission rate (e.g., 0.05 for 5%).", "default": 0.05},
                "tiers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "min_sales": {"type": "number", "description": "Minimum sales amount for this tier."},
                            "max_sales": {"type": "number", "description": "Maximum sales amount for this tier (use null for no upper limit).", "default": None},
                            "rate": {"type": "number", "description": "Commission rate for this tier."}
                        },
                        "required": ["min_sales", "rate"]
                    },
                    "description": "Optional: A list of tiered rates based on sales volume. Tiers should be ordered by min_sales and not overlap."
                }
            },
            "required": ["plan_id"]
        }

    def execute(self, plan_id: str, base_rate: float = 0.05, tiers: List[Dict[str, Any]] = None, **kwargs: Any) -> str:
        if tiers is None: tiers = []
        db = next(get_db())
        try:
            now = datetime.now().isoformat() + "Z"
            new_plan = CommissionPlan(
                plan_id=plan_id,
                base_rate=base_rate,
                created_at=now
            )
            db.add(new_plan)
            db.flush() # Flush to get plan_id for tiers

            for tier_data in tiers:
                new_tier = CommissionTier(
                    plan_id=plan_id,
                    min_sales=tier_data["min_sales"],
                    max_sales=tier_data.get("max_sales"),
                    rate=tier_data["rate"]
                )
                db.add(new_tier)
            db.commit()
            db.refresh(new_plan)
            report = {"message": f"Commission plan '{plan_id}' defined successfully with base rate {base_rate}."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Commission plan '{plan_id}' already exists. Please choose a unique ID."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error defining commission plan: {e}")
            report = {"error": f"Failed to define commission plan: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class CalculateCommissionTool(BaseTool):
    """Calculates commission for a given sales amount using a specified commission plan."""
    def __init__(self, tool_name="calculate_commission"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Calculates commission for a given sales amount, using a specified commission plan or a default rate."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sales_amount": {"type": "number", "description": "The total sales amount for which to calculate commission."},
                "plan_id": {"type": "string", "description": "The ID of the commission plan to use for calculation.", "default": "default_plan"}
            },
            "required": ["sales_amount"]
        }

    def execute(self, sales_amount: float, plan_id: str = "default_plan", **kwargs: Any) -> str:
        db = next(get_db())
        try:
            plan = db.query(CommissionPlan).options(joinedload(CommissionPlan.tiers)).filter(CommissionPlan.plan_id == plan_id).first()
            if not plan:
                return json.dumps({"error": f"Commission plan '{plan_id}' not found. Please define it first."})
            
            commission = 0.0
            applied_rate = plan.base_rate
            
            # Tiered commission calculation
            if plan.tiers:
                for tier in sorted(plan.tiers, key=lambda t: t.min_sales): # Ensure tiers are sorted
                    if sales_amount >= tier.min_sales and (tier.max_sales is None or sales_amount <= tier.max_sales):
                        commission = sales_amount * tier.rate
                        applied_rate = tier.rate
                        break
            else:
                commission = sales_amount * plan.base_rate
                
            report = {
                "sales_amount": sales_amount,
                "commission_plan_id": plan_id,
                "applied_rate": applied_rate,
                "calculated_commission": round(commission, 2),
                "message": f"Commission of {commission:.2f} calculated for sales of {sales_amount:.2f} using plan '{plan_id}'."
            }
        except Exception as e:
            logger.error(f"Error calculating commission: {e}")
            report = {"error": f"Failed to calculate commission: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetCommissionPlanTool(BaseTool):
    """Retrieves the details of a specific commission plan."""
    def __init__(self, tool_name="get_commission_plan"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the details of a specific commission plan, including its base rate and tiered rates."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"plan_id": {"type": "string", "description": "The ID of the commission plan to retrieve."}},
            "required": ["plan_id"]
        }

    def execute(self, plan_id: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            plan = db.query(CommissionPlan).options(joinedload(CommissionPlan.tiers)).filter(CommissionPlan.plan_id == plan_id).first()
            if not plan:
                return json.dumps({"error": f"Commission plan '{plan_id}' not found."})
            
            tiers_list = [{
                "min_sales": t.min_sales,
                "max_sales": t.max_sales,
                "rate": t.rate
            } for t in sorted(plan.tiers, key=lambda t: t.min_sales)]
            
            report = {
                "plan_id": plan.plan_id,
                "base_rate": plan.base_rate,
                "created_at": plan.created_at,
                "tiers": tiers_list
            }
        except Exception as e:
            logger.error(f"Error getting commission plan: {e}")
            report = {"error": f"Failed to get commission plan: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListCommissionPlansTool(BaseTool):
    """Lists all defined commission plans."""
    def __init__(self, tool_name="list_commission_plans"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all defined commission plans, showing their IDs and base rates."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            plans = db.query(CommissionPlan).order_by(CommissionPlan.created_at.desc()).all()
            plan_list = [{
                "plan_id": p.plan_id,
                "base_rate": p.base_rate,
                "created_at": p.created_at
            } for p in plans]
            report = {
                "total_plans": len(plan_list),
                "plans": plan_list
            }
        except Exception as e:
            logger.error(f"Error listing commission plans: {e}")
            report = {"error": f"Failed to list commission plans: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
