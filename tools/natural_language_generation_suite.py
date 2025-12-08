import logging
import random
from typing import Dict, Any, List, Union

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class NaturalLanguageGenerationTool(BaseTool):
    """
    A tool for generating natural language reports and summaries from
    structured data using template-based rules.
    """
    def __init__(self, tool_name: str = "NaturalLanguageGeneration", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates natural language reports and summaries from structured data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_report", "summarize_data"]},
                "data": {"type": "object", "description": "The structured data for NLG."},
                "output_format": {"type": "string", "enum": ["text", "bullet_points"], "default": "text"}
            },
            "required": ["operation", "data"]
        }

    def _generate_sales_report(self, sales_data: Dict[str, Any], output_format: str) -> str:
        """Generates a sales report from structured sales data."""
        region = sales_data.get("region", "unspecified")
        q1 = sales_data.get("sales_q1", 0)
        q2 = sales_data.get("sales_q2", 0)
        growth = sales_data.get("growth_q2", 0)
        
        if output_format == "text":
            report = f"Sales in the {region} region showed strong performance. "
            report += f"Q1 sales were ${q1:,.0f}, increasing to ${q2:,.0f} in Q2, "
            report += f"representing a {growth:.1f}% growth. "
            report += "This indicates a positive market trend and effective sales strategies."
            return report
        elif output_format == "bullet_points":
            report_lines = [
                f"- Region: {region}",
                f"- Q1 Sales: ${q1:,.0f}",
                f"- Q2 Sales: ${q2:,.0f}",
                f"- Q2 Growth: {growth:.1f}%",
                "- Strong performance and positive market trend."
            ]
            return "\n".join(report_lines)
        return "Unsupported output format."

    def _summarize_product_reviews(self, review_data: Dict[str, Any], output_format: str) -> str:
        """Summarizes product reviews."""
        product_name = review_data.get("product_name", "product")
        reviews = review_data.get("reviews", [])
        
        positive_keywords = ["great", "excellent", "love", "good", "happy"]
        negative_keywords = ["poor", "bad", "disappointed", "broken", "slow"]
        
        positive_count = 0
        negative_count = 0
        
        for review in reviews:
            if any(kw in review.lower() for kw in positive_keywords):
                positive_count += 1
            if any(kw in review.lower() for kw in negative_keywords):
                negative_count += 1
        
        total_reviews = len(reviews)
        
        if output_format == "text":
            summary = f"Summary for {product_name}: Out of {total_reviews} reviews, {positive_count} were positive and {negative_count} were negative. "
            if positive_count > negative_count:
                summary += "Overall sentiment is positive, with customers appreciating its features."
            elif negative_count > positive_count:
                summary += "Overall sentiment is negative, indicating areas for improvement."
            else:
                summary += "Sentiment is mixed."
            return summary
        elif output_format == "bullet_points":
            summary_lines = [
                f"- Product: {product_name}",
                f"- Total Reviews: {total_reviews}",
                f"- Positive Reviews: {positive_count}",
                f"- Negative Reviews: {negative_count}"
            ]
            if positive_count > negative_count:
                summary_lines.append("- Overall positive sentiment.")
            elif negative_count > positive_count:
                summary_lines.append("- Overall negative sentiment, needs improvement.")
            else:
                summary_lines.append("- Mixed sentiment.")
            return "\n".join(summary_lines)
        return "Unsupported output format."

    def execute(self, operation: str, data: Dict[str, Any], output_format: str = "text", **kwargs: Any) -> str:
        """
        Generates natural language output based on the specified operation and data.
        """
        if operation == "generate_report":
            return self._generate_sales_report(data, output_format)
        elif operation == "summarize_data":
            return self._summarize_product_reviews(data, output_format)
        else:
            raise ValueError(f"Unsupported operation: {operation}. Choose 'generate_report' or 'summarize_data'.")

if __name__ == '__main__':
    print("Demonstrating NaturalLanguageGenerationTool functionality...")
    
    nlg_tool = NaturalLanguageGenerationTool()
    
    try:
        # 1. Generate a sales report (text format)
        print("\n--- Generating Sales Report (Text) ---")
        sales_data = {"region": "North", "sales_q1": 120000, "sales_q2": 150000, "growth_q2": 25.0}
        report_text = nlg_tool.execute(operation="generate_report", data=sales_data, output_format="text")
        print(report_text)

        # 2. Generate a sales report (bullet points)
        print("\n--- Generating Sales Report (Bullet Points) ---")
        report_bullets = nlg_tool.execute(operation="generate_report", data=sales_data, output_format="bullet_points")
        print(report_bullets)

        # 3. Summarize product reviews (text format)
        print("\n--- Summarizing Product Reviews (Text) ---")
        review_data = {
            "product_name": "Smart Coffee Maker",
            "reviews": [
                "This is a great product, makes excellent coffee!",
                "Fast delivery, but the quality is poor.",
                "Love my new coffee maker, very happy with it.",
                "Disappointed, it broke after a week."
            ]
        }
        summary_text = nlg_tool.execute(operation="summarize_data", data=review_data, output_format="text")
        print(summary_text)

        # 4. Summarize product reviews (bullet points)
        print("\n--- Summarizing Product Reviews (Bullet Points) ---")
        summary_bullets = nlg_tool.execute(operation="summarize_data", data=review_data, output_format="bullet_points")
        print(summary_bullets)

    except Exception as e:
        print(f"\nAn error occurred: {e}")