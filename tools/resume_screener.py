

import logging
import json
import re
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ResumeScreenerTool(BaseTool):
    """
    A tool that screens resumes against job descriptions using keyword matching
    to provide a match score and justification.
    """

    def __init__(self, tool_name: str = "ResumeScreener", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Screens resumes against job descriptions, providing a match score and justification based on skills and experience."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "resume_text": {"type": "string", "description": "The full text content of the candidate's resume."},
                "job_description": {"type": "string", "description": "The full text content of the job description."}
            },
            "required": ["resume_text", "job_description"]
        }

    def execute(self, resume_text: str, job_description: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Screens a resume against a job description using keyword matching.
        """
        if not resume_text or not job_description:
            raise ValueError("Resume text and job description cannot be empty.")

        # Normalize text for keyword extraction
        resume_lower = resume_text.lower()
        job_lower = job_description.lower()

        # Simple keyword extraction (can be improved with NLP libraries like spaCy)
        # For now, split by common delimiters and filter short words
        def extract_keywords(text: str) -> List[str]:
            words = re.findall(r'\b\w+\b', text)
            return [word for word in words if len(word) > 2]

        resume_keywords = set(extract_keywords(resume_lower))
        job_keywords = set(extract_keywords(job_lower))

        # Identify matching keywords
        matched_keywords = list(resume_keywords.intersection(job_keywords))
        
        # Calculate match score
        # Score based on percentage of job description keywords found in resume
        match_score = 0.0
        if len(job_keywords) > 0:
            match_score = len(matched_keywords) / len(job_keywords)
        
        # Generate justification
        justification = f"The resume was screened against the job description. "
        if match_score >= 0.7:
            justification += f"A strong match was found (Score: {match_score:.2f}). Key matching skills/experience include: {', '.join(matched_keywords[:5])}."
        elif match_score >= 0.4:
            justification += f"A moderate match was found (Score: {match_score:.2f}). Some key matching skills/experience include: {', '.join(matched_keywords[:5])}. Consider areas for further review."
        else:
            justification += f"A low match was found (Score: {match_score:.2f}). Few matching skills/experience were identified. "
            missing_keywords = list(job_keywords.difference(resume_keywords))
            if missing_keywords:
                justification += f"Missing key requirements include: {', '.join(missing_keywords[:5])}."

        return {
            "status": "success",
            "match_score": round(match_score, 2),
            "matched_keywords": matched_keywords,
            "justification": justification
        }

if __name__ == '__main__':
    print("Demonstrating ResumeScreenerTool functionality...")
    
    screener_tool = ResumeScreenerTool()
    
    # Sample resume and job description
    sample_resume_good = """
    John Doe
    Experience: 5 years as a Senior Software Engineer. Proficient in Python, Java, AWS, and Docker.
    Led multiple projects, strong in system design and agile methodologies.
    Education: M.Sc. Computer Science.
    """
    sample_resume_bad = """
    Jane Smith
    Experience: 2 years as a Junior Web Developer. Proficient in HTML, CSS, JavaScript.
    Worked on front-end development.
    Education: B.A. Graphic Design.
    """
    sample_job_description = """
    Job Title: Senior Software Engineer
    Requirements: 5+ years experience. Strong proficiency in Python, AWS, System Design.
    Experience with Docker and leading projects is a plus.
    """
    
    try:
        # 1. Screen a good resume
        print("\n--- Screening a good resume ---")
        result1 = screener_tool.execute(resume_text=sample_resume_good, job_description=sample_job_description)
        print(json.dumps(result1, indent=2))

        # 2. Screen a bad resume
        print("\n--- Screening a bad resume ---")
        result2 = screener_tool.execute(resume_text=sample_resume_bad, job_description=sample_job_description)
        print(json.dumps(result2, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
