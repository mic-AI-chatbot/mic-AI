import logging
import json
import random
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SmartContract:
    """Represents a simulated smart contract with state and executable functions."""
    def __init__(self, contract_id: str, name: str, code: str, initial_state: Dict[str, Any]):
        self.contract_id = contract_id
        self.name = name
        self.code = code # Simulated code, not actually executed
        self.state = initial_state
        self.deployed_at = datetime.now().isoformat()

    def call_function(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates calling a function on the smart contract and modifying its state."""
        # This is a very simplified simulation. In reality, contract code would be executed.
        # Example functions:
        if function_name == "transfer" and "from_account" in params and "to_account" in params and "amount" in params:
            from_acc = params["from_account"]
            to_acc = params["to_account"]
            amount = params["amount"]
            if self.state.get("balances", {}).get(from_acc, 0) >= amount:
                self.state["balances"][from_acc] -= amount
                self.state["balances"][to_acc] = self.state.get("balances", {}).get(to_acc, 0) + amount
                return {"status": "success", "message": f"Transferred {amount} from {from_acc} to {to_acc}."}
            else:
                return {"status": "failed", "message": "Insufficient balance."}
        elif function_name == "update_owner" and "new_owner" in params:
            self.state["owner"] = params["new_owner"]
            return {"status": "success", "message": f"Owner updated to {params['new_owner']}."}
        else:
            return {"status": "failed", "message": f"Function '{function_name}' not found or invalid parameters for contract '{self.name}'."}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "name": self.name,
            "code_snippet": self.code[:50] + "..." if len(self.code) > 50 else self.code,
            "state": self.state,
            "deployed_at": self.deployed_at
        }

class Block:
    """Represents a single block in the simulated blockchain."""
    def __init__(self, index: int, transactions: List[Dict[str, Any]], previous_hash: str):
        self.index = index
        self.transactions = transactions
        self.timestamp = datetime.now().isoformat()
        self.previous_hash = previous_hash
        self.nonce = 0 # Simplified: no actual proof-of-work
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    """Manages the simulated blockchain, including blocks, pending transactions, and deployed smart contracts."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Blockchain, cls).__new__(cls)
            cls._instance.chain: List[Block] = []
            cls._instance.pending_transactions: List[Dict[str, Any]] = []
            cls._instance.contracts: Dict[str, SmartContract] = {}
            cls._instance.create_genesis_block()
        return cls._instance

    def create_genesis_block(self):
        self.chain.append(Block(0, [], "0"))

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, transaction: Dict[str, Any]):
        self.pending_transactions.append(transaction)

    def add_contract(self, contract: SmartContract):
        self.contracts[contract.contract_id] = contract

    def mine_pending_transactions(self) -> Block:
        # In a real blockchain, this would involve Proof-of-Work or Proof-of-Stake.
        # Here, we just create a new block with pending transactions.
        new_block = Block(len(self.chain), self.pending_transactions, self.last_block.hash)
        self.chain.append(new_block)
        self.pending_transactions = [] # Clear pending transactions
        return new_block

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_length": len(self.chain),
            "last_block_hash": self.last_block.hash,
            "pending_transactions_count": len(self.pending_transactions),
            "deployed_contracts_count": len(self.contracts)
        }

blockchain_instance = Blockchain()

class CreateSmartContractTool(BaseTool):
    """Creates and deploys a simple smart contract on the simulated blockchain."""
    def __init__(self, tool_name="create_smart_contract"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates and deploys a new smart contract on the simulated blockchain, defining its name, code, and initial state."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "A unique identifier for the smart contract."},
                "contract_name": {"type": "string", "description": "The name of the smart contract."},
                "contract_code": {"type": "string", "description": "The simulated code of the smart contract (e.g., a Solidity code snippet)."},
                "initial_state": {"type": "object", "description": "A dictionary representing the initial state variables of the contract (e.g., {'owner': 'address_A', 'balances': {'address_A': 100}})."}
            },
            "required": ["contract_id", "contract_name", "contract_code", "initial_state"]
        }

    def execute(self, contract_id: str, contract_name: str, contract_code: str, initial_state: Dict[str, Any], **kwargs: Any) -> str:
        if contract_id in blockchain_instance.contracts:
            return json.dumps({"error": f"Smart contract with ID '{contract_id}' already exists."})
        
        contract = SmartContract(contract_id, contract_name, contract_code, initial_state)
        blockchain_instance.add_contract(contract)
        
        report = {
            "message": f"Smart contract '{contract_name}' (ID: {contract_id}) deployed.",
            "contract_details": contract.to_dict()
        }
        return json.dumps(report, indent=2)

