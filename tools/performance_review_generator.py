import logging
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PerformanceReviewGeneratorTool(BaseTool):
    """
    A tool that generates structured performance reviews for employees
    based on provided performance data.
    """
    def __init__(self, tool_name: str = "PerformanceReviewGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates structured performance reviews for employees based on performance data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "employee_name": {"type": "string", "description": "The name of the employee."},
                "review_period": {"type": "string", "description": "The period for the performance review (e.g., 'Q3 2023', 'Annual 2023')."},
                "performance_data": {
                    "type": "object",
                    "description": "A dictionary containing employee performance metrics and feedback.",
                    "properties": {
                        "achievements": {"type": "array", "items": {"type": "string"}},
                        "areas_for_improvement": {"type": "array", "items": {"type": "string"}},
                        "goals_met_count": {"type": "integer"},
                        "total_goals": {"type": "integer"},
                        "peer_feedback_summary": {"type": "string"}
                    },
                    "required": ["achievements", "areas_for_improvement", "goals_met_count", "total_goals"]
                }
            },
            "required": ["employee_name", "review_period", "performance_data"]
        }

    def execute(self, employee_name: str, review_period: str, performance_data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Generates a structured performance review based on the provided data.
        """
        if not employee_name or not review_period or not performance_data:
            raise ValueError("Employee name, review period, and performance data are required.")

        achievements = performance_data.get("achievements", [])
        improvements = performance_data.get("areas_for_improvement", [])
        goals_met = performance_data.get("goals_met_count", 0)
        total_goals = performance_data.get("total_goals", 0)
        peer_feedback = performance_data.get("peer_feedback_summary", "No specific peer feedback provided.")

        # Determine overall rating
        if goals_met == total_goals and len(achievements) >= 2 and not improvements:
            overall_rating = "Exceeds Expectations"
            summary_statement = f"{employee_name} consistently exceeds expectations, demonstrating exceptional performance and achieving all set goals."
        elif goals_met >= (total_goals * 0.7) and len(achievements) >= 1:
            overall_rating = "Meets Expectations"
            summary_statement = f"{employee_name} consistently meets expectations, delivering solid performance and achieving most goals."
        else:
            overall_rating = "Needs Development"
            summary_statement = f"{employee_name} shows potential but needs development in certain areas to consistently meet expectations."

        # Construct the review
        review_sections = [
            f"--- Performance Review for {employee_name} ({review_period}) ---",
            f"\nOverall Rating: {overall_rating}",
            f"Summary: {summary_statement}",
            "\nKey Achievements:",
        ]
        if achievements:
            review_sections.extend([f"- {ach}" for ach in achievements])
        else:
            review_sections.append("- No specific achievements listed.")
        
        review_sections.append("\nAreas for Improvement:")
        if improvements:
            review_sections.extend([f"- {imp}" for imp in improvements])
        else:
            review_sections.append("- No specific areas for improvement listed.")
            
        review_sections.extend([
            f"\nGoals Status: Met {goals_met} out of {total_goals} goals.",
            f"Peer Feedback Summary: {peer_feedback}",
            "\n--- End of Review ---"
        ])

        return {
            "status": "success",
            "employee_name": employee_name,
            "review_period": review_period,
            "overall_rating": overall_rating,
            "generated_review": "\n".join(review_sections)
        }

if __name__ == '__main__':
    print("Demonstrating PerformanceReviewGeneratorTool functionality...")
    
    review_generator = PerformanceReviewGeneratorTool()
    
    try:
        # 1. Employee exceeding expectations
        print("\n--- Generating review for Alice (Exceeds Expectations) ---")
        alice_data = {
            "achievements": ["Led successful project X, increasing efficiency by 20%.", "Mentored junior team members."],
            "areas_for_improvement": [],
            "goals_met_count": 5,
            "total_goals": 5,
            "peer_feedback_summary": "Alice is a highly valued team member, always proactive and supportive."
        }
        review_alice = review_generator.execute(employee_name="Alice Smith", review_period="Annual 2023", performance_data=alice_data)
        print(review_alice["generated_review"])

        # 2. Employee meeting expectations
        print("\n--- Generating review for Bob (Meets Expectations) ---")
        bob_data = {
            "achievements": ["Completed all assigned tasks on time.", "Contributed to team discussions."],
            "areas_for_improvement": ["Improve presentation skills.", "Take on more leadership roles."],
            "goals_met_count": 3,
            "total_goals": 4,
            "peer_feedback_summary": "Bob is reliable and a good team player."
        }
        review_bob = review_generator.execute(employee_name="Bob Johnson", review_period="Q3 2023", performance_data=bob_data)
        print(review_bob["generated_review"])
        
        # 3. Employee needing development
        print("\n--- Generating review for Charlie (Needs Development) ---")
        charlie_data = {
            "achievements": ["Attended all team meetings."],
            "areas_for_improvement": ["Improve technical skills.", "Meet project deadlines consistently."],
            "goals_met_count": 1,
            "total_goals": 3,
            "peer_feedback_summary": "Charlie is new to the team and is still learning the ropes."
        }
        review_charlie = review_generator.execute(employee_name="Charlie Brown", review_period="Q4 2023", performance_data=charlie_data)
        print(review_charlie["generated_review"])

    except Exception as e:
        print(f"\nAn error occurred: {e}")