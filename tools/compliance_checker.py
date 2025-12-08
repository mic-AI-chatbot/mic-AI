import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import ComplianceCheck
from sqlalchemy.exc import IntegrityError

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered report generation will not be available.")

logger = logging.getLogger(__name__)

class ComplianceReportModel:
    """Manages the text generation model for compliance report generation, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ComplianceReportModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for compliance report generation are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for compliance reports...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

compliance_report_model_instance = ComplianceReportModel()

class CheckComplianceTool(BaseTool):
    """Checks compliance against a set of regulations or standards and stores results persistently."""
    def __init__(self, tool_name="check_compliance"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Checks a system or process against a specified set of regulations or industry standards, returning a compliance status and storing results persistently."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "check_id": {"type": "string", "description": "A unique ID for this compliance check."},
                "system_or_process": {"type": "string", "description": "The system or process to check for compliance (e.g., 'data_handling_process', 'web_application')."},
                "regulations_or_standards": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["GDPR", "ISO_27001", "HIPAA", "PCI_DSS", "SOC_2"]},
                    "description": "A list of regulations or standards to check against."
                }
            },
            "required": ["check_id", "system_or_process", "regulations_or_standards"]
        }

    def execute(self, check_id: str, system_or_process: str, regulations_or_standards: List[str], **kwargs: Any) -> str:
        db = next(get_db())
        try:
            if db.query(ComplianceCheck).filter(ComplianceCheck.check_id == check_id).first():
                return json.dumps({"error": f"Compliance check with ID '{check_id}' already exists. Please choose a unique ID."})

            compliance_status = {}
            overall_status = "compliant"
            
            for regulation in regulations_or_standards:
                # Simulate compliance based on keywords or random chance
                is_compliant = random.choice([True, False])  # nosec B311
                if "GDPR" in regulation and "data_handling" in system_or_process:
                    is_compliant = random.random() < 0.7 # 70% compliant for GDPR data handling  # nosec B311
                elif "HIPAA" in regulation and "medical" in system_or_process:
                    is_compliant = random.random() < 0.6 # 60% compliant for HIPAA medical  # nosec B311
                
                compliance_status[regulation] = {
                    "status": "Compliant" if is_compliant else "Non-Compliant",
                    "details": f"Simulated check against {regulation}. {'All requirements met.' if is_compliant else 'Some requirements not met.'}"
                }
                if not is_compliant:
                    overall_status = "non-compliant"
            
            now = datetime.now().isoformat() + "Z"
            new_check = ComplianceCheck(
                check_id=check_id,
                system_or_process=system_or_process,
                regulations_or_standards=json.dumps(regulations_or_standards),
                compliance_status=json.dumps(compliance_status),
                overall_status=overall_status,
                checked_at=now
            )
            db.add(new_check)
            db.commit()
            db.refresh(new_check)
            
            report = {
                "message": f"Compliance check '{check_id}' for '{system_or_process}' completed.",
                "check_id": check_id,
                "system_or_process": system_or_process,
                "overall_status": overall_status,
                "details": compliance_status
            }
        except IntegrityError:
            db.rollback()
            report = {"error": f"Compliance check with ID '{check_id}' already exists. Please choose a unique ID."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding compliance check: {e}")
            report = {"error": f"Failed to record compliance check: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GenerateComplianceReportTool(BaseTool):
    """Generates a detailed compliance report based on a compliance check using an AI model."""
    def __init__(self, tool_name="generate_compliance_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a detailed compliance report based on the results of a compliance check, including findings and recommendations, using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "check_id": {"type": "string", "description": "The ID of the compliance check to generate a report for."},
                "report_format": {"type": "string", "description": "The desired format for the report.", "enum": ["markdown", "text"], "default": "markdown"}
            },
            "required": ["check_id"]
        }

    def execute(self, check_id: str, report_format: str = "markdown", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed for AI-powered report generation."})

        db = next(get_db())
        try:
            check_results = db.query(ComplianceCheck).filter(ComplianceCheck.check_id == check_id).first()
            if not check_results:
                return json.dumps({"error": f"Compliance check with ID '{check_id}' not found."})
            
            prompt = f"Generate a detailed compliance report for the system/process '{check_results.system_or_process}' based on the following compliance check results: {check_results.compliance_status}. The overall status is '{check_results.overall_status}'. The report should include an executive summary, detailed findings by regulation, and actionable recommendations. Format the report as {report_format}.\n\nCompliance Report:"
            
            generated_report_content = compliance_report_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
            
            report = {
                "check_id": check_id,
                "system_or_process": check_results.system_or_process,
                "overall_status": check_results.overall_status,
                "report_format": report_format,
                "report_content": generated_report_content
            }
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            report = {"error": f"Failed to generate compliance report: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetComplianceCheckDetailsTool(BaseTool):
    """Retrieves the details of a specific compliance check."""
    def __init__(self, tool_name="get_compliance_check_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the full details of a specific compliance check, including the system/process, regulations, and compliance status for each."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"check_id": {"type": "string", "description": "The ID of the compliance check to retrieve details for."}},
            "required": ["check_id"]
        }

    def execute(self, check_id: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            check = db.query(ComplianceCheck).filter(ComplianceCheck.check_id == check_id).first()
            if not check:
                return json.dumps({"error": f"Compliance check with ID '{check_id}' not found."})
            
            report = {
                "check_id": check.check_id,
                "system_or_process": check.system_or_process,
                "regulations_or_standards": json.loads(check.regulations_or_standards),
                "compliance_status": json.loads(check.compliance_status),
                "overall_status": check.overall_status,
                "checked_at": check.checked_at
            }
        except Exception as e:
            logger.error(f"Error getting compliance check details: {e}")
            report = {"error": f"Failed to get compliance check details: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListComplianceChecksTool(BaseTool):
    """Lists all recorded compliance checks."""
    def __init__(self, tool_name="list_compliance_checks"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all recorded compliance checks, showing their ID, system/process, overall status, and check date."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            checks = db.query(ComplianceCheck).order_by(ComplianceCheck.checked_at.desc()).all()
            if not checks:
                return json.dumps({"message": "No compliance checks found."})
            
            check_list = [{
                "check_id": c.check_id,
                "system_or_process": c.system_or_process,
                "overall_status": c.overall_status,
                "checked_at": c.checked_at
            } for c in checks]
            
            report = {"total_checks": len(check_list), "compliance_checks": check_list}
        except Exception as e:
            logger.error(f"Error listing compliance checks: {e}")
            report = {"error": f"Failed to list compliance checks: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)