class TransactOnBlockchainTool(BaseTool):
    """Performs a transaction on the simulated blockchain, including smart contract calls."""
    def __init__(self, tool_name="transact_on_blockchain"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Performs a transaction on the simulated blockchain, either a direct transfer or a smart contract function call."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "transaction_type": {"type": "string", "description": "The type of transaction.", "enum": ["transfer", "contract_call"]},
                "sender": {"type": "string", "description": "The sender's address or ID."},
                "receiver": {"type": "string", "description": "Required for 'transfer': The receiver's address or ID."},
                "amount": {"type": "number", "description": "Required for 'transfer': The amount of cryptocurrency or tokens to transfer."},
                "contract_id": {"type": "string", "description": "Required for 'contract_call': The ID of the smart contract to interact with."},
                "function_name": {"type": "string", "description": "Required for 'contract_call': The name of the contract function to call."},
                "function_params": {
                    "type": "object",
                    "description": "Parameters for the contract function call (if applicable)."
                }
            },
            "required": ["transaction_type", "sender"]
        }

    def execute(self, transaction_type: str, sender: str, **kwargs: Any) -> str:
        transaction_details = {
            "transaction_id": f"tx_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}",  # nosec B311
            "type": transaction_type,
            "sender": sender,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        if transaction_type == "transfer":
            receiver = kwargs.get("receiver")
            amount = kwargs.get("amount")
            if receiver is None or amount is None:
                return json.dumps({"error": "Receiver and amount are required for 'transfer' transaction type."})
            transaction_details["receiver"] = receiver
            transaction_details["amount"] = amount
            blockchain_instance.add_transaction(transaction_details)
            message = f"Transfer of {amount} from {sender} to {receiver} added to pending transactions."
        elif transaction_type == "contract_call":
            contract_id = kwargs.get("contract_id")
            function_name = kwargs.get("function_name")
            function_params = kwargs.get("function_params", {})

            if contract_id is None or function_name is None:
                return json.dumps({"error": "Contract ID and function name are required for 'contract_call' transaction type."})

            contract = blockchain_instance.contracts.get(contract_id)
            if not contract:
                return json.dumps({"error": f"Smart contract with ID '{contract_id}' not found."})
            
            contract_call_result = contract.call_function(function_name, function_params)
            transaction_details["contract_id"] = contract_id
            transaction_details["function_name"] = function_name
            transaction_details["function_params"] = function_params
            transaction_details["contract_call_result"] = contract_call_result
            blockchain_instance.add_transaction(transaction_details)
            message = f"Smart contract '{contract_id}' function '{function_name}' called by {sender}. Result: {contract_call_result.get('status')}."
        else:
            return json.dumps({"error": f"Unsupported transaction type: {transaction_type}."})
            
        return json.dumps({"message": message, "transaction_details": transaction_details}, indent=2)

class GetBlockchainStatusTool(BaseTool):
    """Retrieves the current status of the simulated blockchain."""
    def __init__(self, tool_name="get_blockchain_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status of the simulated blockchain, including chain length, pending transactions, and deployed contracts."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        return json.dumps(blockchain_instance.to_dict(), indent=2)

class GetContractStateTool(BaseTool):
    """Retrieves the current state of a deployed smart contract."""
    def __init__(self, tool_name="get_contract_state"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current state variables of a deployed smart contract."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"contract_id": {"type": "string", "description": "The ID of the smart contract to retrieve the state for."}},
            "required": ["contract_id"]
        }

    def execute(self, contract_id: str, **kwargs: Any) -> str:
        contract = blockchain_instance.contracts.get(contract_id)
        if not contract:
            return json.dumps({"error": f"Smart contract with ID '{contract_id}' not found."})
            
        return json.dumps({"contract_id": contract_id, "current_state": contract.state}, indent=2)

class MinePendingTransactionsTool(BaseTool):
    """Mines pending transactions into a new block on the simulated blockchain."""
    def __init__(self, tool_name="mine_pending_transactions"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Mines all pending transactions into a new block on the simulated blockchain, adding it to the chain."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        if not blockchain_instance.pending_transactions:
            return json.dumps({"message": "No pending transactions to mine."})
        
        new_block = blockchain_instance.mine_pending_transactions()
        
        report = {
            "message": "Pending transactions mined into a new block.",
            "new_block_id": new_block.index,
            "new_block_hash": new_block.hash,
            "transactions_in_block": len(new_block.transactions)
        }
        return json.dumps(report, indent=2)