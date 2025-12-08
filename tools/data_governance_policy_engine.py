import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DG_POLICY_ENGINE_POLICIES_FILE = "dg_policy_engine_policies.json"

class DataGovernancePolicyEngine:
    """
    A tool for defining data governance policies and evaluating data assets
    against those policies. Policies are persisted in a local JSON file.
    """

    def __init__(self):
        """
        Initializes the DataGovernancePolicyEngine.
        Loads existing policies or creates a new one.
        """
        self.policies: Dict[str, Dict[str, Any]] = self._load_policies()

    def _load_policies(self) -> Dict[str, Dict[str, Any]]:
        """Loads data governance policies from a JSON file."""
        if os.path.exists(DG_POLICY_ENGINE_POLICIES_FILE):
            with open(DG_POLICY_ENGINE_POLICIES_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted policies file '{DG_POLICY_ENGINE_POLICIES_FILE}'. Starting with empty policies.")
                    return {}
        return {}

    def _save_policies(self) -> None:
        """Saves current data governance policies to a JSON file."""
        with open(DG_POLICY_ENGINE_POLICIES_FILE, 'w') as f:
            json.dump(self.policies, f, indent=4)

    def define_policy(self, policy_id: str, rules: Dict[str, Any], description: str) -> Dict[str, Any]:
        """
        Defines a new data governance policy.

        Args:
            policy_id: A unique identifier for the policy.
            rules: A dictionary defining the rules of the policy.
                   Example: {"data_type": "PII", "action": "mask", "min_age": 18}
            description: A description for the policy.

        Returns:
            A dictionary containing the details of the newly defined policy.
        """
        if not policy_id or not rules or not description:
            raise ValueError("Policy ID, rules, and description cannot be empty.")
        if policy_id in self.policies:
            raise ValueError(f"Policy with ID '{policy_id}' already exists.")

        new_policy = {
            "policy_id": policy_id,
            "description": description,
            "rules": rules,
            "defined_at": datetime.now().isoformat()
        }
        self.policies[policy_id] = new_policy
        self._save_policies()
        logger.info(f"Policy '{policy_id}' defined successfully.")
        return new_policy

    def evaluate_asset(self, policy_id: str, data_asset_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a data asset against a defined policy, returning a compliance status
        and any identified violations.

        Args:
            policy_id: The ID of the policy to evaluate against.
            data_asset_details: A dictionary containing details of the data asset to evaluate.
                                Example: {"asset_name": "customer_data", "data_type": "PII", "age": 25}

        Returns:
            A dictionary containing the evaluation result, including compliance status and violations.
        """
        if policy_id not in self.policies:
            raise ValueError(f"Policy with ID '{policy_id}' not found.")

        policy = self.policies[policy_id]
        rules = policy["rules"]
        
        compliance_status = "compliant"
        violations = []

        # Simulate evaluation based on policy rules
        # Rule 1: Check data_type
        if "data_type" in rules:
            required_data_type = rules["data_type"]
            asset_data_type = data_asset_details.get("data_type")
            if asset_data_type != required_data_type:
                violations.append(f"Data type mismatch: Policy requires '{required_data_type}', asset is '{asset_data_type}'.")
                compliance_status = "non-compliant"
        
        # Rule 2: Check min_age
        if "min_age" in rules and data_asset_details.get("age") is not None:
            required_min_age = rules["min_age"]
            asset_age = data_asset_details["age"]
            if asset_age < required_min_age:
                violations.append(f"Age violation: Asset age ({asset_age}) is below minimum required age ({required_min_age}).")
                compliance_status = "non-compliant"

        # Rule 3: Check required_fields
        if "required_fields" in rules:
            for field in rules["required_fields"]:
                if field not in data_asset_details or data_asset_details.get(field) is None:
                    violations.append(f"Missing required field: '{field}'.")
                    compliance_status = "non-compliant"

        evaluation_result = {
            "policy_id": policy_id,
            "data_asset_name": data_asset_details.get("asset_name", "N/A"),
            "compliance_status": compliance_status,
            "violations": violations,
            "evaluated_at": datetime.now().isoformat()
        }
        logger.info(f"Asset '{data_asset_details.get('asset_name', 'N/A')}' evaluated against policy '{policy_id}'. Status: {compliance_status}")
        return evaluation_result

    def list_policies(self) -> List[Dict[str, Any]]:
        """
        Lists all defined data governance policies.

        Returns:
            A list of dictionaries, each representing a defined policy.
        """
        return list(self.policies.values())

    def get_policy_details(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the full details of a specific data governance policy.

        Args:
            policy_id: The ID of the policy to retrieve.

        Returns:
            A dictionary containing the policy's details, or None if not found.
        """
        return self.policies.get(policy_id)

# Example usage (for direct script execution)
if __name__ == '__main__':
    print("Demonstrating DataGovernancePolicyEngine functionality...")

    engine = DataGovernancePolicyEngine()

    # --- Defining Policies ---
    print("\n--- Defining Policies ---")
    try:
        policy1 = engine.define_policy(
            policy_id="PII_Data_Policy",
            rules={"data_type": "PII", "required_fields": ["email", "name"]},
            description="Policy for handling Personally Identifiable Information."
        )
        print(f"Defined: {policy1['policy_id']}")

        policy2 = engine.define_policy(
            policy_id="Age_Restricted_Access",
            rules={"min_age": 18},
            description="Policy for data accessible only to adults."
        )
        print(f"Defined: {policy2['policy_id']}")
    except Exception as e:
        print(f"Policy definition failed: {e}")

    # --- Listing Policies ---
    print("\n--- Listing Policies ---")
    all_policies = engine.list_policies()
    print(json.dumps(all_policies, indent=2))

    # --- Evaluating Assets ---
    print("\n--- Evaluating Asset 1 (Compliant PII) ---")
    asset1 = {"asset_name": "customer_profile_db", "data_type": "PII", "email": "test@example.com", "name": "John Doe"}
    evaluation_result_1 = engine.evaluate_asset("PII_Data_Policy", asset1)
    print(json.dumps(evaluation_result_1, indent=2))

    print("\n--- Evaluating Asset 2 (Non-Compliant PII - missing field) ---")
    asset2 = {"asset_name": "customer_contact_list", "data_type": "PII", "email": "jane@example.com"}
    evaluation_result_2 = engine.evaluate_asset("PII_Data_Policy", asset2)
    print(json.dumps(evaluation_result_2, indent=2))

    print("\n--- Evaluating Asset 3 (Non-Compliant Age) ---")
    asset3 = {"asset_name": "user_activity_log", "age": 16}
    evaluation_result_3 = engine.evaluate_asset("Age_Restricted_Access", asset3)
    print(json.dumps(evaluation_result_3, indent=2))

    print("\n--- Evaluating Asset 4 (Compliant Age) ---")
    asset4 = {"asset_name": "user_activity_log_adults", "age": 25}
    evaluation_result_4 = engine.evaluate_asset("Age_Restricted_Access", asset4)
    print(json.dumps(evaluation_result_4, indent=2))

    # Clean up
    if os.path.exists(DG_POLICY_ENGINE_POLICIES_FILE):
        os.remove(DG_POLICY_ENGINE_POLICIES_FILE)
        print(f"\nCleaned up {DG_POLICY_ENGINE_POLICIES_FILE}")