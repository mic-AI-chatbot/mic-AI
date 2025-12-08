import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

# Deferring transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered planning will not be available.")

logger = logging.getLogger(__name__)

CRISIS_PLANS_FILE = Path("crisis_plans.json")

class CrisisPlanManager:
    """Manages crisis plans, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CRISIS_PLANS_FILE):
        if cls._instance is None:
            cls._instance = super(CrisisPlanManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.plans: Dict[str, Any] = cls._instance._load_plans()
        return cls._instance

    def _load_plans(self) -> Dict[str, Any]:
        """Loads crisis plan information from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty plans.")
                return {}
            except Exception as e:
                logger.error(f"Error loading plans from {self.file_path}: {e}")
                return {}
        return {}

    def _save_plans(self) -> None:
        """Saves crisis plan information to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.plans, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving plans to {self.file_path}: {e}")

    def create_plan(self, plan_id: str, name: str, crisis_type: str, scope: str, objectives: List[str]) -> bool:
        if plan_id in self.plans:
            return False
        self.plans[plan_id] = {
            "name": name,
            "crisis_type": crisis_type,
            "scope": scope,
            "objectives": objectives,
            "status": "draft",
            "risk_assessment": {},
            "communication_strategy": {},
            "response_team": [],
            "created_at": datetime.now().isoformat() + "Z",
            "last_updated_at": datetime.now().isoformat() + "Z"
        }
        self._save_plans()
        return True

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        return self.plans.get(plan_id)

    def update_risk_assessment(self, plan_id: str, risk_level: str, description: str) -> bool:
        if plan_id not in self.plans:
            return False
        self.plans[plan_id]["risk_assessment"] = {
            "level": risk_level,
            "description": description,
            "assessed_at": datetime.now().isoformat() + "Z"
        }
        self.plans[plan_id]["last_updated_at"] = datetime.now().isoformat() + "Z"
        self._save_plans()
        return True

    def update_communication_strategy(self, plan_id: str, internal_strategy: str, external_strategy: str) -> bool:
        if plan_id not in self.plans:
            return False
        self.plans[plan_id]["communication_strategy"] = {
            "internal": internal_strategy,
            "external": external_strategy,
            "defined_at": datetime.now().isoformat() + "Z"
        }
        self.plans[plan_id]["last_updated_at"] = datetime.now().isoformat() + "Z"
        self._save_plans()
        return True

    def list_plans(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if not status:
            return [{"plan_id": p_id, "name": details['name'], "crisis_type": details['crisis_type'], "status": details['status'], "created_at": details['created_at']} for p_id, details in self.plans.items()]
        
        filtered_list = []
        for p_id, details in self.plans.items():
            if details['status'] == status:
                filtered_list.append({"plan_id": p_id, "name": details['name'], "crisis_type": details['crisis_type'], "status": details['status'], "created_at": details['created_at']})
        return filtered_list

crisis_plan_manager = CrisisPlanManager()

class CrisisPlanningModel:
    """Manages the text generation model for crisis planning tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrisisPlanningModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for crisis planning are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for crisis planning...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if self._generator is None:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

crisis_planning_model_instance = CrisisPlanningModel()

