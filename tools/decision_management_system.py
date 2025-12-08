import logging
import os
import json
import re
import operator
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DecisionManagementSystemTool(BaseTool):
    """
    A tool for simulating a decision management system, allowing for the definition
    and execution of decision models, and logging of decision outcomes.
    """

    def __init__(self, tool_name: str = "decision_management_system"):
        super().__init__(tool_name=tool_name)
        self.models_file = "decision_models.json"
        self.logs_file = "decision_logs.json"
        self.models: Dict[str, Dict[str, Any]] = self._load_state(self.models_file)
        self.logs: List[Dict[str, Any]] = self._load_state(self.logs_file, is_list=True)

    @property
    def description(self) -> str:
        return "Defines and executes decision models, logs decision outcomes, and manages decision-making processes."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The decision management operation to perform.",
                    "enum": ["define_model", "execute_decision", "get_decision_logs", "list_models", "get_model_details"]
                },
                "model_id": {"type": "string"},
                "model_name": {"type": "string"},
                "rules": {"type": "array", "items": {"type": "object"}},
                "inputs": {"type": "array", "items": {"type": "string"}},
                "outputs": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string"},
                "input_data": {"type": "object"}
            },
            "required": ["operation"]
        }

    def _load_state(self, file_path: str, is_list: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted state file '{file_path}'. Starting fresh.")
                    return [] if is_list else {}
        return [] if is_list else {}

    def _save_state(self, state: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: str) -> None:
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=4)

    def _define_model(self, model_id: str, model_name: str, rules: List[Dict[str, Any]], inputs: List[str], outputs: List[str], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([model_id, model_name, rules, inputs, outputs]):
            raise ValueError("Model ID, name, rules, inputs, and outputs cannot be empty.")
        if model_id in self.models:
            raise ValueError(f"Decision model '{model_id}' already exists.")

        new_model = {
            "model_id": model_id, "model_name": model_name, "rules": rules,
            "inputs": inputs, "outputs": outputs, "description": description,
            "status": "defined", "defined_at": datetime.now().isoformat()
        }
        self.models[model_id] = new_model
        self._save_state(self.models, self.models_file)
        return new_model

    def _execute_decision(self, model_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        model = self.models.get(model_id)
        if not model: raise ValueError(f"Decision model '{model_id}' not found.")
        
        decision_outcome: Dict[str, Any] = {}
        execution_status = "completed"
        messages = []

        ops = {
            '==': operator.eq, '!=': operator.ne,
            '>': operator.gt, '<': operator.lt,
            '>=': operator.ge, '<=': operator.le
        }

        rule_matched = False
        for rule in model["rules"]:
            condition_str = rule.get("condition")
            action = rule.get("action")
            
            if condition_str:
                try:
                    # This is a simplified parser for demonstration. A robust solution would use a proper expression parser.
                    match = re.match(r"input\['\"](\w+)\[\'\"]\]\s*([<>=!]+)\s*(.*)", condition_str)
                    if match:
                        key, op_symbol, value_str = match.groups()
                        
                        if op_symbol not in ops:
                            raise ValueError(f"Unsupported operator '{op_symbol}' in condition.")
                        
                        op_func = ops[op_symbol]
                        
                        input_value = input_data.get(key)
                        if input_value is None:
                            condition_met = False
                        else:
                            compare_value = None
                            try:
                                # Attempt type conversion for comparison
                                if isinstance(input_value, (int, float)):
                                    compare_value = type(input_value)(value_str)
                                elif isinstance(input_value, bool):
                                    compare_value = value_str.lower() == 'true'
                                else: # Assume string comparison
                                    compare_value = value_str.strip("'\"")
                                condition_met = op_func(input_value, compare_value)
                            except (ValueError, TypeError):
                                condition_met = False # Type conversion failed, so condition not met
                        
                        if condition_met:
                            decision_outcome["rule_matched"] = rule
                            decision_outcome["action_taken"] = action
                            messages.append(f"Rule matched: '{condition_str}', Action: '{action}'.")
                            rule_matched = True
                            break
                    else:
                        messages.append(f"Could not parse condition '{condition_str}'.")
                        execution_status = "failed"

                except Exception as e:
                    messages.append(f"Error evaluating condition '{condition_str}': {e}")
                    execution_status = "failed"
            else:
                messages.append("Rule has no condition, skipping.")

        # Fallback logic if no rule matched
        if not rule_matched:
            messages.append("No rules matched, applying fallback logic.")
            for output_key in model["outputs"]:
                if output_key not in decision_outcome:
                    if output_key == "approval_status":
                        decision_outcome[output_key] = "Approved" if input_data.get("score", 0) > 70 else "Rejected"
                    elif output_key == "risk_level":
                        decision_outcome[output_key] = "High" if input_data.get("amount", 0) > 1000 else "Low"
                    else:
                        decision_outcome[output_key] = f"Simulated default {output_key}"

        log_entry = {
            "log_id": f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}",
            "model_id": model_id, "input_data": input_data, "outcome": decision_outcome,
            "status": execution_status, "messages": messages, "executed_at": datetime.now().isoformat()
        }
        self.logs.append(log_entry)
        self._save_state(self.logs, self.logs_file)
        return log_entry

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_model":
            return self._define_model(kwargs.get("model_id"), kwargs.get("model_name"), kwargs.get("rules"), kwargs.get("inputs"), kwargs.get("outputs"), kwargs.get("description"))
        elif operation == "execute_decision":
            return self._execute_decision(kwargs.get("model_id"), kwargs.get("input_data"))
        elif operation == "get_decision_logs":
            model_id = kwargs.get("model_id")
            if model_id: return [log for log in self.logs if log.get("model_id") == model_id]
            return self.logs
        elif operation == "list_models":
            return [{k: v for k, v in model.items() if k != "rules"} for model in self.models.values()]
        elif operation == "get_model_details":
            return self.models.get(kwargs.get("model_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DecisionManagementSystemTool functionality...")
    tool = DecisionManagementSystemTool()
    
    try:
        print("\n--- Defining Model ---")
        tool.execute(operation="define_model", model_id="loan_approval", model_name="Loan Approval", rules=[{"condition": "input['credit_score'] >= 700", "action": "Approve"}], inputs=["credit_score"], outputs=["approval_status"])
        
        print("\n--- Executing Decision ---")
        decision_result = tool.execute(operation="execute_decision", model_id="loan_approval", input_data={"credit_score": 750})
        print(json.dumps(decision_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.models_file): os.remove(tool.models_file)
        if os.path.exists(tool.logs_file): os.remove(tool.logs_file)
        print("\nCleanup complete.")