import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SecretManagementSimulatorTool(BaseTool):
    """
    A tool that simulates a secret management solution, allowing for storing,
    retrieving, and deleting secrets securely.
    """

    def __init__(self, tool_name: str = "SecretManagementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.secrets_file = os.path.join(self.data_dir, "managed_secrets.json")
        # Secrets structure: {secret_name: {value: "obfuscated_value", created_at: ..., last_accessed_at: ...}}
        self.secrets: Dict[str, Dict[str, Any]] = self._load_data(self.secrets_file, default={})

    @property
    def description(self) -> str:
        return "Simulates secret management: store, retrieve, and delete secrets securely."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["store_secret", "retrieve_secret", "delete_secret", "list_secrets"]},
                "secret_name": {"type": "string"},
                "secret_value": {"type": "string", "description": "The value of the secret to store."}
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

    def _save_data(self):
        with open(self.secrets_file, 'w') as f: json.dump(self.secrets, f, indent=2)

    def store_secret(self, secret_name: str, secret_value: str) -> Dict[str, Any]:
        """Stores a secret securely (simulated obfuscation)."""
        if secret_name in self.secrets: raise ValueError(f"Secret '{secret_name}' already exists. Use a different name or delete first.")
        
        # Simulate obfuscation
        obfuscated_value = f"OBFUSCATED_{random.randint(100000, 999999)}"  # nosec B311
        
        new_secret = {
            "name": secret_name, "value": obfuscated_value, # Store obfuscated value
            "created_at": datetime.now().isoformat(), "last_accessed_at": None
        }
        self.secrets[secret_name] = new_secret
        self._save_data()
        return {"status": "success", "message": f"Secret '{secret_name}' stored securely."}

    def retrieve_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieves a secret (simulated decryption)."""
        secret = self.secrets.get(secret_name)
        if not secret: raise ValueError(f"Secret '{secret_name}' not found.")
        
        # Simulate decryption
        decrypted_value = f"DECRYPTED_VALUE_FOR_{secret_name}"
        
        secret["last_accessed_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "secret_name": secret_name, "secret_value": decrypted_value}

    def delete_secret(self, secret_name: str) -> Dict[str, Any]:
        """Deletes a secret."""
        if secret_name not in self.secrets: raise ValueError(f"Secret '{secret_name}' not found.")
        
        del self.secrets[secret_name]
        self._save_data()
        return {"status": "success", "message": f"Secret '{secret_name}' deleted successfully."}

    def list_secrets(self) -> List[Dict[str, Any]]:
        """Lists all stored secrets (names only)."""
        return [{
            "name": name, "created_at": secret["created_at"]
        } for name, secret in self.secrets.items()]

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "store_secret":
            secret_name = kwargs.get('secret_name')
            secret_value = kwargs.get('secret_value')
            if not all([secret_name, secret_value]):
                raise ValueError("Missing 'secret_name' or 'secret_value' for 'store_secret' operation.")
            return self.store_secret(secret_name, secret_value)
        elif operation == "retrieve_secret":
            secret_name = kwargs.get('secret_name')
            if not secret_name:
                raise ValueError("Missing 'secret_name' for 'retrieve_secret' operation.")
            return self.retrieve_secret(secret_name)
        elif operation == "delete_secret":
            secret_name = kwargs.get('secret_name')
            if not secret_name:
                raise ValueError("Missing 'secret_name' for 'delete_secret' operation.")
            return self.delete_secret(secret_name)
        elif operation == "list_secrets":
            # No additional kwargs required for list_secrets
            return self.list_secrets()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SecretManagementSimulatorTool functionality...")
    temp_dir = "temp_secret_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    secret_manager = SecretManagementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Store a secret
        print("\n--- Storing secret 'API_KEY_SERVICE_X' ---")
        secret_manager.execute(operation="store_secret", secret_name="API_KEY_SERVICE_X", secret_value="DEMO_VALUE_12345")
        print("Secret stored.")

        # 2. Retrieve the secret
        print("\n--- Retrieving secret 'API_KEY_SERVICE_X' ---")
        retrieved_secret = secret_manager.execute(operation="retrieve_secret", secret_name="API_KEY_SERVICE_X") # nosec B106
        print(json.dumps(retrieved_secret, indent=2))

        # 3. Store another secret
        print("\n--- Storing secret 'DB_PASSWORD_PROD' ---")
        secret_manager.execute(operation="store_secret", secret_name="DB_PASSWORD_PROD", secret_value="DEMO_VALUE_67890")
        print("Secret stored.")

        # 4. List all secrets
        print("\n--- Listing all secrets ---")
        all_secrets = secret_manager.execute(operation="list_secrets", secret_name="any") # nosec B106
        print(json.dumps(all_secrets, indent=2))

        # 5. Delete a secret
        print("\n--- Deleting secret 'API_KEY_SERVICE_X' ---")
        secret_manager.execute(operation="delete_secret", secret_name="API_KEY_SERVICE_X") # nosec B106
        print("Secret deleted.")

        # 6. List all secrets again
        print("\n--- Listing all secrets after deletion ---")
        all_secrets_after_delete = secret_manager.execute(operation="list_secrets", secret_name="any") # nosec B106
        print(json.dumps(all_secrets_after_delete, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")