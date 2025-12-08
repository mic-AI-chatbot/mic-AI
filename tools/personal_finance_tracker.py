import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Union, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalFinanceTrackerTool(BaseTool):
    """
    A tool to track personal finances by recording transactions, managing budgets,
    and providing summaries with persistence.
    """

    def __init__(self, tool_name: str = "PersonalFinanceTracker", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.transactions_file = os.path.join(self.data_dir, "finance_transactions.json")
        self.budgets_file = os.path.join(self.data_dir, "finance_budgets.json")
        
        self.transactions: List[Dict[str, Union[str, float]]] = self._load_data(self.transactions_file, default=[])
        self.budgets: Dict[str, float] = self._load_data(self.budgets_file, default={})

    @property
    def description(self) -> str:
        return "Tracks personal finances: records transactions, manages budgets, and provides summaries."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_transaction", "get_balance", "get_transactions", "set_budget", "get_budget_status"]},
                "transaction_type": {"type": "string", "enum": ["income", "expense"]},
                "amount": {"type": "number", "minimum": 0.01},
                "category": {"type": "string"},
                "description": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                "budget_amount": {"type": "number", "minimum": 0.01}
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

    def _save_transactions(self) -> None:
        with open(self.transactions_file, 'w') as f: json.dump(self.transactions, f, indent=2)

    def _save_budgets(self) -> None:
        with open(self.budgets_file, 'w') as f: json.dump(self.budgets, f, indent=2)

    def add_transaction(self, transaction_type: str, amount: float, category: str, description: str = "", date: Optional[str] = None) -> Dict[str, Any]:
        """Records a financial transaction (income or expense)."""
        if transaction_type.lower() not in ["income", "expense"]: raise ValueError("Invalid transaction type. Must be 'income' or 'expense'.")
        if amount <= 0: raise ValueError("Invalid amount. Must be a positive number.")
        if not category.strip(): raise ValueError("Invalid category. Must be a non-empty string.")
        
        if date is None: date = datetime.now().strftime("%Y-%m-%d")
        else:
            try: datetime.strptime(date, "%Y-%m-%d")
            except ValueError: raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

        transaction = {
            'type': transaction_type.lower(), 'amount': float(amount),
            'category': category.strip(), 'description': description.strip(), 'date': date
        }
        self.transactions.append(transaction)
        self._save_transactions()
        return {"status": "success", "message": f"Recorded {transaction_type} of ${amount:.2f} in {category} category on {date}."}

    def get_balance(self) -> Dict[str, Any]:
        """Calculates the current balance."""
        total_income = sum(t['amount'] for t in self.transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in self.transactions if t['type'] == 'expense')
        balance = total_income - total_expense
        return {"status": "success", "balance": round(balance, 2)}

    def get_transactions(self, transaction_type: Optional[str] = None, category: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves a list of transactions, optionally filtered."""
        filtered_transactions = self.transactions
        if transaction_type: filtered_transactions = [t for t in filtered_transactions if t['type'] == transaction_type.lower()]
        if category: filtered_transactions = [t for t in filtered_transactions if t['category'] == category.strip()]
        if start_date: filtered_transactions = [t for t in filtered_transactions if t['date'] >= start_date]
        if end_date: filtered_transactions = [t for t in filtered_transactions if t['date'] <= end_date]
        
        return filtered_transactions

    def set_budget(self, category: str, budget_amount: float) -> Dict[str, Any]:
        """Sets a budget for a specific category."""
        if budget_amount <= 0: raise ValueError("Invalid budget amount. Must be a positive number.")
        if not category.strip(): raise ValueError("Invalid category. Must be a non-empty string.")
        
        self.budgets[category.strip()] = budget_amount
        self._save_budgets()
        return {"status": "success", "message": f"Budget of ${budget_amount:.2f} set for category '{category}'."}

    def get_budget_status(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Gets the status of a budget, optionally for a specific category."""
        if not self.budgets: return {"status": "info", "message": "No budgets set yet."}

        budget_status = {}
        for cat, budgeted_amount in self.budgets.items():
            if category and cat != category: continue
            
            spent_amount = sum(t['amount'] for t in self.transactions if t['type'] == 'expense' and t['category'] == cat)
            remaining = budgeted_amount - spent_amount
            budget_status[cat] = {"budgeted": budgeted_amount, "spent": round(spent_amount, 2), "remaining": round(remaining, 2)}
        
        return {"status": "success", "budget_status": budget_status}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_transaction":
            return self.add_transaction(kwargs['transaction_type'], kwargs['amount'], kwargs['category'], kwargs.get('description', ''), kwargs.get('date'))
        elif operation == "get_balance":
            return self.get_balance()
        elif operation == "get_transactions":
            return self.get_transactions(kwargs.get('transaction_type'), kwargs.get('category'), kwargs.get('start_date'), kwargs.get('end_date'))
        elif operation == "set_budget":
            return self.set_budget(kwargs['category'], kwargs['budget_amount'])
        elif operation == "get_budget_status":
            return self.get_budget_status(kwargs.get('category'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PersonalFinanceTrackerTool functionality...")
    temp_dir = "temp_finance_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    finance_tracker = PersonalFinanceTrackerTool(data_dir=temp_dir)
    
    try:
        # 1. Add some income
        print("\n--- Adding income ---")
        finance_tracker.execute(operation="add_transaction", transaction_type="income", amount=2000.0, category="Salary", description="Monthly pay")
        print("Income added.")

        # 2. Add some expenses
        print("\n--- Adding expenses ---")
        finance_tracker.execute(operation="add_transaction", transaction_type="expense", amount=500.0, category="Rent", description="Monthly rent")
        finance_tracker.execute(operation="add_transaction", transaction_type="expense", amount=75.0, category="Groceries", description="Weekly groceries")
        finance_tracker.execute(operation="add_transaction", transaction_type="expense", amount=30.0, category="Groceries", description="Mid-week top-up")
        print("Expenses added.")

        # 3. Get current balance
        print("\n--- Getting current balance ---")
        balance = finance_tracker.execute(operation="get_balance")
        print(json.dumps(balance, indent=2))

        # 4. Set a budget
        print("\n--- Setting budget for Groceries ---")
        finance_tracker.execute(operation="set_budget", category="Groceries", budget_amount=100.0)
        print("Budget set.")

        # 5. Get budget status
        print("\n--- Getting budget status for Groceries ---")
        budget_status = finance_tracker.execute(operation="get_budget_status", category="Groceries")
        print(json.dumps(budget_status, indent=2))

        # 6. Get all expenses
        print("\n--- Getting all expenses ---")
        expenses = finance_tracker.execute(operation="get_transactions", transaction_type="expense")
        print(json.dumps(expenses, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")