class CreateCrisisPlanTool(BaseTool):
    """Creates a new crisis plan in the crisis management system."""
    def __init__(self, tool_name="create_crisis_plan"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new crisis plan with a unique ID, name, crisis type, scope, and objectives."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "A unique ID for the crisis plan."},
                "name": {"type": "string", "description": "The name of the crisis plan."},
                "crisis_type": {"type": "string", "description": "The type of crisis the plan addresses.", "enum": ["cyber_attack", "natural_disaster", "reputation_crisis", "operational_failure"]},
                "scope": {"type": "string", "description": "The scope of the plan (e.g., 'IT systems', 'entire organization')."},
                "objectives": {"type": "array", "items": {"type": "string"}, "description": "A list of objectives for the plan (e.g., ['minimize downtime', 'ensure data recovery'])."}
            },
            "required": ["plan_id", "name", "crisis_type", "scope", "objectives"]
        }

    def execute(self, plan_id: str, name: str, crisis_type: str, scope: str, objectives: List[str], **kwargs: Any) -> str:
        success = crisis_plan_manager.create_plan(plan_id, name, crisis_type, scope, objectives)
        if success:
            report = {"message": f"Crisis plan '{plan_id}' ('{name}') created successfully. Status: draft."}
        else:
            report = {"error": f"Crisis plan with ID '{plan_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class AssessCrisisRiskTool(BaseTool):
    """Assesses risks for a crisis plan using an AI model."""
    def __init__(self, tool_name="assess_crisis_risk"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Assesses potential risks for a crisis plan, providing a risk level and description using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "The ID of the crisis plan to assess risks for."},
                "crisis_scenario": {"type": "string", "description": "A description of the crisis scenario to assess risks for."}
            },
            "required": ["plan_id", "crisis_scenario"]
        }

    def execute(self, plan_id: str, crisis_scenario: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered risk assessment."})

        plan = crisis_plan_manager.get_plan(plan_id)
        if not plan:
            return json.dumps({"error": f"Crisis plan '{plan_id}' not found. Please create it first."})
        
        prompt = f"Assess the risks for the crisis plan '{plan['name']}' (Crisis Type: {plan['crisis_type']}, Scope: {plan['scope']}, Objectives: {plan['objectives']}) given the following crisis scenario: '{crisis_scenario}'. Provide a risk level (Low, Medium, High, Critical) and a brief description of the assessment. Provide the output in JSON format with keys 'risk_level' and 'description'.\n\nJSON Output:"
        
        llm_response = crisis_planning_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 500)
        
        try:
            risk_assessment = json.loads(llm_response)
            success = crisis_plan_manager.update_risk_assessment(plan_id, risk_assessment.get("risk_level", "Unknown"), risk_assessment.get("description", "AI assessment."))
            if success:
                return json.dumps({"message": f"Risk assessed for plan '{plan_id}'.", "risk_assessment": risk_assessment}, indent=2)
            else:
                return json.dumps({"error": f"Failed to update risk assessment for plan '{plan_id}'. An unexpected error occurred."})
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class DefineCommunicationStrategyTool(BaseTool):
    """Defines a communication strategy for a crisis plan using an AI model."""
    def __init__(self, tool_name="define_communication_strategy"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Defines a communication strategy for a crisis plan, including internal and external communication guidelines, using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "The ID of the crisis plan to define the strategy for."},
                "crisis_scenario": {"type": "string", "description": "A description of the crisis scenario for which to define the strategy."}
            },
            "required": ["plan_id", "crisis_scenario"]
        }

    def execute(self, plan_id: str, crisis_scenario: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered strategy generation."})

        plan = crisis_plan_manager.get_plan(plan_id)
        if not plan:
            return json.dumps({"error": f"Crisis plan '{plan_id}' not found. Please create it first."})
        
        prompt = f"Define an internal and external communication strategy for the crisis plan '{plan['name']}' (Crisis Type: {plan['crisis_type']}, Scope: {plan['scope']}) given the following crisis scenario: '{crisis_scenario}'. Provide the strategy in JSON format with keys 'internal_strategy' and 'external_strategy'.\n\nJSON Output:"
        
        llm_response = crisis_planning_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        try:
            communication_strategy = json.loads(llm_response)
            success = crisis_plan_manager.update_communication_strategy(plan_id, communication_strategy.get("internal_strategy", "N/A"), communication_strategy.get("external_strategy", "N/A"))
            if success:
                return json.dumps({"message": f"Communication strategy defined for plan '{plan_id}'.", "strategy": communication_strategy}, indent=2)
            else:
                return json.dumps({"error": f"Failed to update communication strategy for plan '{plan_id}'. An unexpected error occurred."})
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})

class GetCrisisPlanDetailsTool(BaseTool):
    """Retrieves details of a specific crisis plan."""
    def __init__(self, tool_name="get_crisis_plan_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves details of a specific crisis plan, including its type, scope, objectives, risk assessment, and communication strategy."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"plan_id": {"type": "string", "description": "The ID of the crisis plan to retrieve details for."}},
            "required": ["plan_id"]
        }

    def execute(self, plan_id: str, **kwargs: Any) -> str:
        plan = crisis_plan_manager.get_plan(plan_id)
        if not plan:
            return json.dumps({"error": f"Crisis plan '{plan_id}' not found."})
            
        return json.dumps(plan, indent=2)

class ListCrisisPlansTool(BaseTool):
    """Lists all crisis plans."""
    def __init__(self, tool_name="list_crisis_plans"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all crisis plans, showing their ID, name, crisis type, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional: Filter plans by status.", "enum": ["draft", "active", "archived"], "default": None}
            },
            "required": []
        }

    def execute(self, status: Optional[str] = None, **kwargs: Any) -> str:
        plans = crisis_plan_manager.list_plans(status)
        if not plans:
            return json.dumps({"message": "No crisis plans found matching the criteria."})
        
        return json.dumps({"total_plans": len(plans), "crisis_plans": plans}, indent=2)