import logging
import random
from typing import Dict, Any, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class StructuredDataToTextReportWriterTool(BaseTool):
    """
    A tool for simulating structured data to text report writing.
    """
    def __init__(self, tool_name: str = "structured_data_to_text_report_writer_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates converting numerical data into narrative reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "The structured data to convert into a narrative report (e.g., {'sales': 1000, 'growth': 0.15})."
                },
                "report_type": {"type": "string", "description": "The type of report to generate (e.g., 'sales_summary', 'financial_overview').", "default": "sales_summary"}
            },
            "required": ["data"]
        }

    def execute(self, data: Dict[str, Any], report_type: str = "sales_summary", **kwargs: Any) -> str:
        if not data:
            raise ValueError("Input 'data' cannot be empty.")

        report_lines = [f"--- {report_type.replace('_', ' ').title()} Report ---"]

        if report_type == "sales_summary":
            sales = data.get("sales")
            growth = data.get("growth")
            region = data.get("region", "global")

            if sales is not None:
                report_lines.append(f"Total sales for the period: ${sales:,.2f}.")
            if growth is not None:
                report_lines.append(f"This represents a growth of {growth:.2%} compared to the previous period.")
            if region:
                report_lines.append(f"Analysis focused on the {region} region.")
            
            if sales is None and growth is None:
                report_lines.append("No specific sales or growth data provided for summary.")

        elif report_type == "financial_overview":
            revenue = data.get("revenue")
            expenses = data.get("expenses")
            profit = data.get("profit")
            period = data.get("period", "current quarter")

            report_lines.append(f"Financial Overview for the {period}:")
            if revenue is not None:
                report_lines.append(f"  Total Revenue: ${revenue:,.2f}")
            if expenses is not None:
                report_lines.append(f"  Total Expenses: ${expenses:,.2f}")
            if profit is not None:
                report_lines.append(f"  Net Profit: ${profit:,.2f}")
            
            if revenue is None and expenses is None and profit is None:
                report_lines.append("No specific financial data provided for overview.")

        else:
            report_lines.append(f"Report type '{report_type}' not specifically handled. Raw data: {json.dumps(data)}")

        report_lines.append("--- End of Report ---")
        return "\n".join(report_lines)

if __name__ == '__main__':
    print("Demonstrating StructuredDataToTextReportWriterTool functionality...")
    
    writer_tool = StructuredDataToTextReportWriterTool()
    
    try:
        # 1. Generate a sales summary report
        print("\n--- Generating Sales Summary Report ---")
        sales_data = {"sales": 123456.78, "growth": 0.12, "region": "North America"}
        sales_report = writer_tool.execute(data=sales_data, report_type="sales_summary")
        print(sales_report)

        # 2. Generate a financial overview report
        print("\n--- Generating Financial Overview Report ---")
        financial_data = {"revenue": 500000, "expenses": 300000, "profit": 200000, "period": "Q3 2025"}
        financial_report = writer_tool.execute(data=financial_data, report_type="financial_overview")
        print(financial_report)

        # 3. Generate a report for an unhandled type
        print("\n--- Generating Report for Unhandled Type ---")
        unhandled_data = {"metric_a": 10, "metric_b": 20}
        unhandled_report = writer_tool.execute(data=unhandled_data, report_type="unhandled_type")
        print(unhandled_report)

    except Exception as e:
        print(f"\nAn error occurred: {e}")