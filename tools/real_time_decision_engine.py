import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RealtimeDecisionEngineSimulatorTool(BaseTool):
    """
    A tool that simulates a real-time decision engine, allowing for defining
    decision rules and making decisions based on incoming data streams.
    """

    def __init__(self, tool_name: str = "RealtimeDecisionEngineSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.rules_file = os.path.join(self.data_dir, "decision_rules.json")
        self.logs_file = os.path.join(self.data_dir, "decision_logs.json")
        
        # Decision rules: {rule_id: {name: ..., conditions: {}, action: ...}}
        self.decision_rules: Dict[str, Dict[str, Any]] = self._load_data(self.rules_file, default={})
        # Decision logs: [{timestamp: ..., data_stream_id: ..., context: ..., decision: ...}]
        self.decision_logs: List[Dict[str, Any]] = self._load_data(self.logs_file, default=[])

    @property
    def description(self) -> str:
        return "Simulates a real-time decision engine: define rules and make decisions based on data streams."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_decision_rule", "make_decision", "get_decision_logs"]},
                "rule_id": {"type": "string"},
                "name": {"type": "string"},
                "conditions": {"type": "object", "description": "e.g., {'event_type': 'purchase', 'amount_gt': 100}"},
                "action": {"type": "string", "description": "e.g., 'send_alert', 'offer_discount'"},
                "data_stream_id": {"type": "string"},
                "decision_context": {"type": "object", "description": "The context for the decision (e.g., {'user_id': 'U1', 'event_type': 'purchase', 'amount': 150})."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_rules(self):
        with open(self.rules_file, 'w') as f: json.dump(self.decision_rules, f, indent=2)

    def _save_logs(self):
        with open(self.logs_file, 'w') as f: json.dump(self.decision_logs, f, indent=2)

    def define_decision_rule(self, rule_id: str, name: str, conditions: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Defines a new decision rule."""
        if rule_id in self.decision_rules: raise ValueError(f"Rule '{rule_id}' already exists.")
        
        new_rule = {
            "id": rule_id, "name": name, "conditions": conditions, "action": action,
            "defined_at": datetime.now().isoformat()
        }
        self.decision_rules[rule_id] = new_rule
        self._save_rules()
        return new_rule

    def make_decision(self, data_stream_id: str, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        """Makes a real-time decision based on defined rules and context."""
        triggered_rules = []
        final_decision = {"action": "no_action", "reason": "No rules triggered."}
        
        for rule_id, rule in self.decision_rules.items():
            conditions_met = True
            for condition_key, condition_value in rule["conditions"].items():
                context_value = decision_context.get(condition_key)
                
                if condition_key.endswith("_gt"): # Greater than
                    actual_key = condition_key[:-3]
                    if not (context_value is not None and context_value > condition_value):
                        conditions_met = False
                        break
                elif condition_key.endswith("_lt"): # Less than
                    actual_key = condition_key[:-3]
                    if not (context_value is not None and context_value < condition_value):
                        conditions_met = False
                        break
                else: # Exact match
                    if context_value != condition_value:
                        conditions_met = False
                        break
            
            if conditions_met:
                triggered_rules.append(rule_id)
                final_decision = {"action": rule["action"], "reason": f"Rule '{rule['name']}' triggered."}
                break # Only trigger the first matching rule for simplicity
        
        log_entry = {
            "timestamp": datetime.now().isoformat(), "data_stream_id": data_stream_id,
            "decision_context": decision_context, "triggered_rules": triggered_rules,
            "decision": final_decision
        }
        self.decision_logs.append(log_entry)
        self._save_logs()
        return final_decision

    def get_decision_logs(self) -> List[Dict[str, Any]]:
        """Retrieves all previously made decisions."""
        return self.decision_logs

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_decision_rule":
            rule_id = kwargs.get('rule_id')
            name = kwargs.get('name')
            conditions = kwargs.get('conditions')
            action = kwargs.get('action')
            if not all([rule_id, name, conditions, action]):
                raise ValueError("Missing 'rule_id', 'name', 'conditions', or 'action' for 'define_decision_rule' operation.")
            return self.define_decision_rule(rule_id, name, conditions, action)
        elif operation == "make_decision":
            data_stream_id = kwargs.get('data_stream_id')
            decision_context = kwargs.get('decision_context')
            if not all([data_stream_id, decision_context]):
                raise ValueError("Missing 'data_stream_id' or 'decision_context' for 'make_decision' operation.")
            return self.make_decision(data_stream_id, decision_context)
        elif operation == "get_decision_logs":
            # No additional kwargs required for get_decision_logs
            return self.get_decision_logs()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RealtimeDecisionEngineSimulatorTool functionality...")
    temp_dir = "temp_decision_engine_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    decision_engine = RealtimeDecisionEngineSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a rule for high-value purchases
        print("\n--- Defining decision rule 'high_value_purchase_alert' ---")
        decision_engine.execute(operation="define_decision_rule", rule_id="rule_001", name="High Value Purchase Alert",
                                conditions={"event_type": "purchase", "amount_gt": 1000}, action="send_fraud_alert")
        print("Rule defined.")

        # 2. Define a rule for offering discount on abandoned cart
        print("\n--- Defining decision rule 'abandoned_cart_discount' ---")
        decision_engine.execute(operation="define_decision_rule", rule_id="rule_002", name="Abandoned Cart Discount",
                                conditions={"event_type": "cart_abandoned", "items_count_gt": 1}, action="offer_10_percent_discount")
        print("Rule defined.")

        # 3. Make a decision (triggers high-value purchase alert)
        print("\n--- Making decision for high-value purchase ---")
        context1 = {"user_id": "U1", "event_type": "purchase", "amount": 1200, "location": "NY"}
        decision1 = decision_engine.execute(operation="make_decision", data_stream_id="ecomm_stream", decision_context=context1)
        print(json.dumps(decision1, indent=2))

        # 4. Make another decision (triggers abandoned cart discount)
        print("\n--- Making decision for abandoned cart ---")
        context2 = {"user_id": "U2", "event_type": "cart_abandoned", "items_count": 3}
        decision2 = decision_engine.execute(operation="make_decision", data_stream_id="ecomm_stream", decision_context=context2)
        print(json.dumps(decision2, indent=2))

        # 5. Make a decision (no rule triggered)
        print("\n--- Making decision for a regular event ---")
        context3 = {"user_id": "U3", "event_type": "page_view", "page": "/product/xyz"}
        decision3 = decision_engine.execute(operation="make_decision", data_stream_id="ecomm_stream", decision_context=context3)
        print(json.dumps(decision3, indent=2))

        # 6. Get decision logs
        print("\n--- Getting decision logs ---")
        logs = decision_engine.execute(operation="get_decision_logs")
        print(json.dumps(logs, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")