import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DecentralizedIdentityManagerTool(BaseTool):
    """
    A tool for simulating a decentralized identity (DID) system.
    """

    def __init__(self, tool_name: str = "decentralized_identity_manager"):
        super().__init__(tool_name)
        self.dids_file = "dids.json"
        self.credentials_file = "credentials.json"
        self.dids: Dict[str, Dict[str, Any]] = self._load_state(self.dids_file)
        self.credentials: Dict[str, Dict[str, Any]] = self._load_state(self.credentials_file)

    @property
    def description(self) -> str:
        return "Simulates a decentralized identity system: creates DIDs, issues/verifies credentials, and manages identity data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The DID operation to perform.",
                    "enum": ["create_did", "issue_verifiable_credential", "verify_verifiable_credential", "list_dids", "list_credentials"]
                },
                "entity_name": {"type": "string"},
                "issuer_did": {"type": "string"},
                "holder_did": {"type": "string"},
                "credential_type": {"type": "string"},
                "claims": {"type": "object"},
                "credential_id": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_state(self, file_path: str) -> Dict[str, Any]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted state file '{file_path}'. Starting fresh.")
                    return {}
        return {}

    def _save_state(self, state: Dict[str, Any], file_path: str) -> None:
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=4)

    def _create_did(self, entity_name: str) -> Dict[str, Any]:
        if not entity_name: raise ValueError("Entity name cannot be empty.")
        did_id = f"did:example:{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_did = {
            "did": did_id, "entity_name": entity_name, "created_at": datetime.now().isoformat(), "status": "active"
        }
        self.dids[did_id] = new_did
        self._save_state(self.dids, self.dids_file)
        return new_did

    def _issue_verifiable_credential(self, issuer_did: str, holder_did: str, credential_type: str, claims: Dict[str, Any]) -> Dict[str, Any]:
        if not all([issuer_did, holder_did, credential_type, claims]):
            raise ValueError("Issuer DID, holder DID, credential type, and claims cannot be empty.")
        if issuer_did not in self.dids: raise ValueError(f"Issuer DID '{issuer_did}' not found.")
        if holder_did not in self.dids: raise ValueError(f"Holder DID '{holder_did}' not found.")

        credential_id = f"VC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_credential = {
            "credential_id": credential_id, "issuer_did": issuer_did, "holder_did": holder_did,
            "credential_type": credential_type, "claims": claims, "issued_at": datetime.now().isoformat(),
            "status": "valid"
        }
        self.credentials[credential_id] = new_credential
        self._save_state(self.credentials, self.credentials_file)
        return new_credential

    def _verify_verifiable_credential(self, credential_id: str) -> Dict[str, Any]:
        credential = self.credentials.get(credential_id)
        if not credential: raise ValueError(f"Verifiable credential '{credential_id}' not found.")
        
        is_valid = (credential["status"] == "valid")
        verification_result = {
            "credential_id": credential_id, "issuer_did": credential["issuer_did"],
            "holder_did": credential["holder_did"], "credential_type": credential["credential_type"],
            "claims_summary": credential["claims"], "is_valid": is_valid,
            "verified_at": datetime.now().isoformat(),
            "message": "Credential is valid." if is_valid else "Credential is not valid."
        }
        return verification_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_did":
            return self._create_did(kwargs.get("entity_name"))
        elif operation == "issue_verifiable_credential":
            return self._issue_verifiable_credential(kwargs.get("issuer_did"), kwargs.get("holder_did"), kwargs.get("credential_type"), kwargs.get("claims"))
        elif operation == "verify_verifiable_credential":
            return self._verify_verifiable_credential(kwargs.get("credential_id"))
        elif operation == "list_dids":
            return list(self.dids.values())
        elif operation == "list_credentials":
            holder_did = kwargs.get("holder_did")
            if holder_did: return [c for c in self.credentials.values() if c.get("holder_did") == holder_did]
            return list(self.credentials.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DecentralizedIdentityManagerTool functionality...")
    tool = DecentralizedIdentityManagerTool()
    
    try:
        print("\n--- Creating DIDs ---")
        issuer_did_info = tool.execute(operation="create_did", entity_name="University of Example")
        issuer_did = issuer_did_info["did"]
        holder_did_info = tool.execute(operation="create_did", entity_name="Alice Smith")
        holder_did = holder_did_info["did"]
        
        print("\n--- Issuing Verifiable Credential ---")
        credential_info = tool.execute(operation="issue_verifiable_credential", issuer_did=issuer_did, holder_did=holder_did, credential_type="BachelorDegree", claims={"degree": "Computer Science"})
        credential_id = credential_info["credential_id"]

        print("\n--- Verifying Verifiable Credential ---")
        verification_result = tool.execute(operation="verify_verifiable_credential", credential_id=credential_id)
        print(json.dumps(verification_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.dids_file): os.remove(tool.dids_file)
        if os.path.exists(tool.credentials_file): os.remove(tool.credentials_file)
        print("\nCleanup complete.")