import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated smart contracts and blockchain data
smart_contracts: Dict[str, Dict[str, Any]] = {}
blockchain_data: Dict[str, Any] = {"latest_block": 1000, "transactions": []}

class Web3DevelopmentKitTool(BaseTool):
    """
    A tool to simulate a Web3 development kit for managing smart contracts and blockchain interactions.
    """
    def __init__(self, tool_name: str = "web3_development_kit_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates Web3 development: deploy contracts, interact, and get blockchain data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'deploy_contract', 'interact_contract', 'get_data', 'list_contracts', 'list_transactions'."
                },
                "contract_code": {"type": "string", "description": "The Solidity code for the smart contract."},
                "contract_address": {"type": "string", "description": "The address of the deployed smart contract."},
                "function_name": {"type": "string", "description": "The name of the function to call on the contract."},
                "function_args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Arguments for the contract function."
                },
                "data_type": {
                    "type": "string",
                    "description": "Type of blockchain data to retrieve ('latest_block', 'transaction_details')."
                },
                "transaction_hash": {"type": "string", "description": "The hash of the transaction to get details for."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            contract_address = kwargs.get("contract_address")
            transaction_hash = kwargs.get("transaction_hash")

            if action in ['interact_contract'] and not contract_address:
                raise ValueError(f"'contract_address' is required for the '{action}' action.")
            if action == 'get_data' and kwargs.get('data_type') == 'transaction_details' and not transaction_hash:
                raise ValueError("'transaction_hash' is required for 'transaction_details' data_type.")

            actions = {
                "deploy_contract": self._deploy_smart_contract,
                "interact_contract": self._interact_with_contract,
                "get_data": self._get_blockchain_data,
                "list_contracts": self._list_contracts,
                "list_transactions": self._list_transactions,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in Web3DevelopmentKitTool: {e}")
            return {"error": str(e)}

    def _deploy_smart_contract(self, contract_code: str, **kwargs) -> Dict:
        if not contract_code:
            raise ValueError("'contract_code' is required to deploy a contract.")
            
        contract_address = f"0x{random.randint(0, 2**160 - 1):040x}" # Simulate Ethereum address  # nosec B311
        new_contract = {
            "address": contract_address,
            "code": contract_code,
            "owner": f"user_{random.randint(100, 999)}",  # nosec B311
            "status": "deployed",
            "deployed_at": datetime.now(timezone.utc).isoformat()
        }
        smart_contracts[contract_address] = new_contract
        logger.info(f"Smart contract deployed at {contract_address}.")
        return {"message": "Contract deployed successfully.", "details": new_contract}

    def _interact_with_contract(self, contract_address: str, function_name: str, function_args: List[str] = None, **kwargs) -> Dict:
        if contract_address not in smart_contracts:
            raise ValueError(f"Smart contract '{contract_address}' not found.")
        if not function_name:
            raise ValueError("'function_name' is required to interact with a contract.")
            
        transaction_hash = f"0x{random.randint(0, 2**256 - 1):064x}"  # nosec B311
        transaction_details = {
            "hash": transaction_hash,
            "contract_address": contract_address,
            "function": function_name,
            "args": function_args or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gas_used": random.randint(21000, 100000),  # nosec B311
            "status": random.choice(["success", "failed"])  # nosec B311
        }
        blockchain_data["transactions"].append(transaction_details)
        logger.info(f"Simulated interaction with contract '{contract_address}'.")
        return {"message": "Contract interaction simulated.", "transaction": transaction_details}

    def _get_blockchain_data(self, data_type: str, transaction_hash: Optional[str] = None, **kwargs) -> Dict:
        if data_type == "latest_block":
            blockchain_data["latest_block"] += random.randint(1, 10) # Simulate new blocks  # nosec B311
            return {"latest_block_number": blockchain_data["latest_block"]}
        elif data_type == "transaction_details":
            for tx in blockchain_data["transactions"]:
                if tx["hash"] == transaction_hash:
                    return {"transaction_details": tx}
            raise ValueError(f"Transaction '{transaction_hash}' not found.")
        else:
            raise ValueError(f"Unsupported data_type: '{data_type}'.")

    def _list_contracts(self, **kwargs) -> Dict:
        if not smart_contracts:
            return {"message": "No smart contracts deployed yet."}
        return {"deployed_contracts": list(smart_contracts.values())}

    def _list_transactions(self, **kwargs) -> Dict:
        if not blockchain_data["transactions"]:
            return {"message": "No transactions recorded yet."}
        return {"transactions": blockchain_data["transactions"]}