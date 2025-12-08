import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DistributedLedgerTechnologyIntegratorTool(BaseTool):
    """
    A tool for simulating Distributed Ledger Technology (DLT) integration actions.
    """

    def __init__(self, tool_name: str = "distributed_ledger_technology_integrator"):
        super().__init__(tool_name)
        self.ledger_file = "simulated_ledger.json"
        self.ledgers: Dict[str, Dict[str, Any]] = self._load_ledgers()

    @property
    def description(self) -> str:
        return "Simulates DLT integration: creates ledgers, submits transactions, and queries ledger data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The DLT operation to perform.",
                    "enum": ["create_ledger", "submit_transaction", "query_ledger", "list_ledgers", "get_ledger_details"]
                },
                "ledger_id": {"type": "string"},
                "ledger_name": {"type": "string"},
                "consensus_mechanism": {"type": "string"},
                "transaction_data": {"type": "object"},
                "query_type": {"type": "string", "enum": ["transactions", "blocks", "transaction_by_id"]},
                "query_params": {"type": "object"}
            },
            "required": ["operation"]
        }

    def _load_ledgers(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.ledger_file):
            with open(self.ledger_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted ledger file '{self.ledger_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_ledgers(self) -> None:
        with open(self.ledger_file, 'w') as f:
            json.dump(self.ledgers, f, indent=4)

    def _get_ledger(self, ledger_id: str) -> Dict[str, Any]:
        if ledger_id not in self.ledgers:
            raise ValueError(f"Ledger with ID '{ledger_id}' not found.")
        return self.ledgers[ledger_id]

    def _create_ledger(self, ledger_id: str, ledger_name: str, consensus_mechanism: str) -> Dict[str, Any]:
        if not all([ledger_id, ledger_name, consensus_mechanism]):
            raise ValueError("Ledger ID, name, and consensus mechanism cannot be empty.")
        if ledger_id in self.ledgers: raise ValueError(f"Ledger '{ledger_id}' already exists.")

        new_ledger = {
            "ledger_id": ledger_id, "ledger_name": ledger_name, "consensus_mechanism": consensus_mechanism,
            "created_at": datetime.now().isoformat(), "transactions": [], "blocks": []
        }
        self.ledgers[ledger_id] = new_ledger
        self._save_ledgers()
        return new_ledger

    def _submit_transaction(self, ledger_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        ledger = self._get_ledger(ledger_id)
        if not transaction_data: raise ValueError("Transaction data cannot be empty.")

        transaction_id = f"TX-{ledger_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_transaction = {
            "transaction_id": transaction_id, "data": transaction_data,
            "timestamp": datetime.now().isoformat(), "status": "pending"
        }
        ledger["transactions"].append(new_transaction)
        
        if not ledger["blocks"] or len(ledger["blocks"][-1]["transactions"]) >= 5:
            block_id = f"BLOCK-{ledger_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
            new_block = {
                "block_id": block_id, "timestamp": datetime.now().isoformat(),
                "transactions": [], "hash": f"HASH-{os.urandom(8).hex()}"
            }
            ledger["blocks"].append(new_block)
        
        ledger["blocks"][-1]["transactions"].append(new_transaction)
        new_transaction["status"] = "confirmed"
        
        self._save_ledgers()
        return new_transaction

    def _query_ledger(self, ledger_id: str, query_type: str, query_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        ledger = self._get_ledger(ledger_id)
        results: List[Dict[str, Any]] = []

        if query_type == "transactions": results = ledger["transactions"]
        elif query_type == "blocks": results = ledger["blocks"]
        elif query_type == "transaction_by_id":
            tx_id = query_params.get("transaction_id") if query_params else None
            if not tx_id: raise ValueError("Query type 'transaction_by_id' requires 'transaction_id' in query_params.")
            results = [tx for tx in ledger["transactions"] if tx.get("transaction_id") == tx_id]
        else: raise ValueError(f"Unsupported query type: '{query_type}'.")
        
        return results

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_ledger":
            return self._create_ledger(kwargs.get("ledger_id"), kwargs.get("ledger_name"), kwargs.get("consensus_mechanism"))
        elif operation == "submit_transaction":
            return self._submit_transaction(kwargs.get("ledger_id"), kwargs.get("transaction_data"))
        elif operation == "query_ledger":
            return self._query_ledger(kwargs.get("ledger_id"), kwargs.get("query_type"), kwargs.get("query_params"))
        elif operation == "list_ledgers":
            return [{k: v for k, v in ledger.items() if k not in ["transactions", "blocks"]} for ledger in self.ledgers.values()]
        elif operation == "get_ledger_details":
            return self.ledgers.get(kwargs.get("ledger_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DistributedLedgerTechnologyIntegratorTool functionality...")
    tool = DistributedLedgerTechnologyIntegratorTool()
    
    try:
        print("\n--- Creating Ledger ---")
        tool.execute(operation="create_ledger", ledger_id="supply_chain_ledger", ledger_name="Supply Chain Tracking", consensus_mechanism="PoS")
        
        print("\n--- Submitting Transaction ---")
        tx_result = tool.execute(operation="submit_transaction", ledger_id="supply_chain_ledger", transaction_data={"item": "Widget A", "quantity": 100})
        print(json.dumps(tx_result, indent=2))

        print("\n--- Querying Ledger ---")
        query_results = tool.execute(operation="query_ledger", ledger_id="supply_chain_ledger", query_type="transactions")
        print(json.dumps(query_results, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.ledger_file): os.remove(tool.ledger_file)
        print("\nCleanup complete.")
