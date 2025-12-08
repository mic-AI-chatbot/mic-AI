import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PrivacyEnhancingComputationSimulatorTool(BaseTool):
    """
    A tool that simulates privacy-enhancing computation (PEC), allowing for
    secure computations on sensitive data and data encryption without revealing
    the raw values.
    """

    def __init__(self, tool_name: str = "PrivacyEnhancingComputationSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.sensitive_data_file = os.path.join(self.data_dir, "sensitive_data.json")
        self.computation_results_file = os.path.join(self.data_dir, "pec_results.json")
        
        # Sensitive data: {data_id: {value: ..., encrypted_value: ...}}
        self.sensitive_data: Dict[str, Dict[str, Any]] = self._load_data(self.sensitive_data_file, default={})
        # Computation results: {result_id: {operation: ..., inputs: ..., output: ...}}
        self.computation_results: Dict[str, Dict[str, Any]] = self._load_data(self.computation_results_file, default={})

    @property
    def description(self) -> str:
        return "Simulates privacy-enhancing computation: secure computations on sensitive data and encryption."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["store_sensitive_data", "secure_computation", "encrypt_data"]},
                "data_id": {"type": "string"},
                "sensitive_value": {"type": "number"},
                "data_id_1": {"type": "string"},
                "data_id_2": {"type": "string"},
                "pec_operation": {"type": "string", "enum": ["add", "multiply"]},
                "method": {"type": "string", "enum": ["homomorphic_encryption", "smpc"], "default": "homomorphic_encryption"}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_sensitive_data(self):
        with open(self.sensitive_data_file, 'w') as f: json.dump(self.sensitive_data, f, indent=2)

    def _save_computation_results(self):
        with open(self.computation_results_file, 'w') as f: json.dump(self.computation_results, f, indent=2)

    def store_sensitive_data(self, data_id: str, sensitive_value: float) -> Dict[str, Any]:
        """Stores a piece of sensitive data."""
        if data_id in self.sensitive_data: raise ValueError(f"Data '{data_id}' already exists.")
        
        self.sensitive_data[data_id] = {
            "value": sensitive_value,
            "encrypted_value": f"ENC_{random.randint(10000, 99999)}", # Simulated encryption  # nosec B311
            "stored_at": datetime.now().isoformat()
        }
        self._save_sensitive_data()
        return {"status": "success", "message": f"Sensitive data '{data_id}' stored securely."}

    def secure_computation(self, data_id_1: str, data_id_2: str, pec_operation: str) -> Dict[str, Any]:
        """Simulates performing a secure computation on two pieces of sensitive data."""
        data1 = self.sensitive_data.get(data_id_1)
        data2 = self.sensitive_data.get(data_id_2)
        if not data1 or not data2: raise ValueError("Both data IDs must exist in sensitive data store.")
        
        result_id = f"comp_{data_id_1}_{data_id_2}_{pec_operation}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        actual_result = 0
        if pec_operation == "add":
            actual_result = data1["value"] + data2["value"]
        elif pec_operation == "multiply":
            actual_result = data1["value"] * data2["value"]
        else:
            raise ValueError(f"Unsupported PEC operation: {pec_operation}.")

        # Simulate encrypted computation result
        encrypted_result = f"ENC_RESULT_{random.randint(100000, 999999)}"  # nosec B311
        
        comp_result = {
            "id": result_id, "operation": pec_operation,
            "input_data_ids": [data_id_1, data_id_2],
            "simulated_encrypted_result": encrypted_result,
            "decrypted_result": actual_result, # This is the actual result, revealed after "decryption"
            "computed_at": datetime.now().isoformat()
        }
        self.computation_results[result_id] = comp_result
        self._save_computation_results()
        return comp_result

    def encrypt_data(self, data_id: str, method: str = "homomorphic_encryption") -> Dict[str, Any]:
        """Simulates encrypting sensitive data using a specified method."""
        data = self.sensitive_data.get(data_id)
        if not data: raise ValueError(f"Data '{data_id}' not found in sensitive data store.")
        
        # Simulate encryption
        encrypted_value = f"ENC_{method.upper()}_{random.randint(1000000, 9999999)}"  # nosec B311
        
        # Update the stored encrypted value
        self.sensitive_data[data_id]["encrypted_value"] = encrypted_value
        self._save_sensitive_data()
        
        return {"status": "success", "data_id": data_id, "encrypted_value": encrypted_value, "method": method}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "store_sensitive_data":
            data_id = kwargs.get('data_id')
            sensitive_value = kwargs.get('sensitive_value')
            if data_id is None or sensitive_value is None:
                raise ValueError("Missing 'data_id' or 'sensitive_value' for 'store_sensitive_data' operation.")
            return self.store_sensitive_data(data_id, sensitive_value)
        elif operation == "secure_computation":
            data_id_1 = kwargs.get('data_id_1')
            data_id_2 = kwargs.get('data_id_2')
            pec_operation = kwargs.get('pec_operation')
            if not all([data_id_1, data_id_2, pec_operation]):
                raise ValueError("Missing 'data_id_1', 'data_id_2', or 'pec_operation' for 'secure_computation' operation.")
            return self.secure_computation(data_id_1, data_id_2, pec_operation)
        elif operation == "encrypt_data":
            data_id = kwargs.get('data_id')
            if data_id is None:
                raise ValueError("Missing 'data_id' for 'encrypt_data' operation.")
            return self.encrypt_data(data_id, kwargs.get('method', 'homomorphic_encryption'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PrivacyEnhancingComputationSimulatorTool functionality...")
    temp_dir = "temp_pec_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    pec_tool = PrivacyEnhancingComputationSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Store sensitive data
        print("\n--- Storing sensitive data 'salary_alice' and 'bonus_alice' ---")
        pec_tool.execute(operation="store_sensitive_data", data_id="salary_alice", sensitive_value=75000.0)
        pec_tool.execute(operation="store_sensitive_data", data_id="bonus_alice", sensitive_value=15000.0)
        print("Sensitive data stored.")

        # 2. Perform a secure computation (addition)
        print("\n--- Performing secure addition of 'salary_alice' and 'bonus_alice' ---")
        sum_result = pec_tool.execute(operation="secure_computation", data_id="salary_alice", data_id_1="salary_alice", data_id_2="bonus_alice", pec_operation="add")
        print(json.dumps(sum_result, indent=2))

        # 3. Perform a secure computation (multiplication)
        print("\n--- Performing secure multiplication of 'salary_alice' and 'bonus_alice' ---")
        mult_result = pec_tool.execute(operation="secure_computation", data_id="salary_alice", data_id_1="salary_alice", data_id_2="bonus_alice", pec_operation="multiply")
        print(json.dumps(mult_result, indent=2))

        # 4. Encrypt a piece of data
        print("\n--- Encrypting 'salary_alice' using homomorphic encryption ---")
        encrypt_result = pec_tool.execute(operation="encrypt_data", data_id="salary_alice", method="homomorphic_encryption")
        print(json.dumps(encrypt_result, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")