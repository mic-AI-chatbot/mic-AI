import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool
from textblob import TextBlob # For sentiment analysis

logger = logging.getLogger(__name__)

class RecruitmentAssistantSimulatorTool(BaseTool):
    """
    A tool that simulates recruitment assistance, including screening resumes,
    generating interview questions, and analyzing candidate feedback.
    """

    def __init__(self, tool_name: str = "RecruitmentAssistantSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.jobs_file = os.path.join(self.data_dir, "job_descriptions.json")
        self.candidates_file = os.path.join(self.data_dir, "candidate_records.json")
        
        # Job descriptions: {job_id: {title: ..., description: ..., required_skills: []}}
        self.job_descriptions: Dict[str, Dict[str, Any]] = self._load_data(self.jobs_file, default={})
        # Candidate records: {candidate_id: {name: ..., resume_summary: ..., feedback: []}}
        self.candidate_records: Dict[str, Dict[str, Any]] = self._load_data(self.candidates_file, default={})

    @property
    def description(self) -> str:
        return "Simulates recruitment assistance: screens resumes, generates interview questions, analyzes feedback."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_job", "screen_resume", "generate_interview_questions", "schedule_interview", "analyze_candidate_feedback"]},
                "job_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "required_skills": {"type": "array", "items": {"type": "string"}},
                "resume_text": {"type": "string"},
                "candidate_id": {"type": "string"},
                "candidate_name": {"type": "string"},
                "interview_type": {"type": "string", "enum": ["behavioral", "technical", "situational"]},
                "interviewer_name": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "HH:MM"},
                "feedback_data": {"type": "object", "description": "e.g., {'strengths': '...', 'weaknesses': '...'}"}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_jobs(self):
        with open(self.jobs_file, 'w') as f: json.dump(self.job_descriptions, f, indent=2)

    def _save_candidates(self):
        with open(self.candidates_file, 'w') as f: json.dump(self.candidate_records, f, indent=2)

    def define_job(self, job_id: str, title: str, description: str, required_skills: List[str]) -> Dict[str, Any]:
        """Defines a new job description."""
        if job_id in self.job_descriptions: raise ValueError(f"Job '{job_id}' already exists.")
        
        new_job = {
            "id": job_id, "title": title, "description": description,
            "required_skills": [s.lower() for s in required_skills],
            "defined_at": datetime.now().isoformat()
        }
        self.job_descriptions[job_id] = new_job
        self._save_jobs()
        return new_job

    def screen_resume(self, job_id: str, candidate_id: str, candidate_name: str, resume_text: str) -> Dict[str, Any]:
        """Simulates screening a resume for relevant skills and experience."""
        job = self.job_descriptions.get(job_id)
        if not job: raise ValueError(f"Job '{job_id}' not found. Define it first.")
        
        resume_lower = resume_text.lower()
        matched_skills = []
        for skill in job["required_skills"]:
            if skill in resume_lower:
                matched_skills.append(skill)
        
        match_score = round(len(matched_skills) / len(job["required_skills"]), 2) if job["required_skills"] else 0.0
        
        candidate_record = {
            "id": candidate_id, "name": candidate_name, "job_id": job_id,
            "resume_summary": resume_text[:100] + "...", # Store a snippet
            "match_score": match_score, "matched_skills": matched_skills,
            "screened_at": datetime.now().isoformat()
        }
        self.candidate_records[candidate_id] = candidate_record
        self._save_candidates()
        return candidate_record

    def generate_interview_questions(self, job_id: str, interview_type: str) -> List[str]:
        """Generates interview questions based on a job description."""
        job = self.job_descriptions.get(job_id)
        if not job: raise ValueError(f"Job '{job_id}' not found. Define it first.")
        
        questions = []
        if interview_type == "behavioral":
            questions.append("Tell me about a time you faced a challenge and how you overcame it.")
            questions.append("Describe a situation where you had to work with a difficult team member.")
        elif interview_type == "technical":
            for skill in job["required_skills"]:
                questions.append(f"How would you implement/solve a problem related to {skill}?")
            questions.append("Explain a complex technical concept in simple terms.")
        elif interview_type == "situational":
            questions.append("What would you do if a project deadline was suddenly moved up?")
            questions.append("How would you handle a conflict with a client?")
        
        return questions

    def schedule_interview(self, candidate_id: str, interviewer_name: str, date: str, time: str) -> Dict[str, Any]:
        """Simulates scheduling an interview."""
        if candidate_id not in self.candidate_records: raise ValueError(f"Candidate '{candidate_id}' not found.")
        
        return {"status": "success", "message": f"Simulated: Interview scheduled for '{candidate_id}' with '{interviewer_name}' on {date} at {time}."}

    def analyze_candidate_feedback(self, candidate_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes candidate feedback for sentiment and key themes."""
        if candidate_id not in self.candidate_records: raise ValueError(f"Candidate '{candidate_id}' not found.")
        
        strengths_text = feedback_data.get("strengths", "")
        weaknesses_text = feedback_data.get("weaknesses", "")
        
        overall_text = strengths_text + " " + weaknesses_text
        blob = TextBlob(overall_text)
        
        overall_sentiment = "positive" if blob.sentiment.polarity > 0.1 else "negative" if blob.sentiment.polarity < -0.1 else "neutral"
        
        key_themes = []
        if "communication" in overall_text.lower(): key_themes.append("communication")
        if "problem solving" in overall_text.lower(): key_themes.append("problem_solving")
        if "technical" in overall_text.lower(): key_themes.append("technical_skills")
        
        self.candidate_records[candidate_id]["feedback_analysis"] = {
            "overall_sentiment": overall_sentiment,
            "key_themes": key_themes,
            "analyzed_at": datetime.now().isoformat()
        }
        self._save_candidates()
        return {"status": "success", "candidate_id": candidate_id, "analysis": self.candidate_records[candidate_id]["feedback_analysis"]}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_job":
            job_id = kwargs.get('job_id')
            title = kwargs.get('title')
            description = kwargs.get('description')
            required_skills = kwargs.get('required_skills')
            if not all([job_id, title, description, required_skills]):
                raise ValueError("Missing 'job_id', 'title', 'description', or 'required_skills' for 'define_job' operation.")
            return self.define_job(job_id, title, description, required_skills)
        elif operation == "screen_resume":
            job_id = kwargs.get('job_id')
            candidate_id = kwargs.get('candidate_id')
            candidate_name = kwargs.get('candidate_name')
            resume_text = kwargs.get('resume_text')
            if not all([job_id, candidate_id, candidate_name, resume_text]):
                raise ValueError("Missing 'job_id', 'candidate_id', 'candidate_name', or 'resume_text' for 'screen_resume' operation.")
            return self.screen_resume(job_id, candidate_id, candidate_name, resume_text)
        elif operation == "generate_interview_questions":
            job_id = kwargs.get('job_id')
            interview_type = kwargs.get('interview_type')
            if not all([job_id, interview_type]):
                raise ValueError("Missing 'job_id' or 'interview_type' for 'generate_interview_questions' operation.")
            return self.generate_interview_questions(job_id, interview_type)
        elif operation == "schedule_interview":
            candidate_id = kwargs.get('candidate_id')
            interviewer_name = kwargs.get('interviewer_name')
            date = kwargs.get('date')
            time = kwargs.get('time')
            if not all([candidate_id, interviewer_name, date, time]):
                raise ValueError("Missing 'candidate_id', 'interviewer_name', 'date', or 'time' for 'schedule_interview' operation.")
            return self.schedule_interview(candidate_id, interviewer_name, date, time)
        elif operation == "analyze_candidate_feedback":
            candidate_id = kwargs.get('candidate_id')
            feedback_data = kwargs.get('feedback_data')
            if not all([candidate_id, feedback_data]):
                raise ValueError("Missing 'candidate_id' or 'feedback_data' for 'analyze_candidate_feedback' operation.")
            return self.analyze_candidate_feedback(candidate_id, feedback_data)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RecruitmentAssistantSimulatorTool functionality...")
    temp_dir = "temp_recruitment_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    rec_tool = RecruitmentAssistantSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a job
        print("\n--- Defining job 'software_engineer_lead' ---")
        rec_tool.execute(operation="define_job", job_id="SE_Lead", title="Software Engineer Lead",
                         description="Lead a team of engineers to develop scalable software solutions.",
                         required_skills=["Python", "AWS", "Leadership", "System Design"])
        print("Job defined.")

        # 2. Screen a resume
        print("\n--- Screening resume for 'Alice Smith' ---")
        resume_text = "Experienced Python developer with strong AWS and leadership skills. Proven track record in system design."
        screen_result = rec_tool.execute(operation="screen_resume", job_id="SE_Lead", candidate_id="cand_alice", candidate_name="Alice Smith", resume_text=resume_text)
        print(json.dumps(screen_result, indent=2))

        # 3. Generate interview questions
        print("\n--- Generating technical interview questions for 'SE_Lead' ---")
        questions = rec_tool.execute(operation="generate_interview_questions", job_id="SE_Lead", interview_type="technical")
        print(json.dumps(questions, indent=2))

        # 4. Schedule an interview
        print("\n--- Scheduling interview for 'Alice Smith' ---")
        schedule_result = rec_tool.execute(operation="schedule_interview", candidate_id="cand_alice", interviewer_name="Bob Johnson", date="2025-12-01", time="10:00")
        print(json.dumps(schedule_result, indent=2))

        # 5. Analyze candidate feedback
        print("\n--- Analyzing feedback for 'Alice Smith' ---")
        feedback_data = {"strengths": "Excellent technical skills and leadership potential.", "weaknesses": "Could improve on client communication."}
        feedback_analysis = rec_tool.execute(operation="analyze_candidate_feedback", candidate_id="cand_alice", feedback_data=feedback_data)
        print(json.dumps(feedback_analysis, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")