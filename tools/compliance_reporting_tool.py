import logging
import json
import os
import random
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from tools.base_tool import BaseTool

# Import compliance_db_manager from compliance_checker.py
try:
    from .compliance_checker import compliance_db_manager
    COMPLIANCE_DB_AVAILABLE = True
except ImportError:
    COMPLIANCE_DB_AVAILABLE = False
    logging.warning("compliance_db_manager from compliance_checker.py not found. Compliance reporting will be limited.")

# ReportLab for PDF generation
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    SimpleDocTemplate = Paragraph = Spacer = Table = TableStyle = getSampleStyleSheet = inch = colors = None
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab library not installed. PDF report generation will not be available. Please install it with 'pip install reportlab'.")

# Deferring transformers import
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
        if self._generator is None:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

compliance_report_model_instance = ComplianceReportModel()

class GeneratePDFComplianceReportTool(BaseTool):
    """Generates a PDF compliance report from compliance check results using an AI model."""
    def __init__(self, tool_name="generate_pdf_compliance_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a PDF compliance report from compliance check results using an AI model, with a given title and saves it to a specified file path. Requires ReportLab."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "The absolute path where the PDF report will be saved."},
                "title": {"type": "string", "description": "The title of the report."},
                "check_id": {"type": "string", "description": "The ID of the compliance check to generate a report for."}
            },
            "required": ["file_path", "title", "check_id"]
        }

    def execute(self, file_path: str, title: str, check_id: str, **kwargs: Any) -> str:
        if not REPORTLAB_AVAILABLE:
            return json.dumps({"error": "ReportLab library is not installed. PDF report generation is not available."})
        if not COMPLIANCE_DB_AVAILABLE:
            return json.dumps({"error": "Compliance database manager not available. Cannot retrieve check results."})
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered report generation."})
        
        check_results = compliance_db_manager.get_compliance_check(check_id)
        if not check_results:
            return json.dumps({"error": f"Compliance check with ID '{check_id}' not found."})

        prompt = f"Generate a detailed compliance report for the system/process '{check_results['system_or_process']}' based on the following compliance check results: {json.dumps(check_results['compliance_status'])}. The overall status is '{check_results['overall_status']}'. The report should include an executive summary, detailed findings by regulation, and actionable recommendations. Format the report as a professional document.\n\nCompliance Report Content:"
        
        generated_report_content = compliance_report_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 1000)

        doc = SimpleDocTemplate(file_path)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(title, styles['h1']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))
        
        # Add AI-generated content, replacing newlines with breaks for PDF
        for paragraph in generated_report_content.split('\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph, styles['Normal']))
                story.append(Spacer(1, 0.1 * inch))

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            doc.build(story)
            return json.dumps({"message": f"PDF compliance report '{title}' generated and saved to '{os.path.abspath(file_path)}'.", "file_path": os.path.abspath(file_path)})
        except Exception as e:
            logger.error(f"Error generating PDF compliance report: {e}")
            return json.dumps({"error": f"Error generating PDF compliance report: {e}"})

class GenerateHTMLComplianceReportTool(BaseTool):
    """Generates an HTML compliance report from compliance check results using an AI model."""
    def __init__(self, tool_name="generate_html_compliance_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates an HTML compliance report from compliance check results using an AI model, with a given title and saves it to a specified file path."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "The absolute path where the HTML report will be saved."},
                "title": {"type": "string", "description": "The title of the report."},
                "check_id": {"type": "string", "description": "The ID of the compliance check to generate a report for."}
            },
            "required": ["file_path", "title", "check_id"]
        }

    def execute(self, file_path: str, title: str, check_id: str, **kwargs: Any) -> str:
        if not COMPLIANCE_DB_AVAILABLE:
            return json.dumps({"error": "Compliance database manager not available. Cannot retrieve check results."})
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered report generation."})
        
        check_results = compliance_db_manager.get_compliance_check(check_id)
        if not check_results:
            return json.dumps({"error": f"Compliance check with ID '{check_id}' not found."})

        prompt = f"Generate a detailed compliance report for the system/process '{check_results['system_or_process']}' based on the following compliance check results: {json.dumps(check_results['compliance_status'])}. The overall status is '{check_results['overall_status']}'. The report should include an executive summary, detailed findings by regulation, and actionable recommendations. Format the report as HTML.\n\nCompliance Report Content (HTML):"
        
        generated_report_content = compliance_report_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 1000)

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; color: #333; margin: 20px; }}
        h1, h2, h3 {{ color: #0056b3; }}
        .compliant {{ color: green; font-weight: bold; }}
        .non-compliant {{ color: red; font-weight: bold; }}
        ul {{ list-style-type: disc; margin-left: 20px; }}
        li {{ margin-bottom: 5px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p><b>Report Date:</b> {datetime.now().strftime('%Y-%m-%d')}</p>
    {generated_report_content}
</body>
</html>
"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return json.dumps({"message": f"HTML compliance report '{title}' generated and saved to '{os.path.abspath(file_path)}'.", "file_path": os.path.abspath(file_path)})
        except Exception as e:
            logger.error(f"Error generating HTML compliance report: {e}")
            return json.dumps({"error": f"Error generating HTML compliance report: {e}"})