
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SpecializedDomainSimulatorTool(BaseTool):
    """
    A tool that simulates a specialized domain tool, performing domain-specific
    analysis on provided data and generating reports.
    """

    def __init__(self, tool_name: str = "SpecializedDomainSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.domain_data_file = os.path.join(self.data_dir, "domain_data.json")
        self.reports_file = os.path.join(self.data_dir, "domain_analysis_reports.json")
        
        # Domain data: {data_id: {domain_type: ..., content: {}}}
        self.domain_data: Dict[str, Dict[str, Any]] = self._load_data(self.domain_data_file, default={})
        # Analysis reports: {report_id: {data_id: ..., analysis_type: ..., results: {}}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates a specialized domain tool: adds domain-specific data and performs domain-specific analysis."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_domain_data", "perform_domain_analysis", "get_analysis_report"]},
                "data_id": {"type": "string"},
                "domain_type": {"type": "string", "enum": ["financial_report", "medical_record", "project_status"]},
                "data_content": {"type": "object", "description": "Domain-specific data content."},
                "analysis_type": {"type": "string", "enum": ["profitability", "risk_assessment", "progress_evaluation"]},
                "report_id": {"type": "string", "description": "ID of the analysis report to retrieve."}
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

    def _save_domain_data(self):
        with open(self.domain_data_file, 'w') as f: json.dump(self.domain_data, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def add_domain_data(self, data_id: str, domain_type: str, data_content: Dict[str, Any]) -> Dict[str, Any]:
        """Adds domain-specific data to the system."""
        if data_id in self.domain_data: raise ValueError(f"Data '{data_id}' already exists.")
        
        new_data = {
            "id": data_id, "domain_type": domain_type, "content": data_content,
            "added_at": datetime.now().isoformat()
        }
        self.domain_data[data_id] = new_data
        self._save_domain_data()
        return new_data

    def perform_domain_analysis(self, data_id: str, analysis_type: str) -> Dict[str, Any]:
        """Performs domain-specific analysis on provided data."""
        data = self.domain_data.get(data_id)
        if not data: raise ValueError(f"Domain data '{data_id}' not found. Add it first.")
        
        report_id = f"analysis_report_{data_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        analysis_results = {}
        
        if data["domain_type"] == "financial_report":
            if analysis_type == "profitability":
                revenue = data["content"].get("revenue", 0)
                expenses = data["content"].get("expenses", 0)
                net_profit = revenue - expenses
                profit_margin = round((net_profit / revenue) * 100, 2) if revenue > 0 else 0
                analysis_results = {"net_profit": net_profit, "profit_margin_percent": profit_margin}
            elif analysis_type == "risk_assessment":
                debt = data["content"].get("debt", 0)
                equity = data["content"].get("equity", 0)
                debt_to_equity_ratio = round(debt / equity, 2) if equity > 0 else float('inf')
                risk_level = "low"
                if debt_to_equity_ratio > 2.0: risk_level = "high"
                elif debt_to_equity_ratio > 1.0: risk_level = "medium"
                analysis_results = {"debt_to_equity_ratio": debt_to_equity_ratio, "financial_risk_level": risk_level}
        elif data["domain_type"] == "medical_record":
            if analysis_type == "progress_evaluation":
                condition = data["content"].get("condition", "unknown")
                treatment_adherence = data["content"].get("treatment_adherence", 0.0)
                outcome = "stable"
                if treatment_adherence > 0.8: outcome = "improving"
                elif treatment_adherence < 0.5: outcome = "worsening"
                analysis_results = {"condition": condition, "treatment_adherence": treatment_adherence, "patient_outcome": outcome}
        
        report = {
            "id": report_id, "data_id": data_id, "domain_type": data["domain_type"],
            "analysis_type": analysis_type, "results": analysis_results,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def get_analysis_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated domain analysis report."""
        report = self.analysis_reports.get(report_id)
        if not report: raise ValueError(f"Analysis report '{report_id}' not found.")
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_domain_data":
            data_id = kwargs.get('data_id')
            domain_type = kwargs.get('domain_type')
            data_content = kwargs.get('data_content')
            if not all([data_id, domain_type, data_content]):
                raise ValueError("Missing 'data_id', 'domain_type', or 'data_content' for 'add_domain_data' operation.")
            return self.add_domain_data(data_id, domain_type, data_content)
        elif operation == "perform_domain_analysis":
            data_id = kwargs.get('data_id')
            analysis_type = kwargs.get('analysis_type')
            if not all([data_id, analysis_type]):
                raise ValueError("Missing 'data_id' or 'analysis_type' for 'perform_domain_analysis' operation.")
            return self.perform_domain_analysis(data_id, analysis_type)
        elif operation == "get_analysis_report":
            report_id = kwargs.get('report_id')
            if not report_id:
                raise ValueError("Missing 'report_id' for 'get_analysis_report' operation.")
            return self.get_analysis_report(report_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SpecializedDomainSimulatorTool functionality...")
    temp_dir = "temp_domain_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    domain_tool = SpecializedDomainSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add financial report data
        print("\n--- Adding financial report data 'Q1_2025_Finance' ---")
        financial_content = {"revenue": 150000, "expenses": 70000, "debt": 200000, "equity": 100000}
        domain_tool.execute(operation="add_domain_data", data_id="Q1_2025_Finance", domain_type="financial_report", data_content=financial_content)
        print("Financial data added.")

        # 2. Perform profitability analysis
        print("\n--- Performing profitability analysis on 'Q1_2025_Finance' ---")
        profit_report = domain_tool.execute(operation="perform_domain_analysis", data_id="Q1_2025_Finance", analysis_type="profitability")
        print(json.dumps(profit_report, indent=2))

        # 3. Perform risk assessment
        print("\n--- Performing risk assessment on 'Q1_2025_Finance' ---")
        risk_report = domain_tool.execute(operation="perform_domain_analysis", data_id="Q1_2025_Finance", analysis_type="risk_assessment")
        print(json.dumps(risk_report, indent=2))

        # 4. Add medical record data
        print("\n--- Adding medical record data 'patient_A_diabetes' ---")
        medical_content = {"condition": "diabetes", "treatment_adherence": 0.9, "blood_sugar_level": 120}
        domain_tool.execute(operation="add_domain_data", data_id="patient_A_diabetes", domain_type="medical_record", data_content=medical_content)
        print("Medical data added.")

        # 5. Perform progress evaluation
        print("\n--- Performing progress evaluation on 'patient_A_diabetes' ---")
        medical_report = domain_tool.execute(operation="perform_domain_analysis", data_id="patient_A_diabetes", analysis_type="progress_evaluation")
        print(json.dumps(medical_report, indent=2))

        # 6. Get analysis report
        print(f"\n--- Getting analysis report for '{profit_report['id']}' ---")
        retrieved_report = domain_tool.execute(operation="get_analysis_report", data_id="any", report_id=profit_report["id"]) # data_id is not used for get_analysis_report
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
