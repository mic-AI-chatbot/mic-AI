import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import Budget, Expense
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class CreateBudgetTool(BaseTool):
    """Creates a new budget with a specified name, category, and allocated amount."""
    def __init__(self, tool_name="create_budget"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new budget with a specified name, category, and allocated amount."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "budget_name": {"type": "string", "description": "A unique name for the new budget."},
                "category": {"type": "string", "description": "The category of the budget (e.g., 'marketing', 'travel', 'software')."},
                "amount": {"type": "number", "description": "The total allocated amount for this budget."}
            },
            "required": ["budget_name", "category", "amount"]
        }

    def execute(self, budget_name: str, category: str, amount: float, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            new_budget = Budget(
                budget_name=budget_name,
                category=category,
                allocated_amount=amount,
                spent_amount=0.0,
                remaining_amount=amount,
                alert_threshold=0.8, # Default
                created_at=datetime.now().isoformat() + "Z"
            )
            db.add(new_budget)
            db.commit()
            db.refresh(new_budget)
            report = {"message": f"Budget '{budget_name}' for category '{category}' created with an allocated amount of {amount:.2f}."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Budget '{budget_name}' already exists. Please choose a unique name."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating budget: {e}")
            report = {"error": f"Failed to create budget: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class TrackSpendingTool(BaseTool):
    """Tracks spending against a budget."""
    def __init__(self, tool_name="track_spending"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Tracks spending against a specified budget, updating the spent and remaining amounts."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "budget_name": {"type": "string", "description": "The name of the budget to track spending for."},
                "expense_amount": {"type": "number", "description": "The amount of the expense to track."},
                "description": {"type": "string", "description": "A brief description of the expense."}
            },
            "required": ["budget_name", "expense_amount", "description"]
        }

    def execute(self, budget_name: str, expense_amount: float, description: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            budget = db.query(Budget).filter(Budget.budget_name == budget_name).first()
            if not budget:
                return json.dumps({"error": f"Budget '{budget_name}' not found. Please create it first."})
            
            new_expense = Expense(
                budget_name=budget_name,
                amount=expense_amount,
                description=description,
                timestamp=datetime.now().isoformat() + "Z"
            )
            db.add(new_expense)

            budget.spent_amount += expense_amount
            budget.remaining_amount -= expense_amount
            db.commit()
            db.refresh(budget)
            db.refresh(new_expense)

            message = f"Expense of {expense_amount:.2f} for '{description}' tracked for budget '{budget_name}'. Remaining: {budget.remaining_amount:.2f}."
            
            if budget.remaining_amount < 0:
                message += f" Warning: Budget is overspent by {-budget.remaining_amount:.2f}."
            elif budget.spent_amount / budget.allocated_amount >= budget.alert_threshold:
                message += f" Alert: Budget has reached {budget.alert_threshold*100:.0f}% of its allocated amount."

            report = {
                "message": message,
                "budget_summary": {
                    "budget_name": budget.budget_name,
                    "category": budget.category,
                    "allocated_amount": budget.allocated_amount,
                    "spent_amount": budget.spent_amount,
                    "remaining_amount": budget.remaining_amount,
                    "alert_threshold": budget.alert_threshold,
                    "created_at": budget.created_at
                }
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error tracking expense or updating budget: {e}")
            report = {"error": f"Failed to track expense for budget '{budget_name}'. An unexpected error occurred: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetBudgetSummaryTool(BaseTool):
    """Retrieves a summary of a specific budget."""
    def __init__(self, tool_name="get_budget_summary"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves a summary of a specific budget, including allocated, spent, and remaining amounts, and a list of recent expenses."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"budget_name": {"type": "string", "description": "The name of the budget to retrieve the summary for."}},
            "required": ["budget_name"]
        }

    def execute(self, budget_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            budget = db.query(Budget).options(joinedload(Budget.expenses)).filter(Budget.budget_name == budget_name).first()
            if not budget:
                return json.dumps({"error": f"Budget '{budget_name}' not found."})
            
            expenses_list = [{
                "expense_id": e.expense_id,
                "amount": e.amount,
                "description": e.description,
                "timestamp": e.timestamp
            } for e in budget.expenses]
            
            report = {
                "budget_name": budget.budget_name,
                "category": budget.category,
                "allocated_amount": budget.allocated_amount,
                "spent_amount": budget.spent_amount,
                "remaining_amount": budget.remaining_amount,
                "alert_threshold_percent": budget.alert_threshold * 100,
                "recent_expenses": expenses_list
            }
        except Exception as e:
            logger.error(f"Error getting budget summary: {e}")
            report = {"error": f"Failed to get budget summary: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class SetBudgetAlertThresholdTool(BaseTool):
    """Sets an alert threshold for a budget."""
    def __init__(self, tool_name="set_budget_alert_threshold"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Sets an alert threshold for a budget, triggering a warning when a certain percentage of the allocated amount is spent."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "budget_name": {"type": "string", "description": "The name of the budget to set the threshold for."},
                "threshold_percent": {"type": "number", "description": "The percentage (0-100) at which to trigger an alert."}
            },
            "required": ["budget_name", "threshold_percent"]
        }

    def execute(self, budget_name: str, threshold_percent: float, **kwargs: Any) -> str:
        if not (0 <= threshold_percent <= 100):
            return json.dumps({"error": "Threshold percentage must be between 0 and 100."})
        
        db = next(get_db())
        try:
            budget = db.query(Budget).filter(Budget.budget_name == budget_name).first()
            if not budget:
                return json.dumps({"error": f"Budget '{budget_name}' not found."})

            budget.alert_threshold = threshold_percent / 100
            db.commit()
            db.refresh(budget)
            report = {"message": f"Alert threshold for budget '{budget_name}' set to {threshold_percent:.2f}%."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting budget alert threshold: {e}")
            report = {"error": f"Failed to set alert threshold for budget '{budget_name}'. An unexpected error occurred: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
