import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool
from mic.llm_loader import get_llm

logger = logging.getLogger(__name__)

class FormulaWriterTool(BaseTool):
    """
    A tool for writing mathematical and scientific formulas using an LLM.
    """

    def __init__(self, tool_name: str = "formula_writer_tool"):
        super().__init__(tool_name)
        self.llm = get_llm() # Instantiate the LLM directly

    @property
    def description(self) -> str:
        return "Generates mathematical and scientific formulas based on a specified subject and concept using an LLM, including explanations and applications."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "enum": ["Math", "Physics", "Chemistry", "Biology", "Computer Science"], "description": "The subject area of the formula."},
                "concept": {"type": "string", "description": "The specific concept for which to write the formula (e.g., 'quadratic formula', 'Newton's second law')."}
            },
            "required": ["subject", "concept"]
        }

    def execute(self, subject: str, concept: str) -> str:
        """
        Generates mathematical and scientific formulas using an LLM.
        """
        logger.info(f"Writing formula for {subject} concept: {concept} using LLM.")

        llm_prompt = f"Generate the mathematical or scientific formula for the concept '{concept}' in the subject of '{subject}'. Provide the formula, ideally in a format like LaTeX or plain text if LaTeX is not suitable. Also, include a brief explanation of the formula, define its variables, and mention a common application. Format the output clearly with sections for Formula, Explanation, Variables, and Application."
        
        llm_response = self.llm.generate_response(llm_prompt)

        return f"Formula for '{concept}' ({subject}):\n```\n{llm_response}\n```"

def execute(subject: str, concept: str) -> str:
    """Legacy execute function for backward compatibility."""
    tool = FormulaWriterTool()
    return tool.execute(subject, concept)