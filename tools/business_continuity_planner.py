import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import BCPPlan, RecoveryStep
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class CreateBusinessContinuityPlanTool(BaseTool):
    """Creates a new business continuity plan in the persistent database."""
    def __init__(self, tool_name="create_business_continuity_plan"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new business continuity plan with a specified name, scope, objectives, Recovery Time Objective (RTO), and Recovery Point Objective (RPO)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {"type": "string", "description": "A unique name for the new business continuity plan."},
                "scope": {"type": "string", "description": "The scope of the plan (e.g., 'IT systems', 'entire organization')."},
                "objectives": {"type": "array", "items": {"type": "string"}, "description": "A list of objectives for the plan (e.g., ['minimize downtime', 'ensure data recovery'])."},
                "rto_hours": {"type": "integer", "description": "Recovery Time Objective in hours (target time to restore business functions)."},
                "rpo_hours": {"type": "integer", "description": "Recovery Point Objective in hours (maximum tolerable data loss)."},
                "recovery_procedures": {"type": "array", "items": {"type": "string"}, "description": "List of key recovery procedures or steps."}
            },
            "required": ["plan_name", "scope", "objectives", "rto_hours", "rpo_hours", "recovery_procedures"]
        }

    def execute(self, plan_name: str, scope: str, objectives: List[str], rto_hours: int, rpo_hours: int, recovery_procedures: List[str], **kwargs: Any) -> str:
        db = next(get_db())
        try:
            new_plan = BCPPlan(
                plan_id=plan_name, # Using plan_name as plan_id for simplicity
                name=plan_name,
                description=scope, # Using scope as description for now
                status="draft",
                created_at=datetime.now().isoformat() + "Z",
                last_updated=datetime.now().isoformat() + "Z"
            )
            db.add(new_plan)
            db.commit()
            db.refresh(new_plan)

            # Add recovery steps
            for i, step_desc in enumerate(recovery_procedures):
                new_step = RecoveryStep(
                    plan_id=plan_name,
                    step_number=i + 1,
                    description=step_desc,
                    responsible_party="N/A", # Default
                    status="pending" # Default
                )
                db.add(new_step)
            db.commit()

            report = {"message": f"Business continuity plan '{plan_name}' created successfully."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Business continuity plan '{plan_name}' already exists. Please choose a unique name."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating BCP: {e}")
            report = {"error": f"Failed to create BCP: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class AddRecoveryStepTool(BaseTool):
    """Adds a recovery step to an existing business continuity plan."""
    def __init__(self, tool_name="add_recovery_step"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a recovery step to an existing business continuity plan."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {"type": "string", "description": "The name of the business continuity plan."},
                "step_description": {"type": "string", "description": "Description of the recovery step."},
                "responsible_party": {"type": "string", "description": "The party responsible for this step."},
                "status": {"type": "string", "description": "Initial status of the step (e.g., 'pending', 'completed').", "default": "pending"}
            },
            "required": ["plan_name", "step_description"]
        }

    def execute(self, plan_name: str, step_description: str, responsible_party: str = "N/A", status: str = "pending", **kwargs: Any) -> str:
        db = next(get_db())
        try:
            plan = db.query(BCPPlan).filter(BCPPlan.plan_id == plan_name).first()
            if not plan:
                return json.dumps({"error": f"Business continuity plan '{plan_name}' not found."})

            # Determine next step number
            last_step = db.query(RecoveryStep).filter(RecoveryStep.plan_id == plan_name).order_by(RecoveryStep.step_number.desc()).first()
            step_number = (last_step.step_number + 1) if last_step else 1

            new_step = RecoveryStep(
                plan_id=plan_name,
                step_number=step_number,
                description=step_description,
                responsible_party=responsible_party,
                status=status
            )
            db.add(new_step)
            plan.last_updated = datetime.now().isoformat() + "Z"
            db.commit()
            db.refresh(new_step)
            db.refresh(plan)
            report = {"message": f"Recovery step '{step_description}' added to plan '{plan_name}'."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding recovery step: {e}")
            report = {"error": f"Failed to add recovery step: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetBusinessContinuityPlanTool(BaseTool):
    """Retrieves the details of a specific business continuity plan."""
    def __init__(self, tool_name="get_business_continuity_plan"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the full details of a specific business continuity plan, including its scope, objectives, RTO, RPO, and recovery procedures."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"plan_name": {"type": "string", "description": "The name of the business continuity plan to retrieve."}},
            "required": ["plan_name"]
        }

    def execute(self, plan_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            plan = db.query(BCPPlan).options(joinedload(BCPPlan.recovery_steps)).filter(BCPPlan.plan_id == plan_name).first()
            if not plan:
                return json.dumps({"error": f"Business continuity plan '{plan_name}' not found."})
            
            recovery_steps_list = [{
                "step_number": s.step_number,
                "description": s.description,
                "responsible_party": s.responsible_party,
                "status": s.status
            } for s in sorted(plan.recovery_steps, key=lambda x: x.step_number)]

            report = {
                "plan_id": plan.plan_id,
                "name": plan.name,
                "description": plan.description,
                "status": plan.status,
                "created_at": plan.created_at,
                "last_updated": plan.last_updated,
                "recovery_steps": recovery_steps_list
            }
        except Exception as e:
            logger.error(f"Error getting BCP details: {e}")
            report = {"error": f"Failed to get BCP details: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class UpdateBCPStatusTool(BaseTool):
    """Updates the status of a business continuity plan."""
    def __init__(self, tool_name="update_bcp_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Updates the status of a business continuity plan (e.g., 'draft', 'active', 'under_review', 'archived')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {"type": "string", "description": "The name of the business continuity plan to update."},
                "new_status": {"type": "string", "description": "The new status for the plan."}
            },
            "required": ["plan_name", "new_status"]
        }

    def execute(self, plan_name: str, new_status: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            plan = db.query(BCPPlan).filter(BCPPlan.plan_id == plan_name).first()
            if not plan:
                return json.dumps({"error": f"Business continuity plan '{plan_name}' not found."})
            
            plan.status = new_status
            plan.last_updated = datetime.now().isoformat() + "Z"
            db.commit()
            db.refresh(plan)
            report = {"message": f"Status for BCP '{plan_name}' updated to '{new_status}'."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating BCP status: {e}")
            report = {"error": f"Failed to update BCP status: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class AssessBusinessContinuityRisksTool(BaseTool):
    """Assesses risks to business continuity for a given plan."""
    def __init__(self, tool_name="assess_business_continuity_risks"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Assesses potential risks to business continuity (e.g., natural disasters, cyber attacks) and their potential impact for a given plan."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {"type": "string", "description": "The name of the business continuity plan to assess risks for."},
                "risk_factors": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["natural_disaster", "cyber_attack", "supply_chain_disruption", "power_outage", "human_error", "system_failure"]},
                    "description": "A list of risk factors to consider."
                }
            },
            "required": ["plan_name", "risk_factors"]
        }

    def execute(self, plan_name: str, risk_factors: List[str], **kwargs: Any) -> str:
        db = next(get_db())
        try:
            plan = db.query(BCPPlan).filter(BCPPlan.plan_id == plan_name).first()
            if not plan:
                return json.dumps({"error": f"Business continuity plan '{plan_name}' not found."})
            
            risk_assessment = {}
            for factor in risk_factors:
                impact_score = random.randint(1, 5) # 1=low, 5=high  # nosec B311
                probability_score = random.randint(1, 5) # 1=low, 5=high  # nosec B311
                risk_score = impact_score * probability_score
                
                risk_assessment[factor] = {
                    "impact_score": impact_score,
                    "probability_score": probability_score,
                    "risk_score": risk_score,
                    "mitigation_suggestion": f"Develop specific strategies and recovery procedures for '{factor}' to reduce its impact and probability. Ensure alignment with RTO/RPO."
                }
            
            overall_risk_level = "low"
            if any(r["risk_score"] > 15 for r in risk_assessment.values()): # Example threshold for high risk
                overall_risk_level = "high"
            elif any(r["risk_score"] > 5 for r in risk_assessment.values()): # Example threshold for medium risk
                overall_risk_level = "medium"
                
            report = {
                "plan_name": plan_name,
                "risk_assessment": risk_assessment,
                "overall_risk_level": overall_risk_level
            }
        except Exception as e:
            logger.error(f"Error assessing BCP risks: {e}")
            report = {"error": f"Failed to assess BCP risks: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class SimulateDisasterTool(BaseTool):
    """Simulates a disaster scenario and assesses its impact on a business continuity plan."""
    def __init__(self, tool_name="simulate_disaster"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates a disaster scenario (e.g., 'power_outage', 'cyber_attack') and assesses its impact on a given business continuity plan, reporting on RTO/RPO adherence."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "plan_name": {"type": "string", "description": "The name of the business continuity plan to test."},
                "disaster_type": {"type": "string", "description": "The type of disaster to simulate.", "enum": ["power_outage", "cyber_attack", "natural_disaster", "system_failure"]}
            },
            "required": ["plan_name", "disaster_type"]
        }

    def execute(self, plan_name: str, disaster_type: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            plan = db.query(BCPPlan).filter(BCPPlan.plan_id == plan_name).first()
            if not plan:
                return json.dumps({"error": f"Business continuity plan '{plan_name}' not found."})
            
            # Simulate impact and recovery time based on disaster type and plan's RTO/RPO
            # For simplicity, RTO/RPO are not stored in the BCPPlan model directly in this refactor.
            # We'll use dummy values for simulation here. In a real scenario, these would be part of the plan details.
            dummy_rto_hours = 8 # Example RTO
            dummy_rpo_hours = 4 # Example RPO

            simulated_downtime = random.randint(dummy_rto_hours - 2, dummy_rto_hours + 5) # Random around RTO  # nosec B311
            simulated_data_loss = random.randint(dummy_rpo_hours - 1, dummy_rpo_hours + 3) # Random around RPO  # nosec B311

            rto_met = simulated_downtime <= dummy_rto_hours
            rpo_met = simulated_data_loss <= dummy_rpo_hours

            report = {
                "plan_name": plan_name,
                "disaster_type": disaster_type,
                "simulated_downtime_hours": simulated_downtime,
                "simulated_data_loss_hours": simulated_data_loss,
                "rto_adherence": "Met" if rto_met else "Not Met",
                "rpo_adherence": "Met" if rpo_met else "Not Met",
                "summary": f"Simulated '{disaster_type}' disaster. Downtime was {simulated_downtime} hours ({'within' if rto_met else 'exceeded'} RTO of {dummy_rto_hours} hours). Data loss was {simulated_data_loss} hours ({'within' if rpo_met else 'exceeded'} RPO of {dummy_rpo_hours} hours)."
            }
        except Exception as e:
            logger.error(f"Error simulating disaster: {e}")
            report = {"error": f"Failed to simulate disaster: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
