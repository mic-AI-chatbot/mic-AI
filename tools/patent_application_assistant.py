import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

# Define valid patent application statuses
PATENT_STATUSES = {
    "draft": "Drafting in progress",
    "prior_art_search": "Prior art search underway",
    "review": "Internal review",
    "filed": "Filed with patent office",
    "granted": "Patent granted",
    "rejected": "Application rejected"
}

class PatentApplicationAssistantTool(BaseTool):
    """
    A tool that simulates a patent application assistant, allowing for creating
    applications, drafting sections, and simulating prior art searches.
    """

    def __init__(self, tool_name: str = "PatentAssistant", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.applications_file = os.path.join(self.data_dir, "patent_applications.json")
        # Applications structure: {app_id: {title: ..., inventor: ..., status: ..., sections: {abstract: "..."}}}
        self.applications: Dict[str, Dict[str, Any]] = self._load_data(self.applications_file, default={})

    @property
    def description(self) -> str:
        return "Simulates patent application assistance: create, draft sections, and simulate prior art search."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_application", "draft_section", "simulate_prior_art_search", "update_status", "get_application_details"]},
                "application_id": {"type": "string"},
                "title": {"type": "string"},
                "inventor": {"type": "string"},
                "section_name": {"type": "string", "enum": ["abstract", "claims", "description", "background"]},
                "content": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords for prior art search."},
                "new_status": {"type": "string", "enum": list(PATENT_STATUSES.keys())}
            },
            "required": ["operation", "application_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.applications_file, 'w') as f: json.dump(self.applications, f, indent=2)

    def create_application(self, application_id: str, title: str, inventor: str) -> Dict[str, Any]:
        """Creates a new patent application record."""
        if application_id in self.applications: raise ValueError(f"Application '{application_id}' already exists.")
        
        new_app = {
            "id": application_id, "title": title, "inventor": inventor,
            "status": "draft", "sections": {}, "created_at": datetime.now().isoformat()
        }
        self.applications[application_id] = new_app
        self._save_data()
        return new_app

    def draft_section(self, application_id: str, section_name: str, content: str) -> Dict[str, Any]:
        """Drafts or updates a specific section of a patent application."""
        app = self.applications.get(application_id)
        if not app: raise ValueError(f"Application '{application_id}' not found.")
        
        app["sections"][section_name] = content
        app["last_updated_at"] = datetime.now().isoformat()
        self._save_data()
        return app

    def simulate_prior_art_search(self, application_id: str, keywords: List[str]) -> Dict[str, Any]:
        """Simulates a prior art search based on keywords."""
        app = self.applications.get(application_id)
        if not app: raise ValueError(f"Application '{application_id}' not found.")
        
        # Simulate finding some prior art references
        num_references = random.randint(0, 3)  # nosec B311
        prior_art_references = []
        for i in range(num_references):
            ref_title = f"Prior Art for '{random.choice(keywords)}' - Patent {random.randint(1000000, 9999999)}"  # nosec B311
            prior_art_references.append({"title": ref_title, "patent_id": f"US{random.randint(1000000, 9999999)}A1", "relevance_score": round(random.uniform(0.5, 0.9), 2)})  # nosec B311
        
        app["prior_art_search_results"] = prior_art_references
        app["status"] = "prior_art_search_completed"
        self._save_data()
        return {"status": "success", "message": f"Prior art search simulated for '{application_id}'.", "results": prior_art_references}

    def update_status(self, application_id: str, new_status: str) -> Dict[str, Any]:
        """Updates the status of a patent application."""
        app = self.applications.get(application_id)
        if not app: raise ValueError(f"Application '{application_id}' not found.")
        if new_status not in PATENT_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {list(PATENT_STATUSES.keys())}.")

        app["status"] = new_status
        app["last_updated_at"] = datetime.now().isoformat()
        self._save_data()
        return app

    def get_application_details(self, application_id: str) -> Dict[str, Any]:
        """Retrieves the full details of a patent application."""
        app = self.applications.get(application_id)
        if not app: raise ValueError(f"Application '{application_id}' not found.")
        return app

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "create_application": self.create_application,
            "draft_section": self.draft_section,
            "simulate_prior_art_search": self.simulate_prior_art_search,
            "update_status": self.update_status,
            "get_application_details": self.get_application_details
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating PatentApplicationAssistantTool functionality...")
    temp_dir = "temp_patent_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    patent_tool = PatentApplicationAssistantTool(data_dir=temp_dir)
    
    try:
        # 1. Create a new patent application
        print("\n--- Creating new patent application 'AI_Drug_Discovery' ---")
        patent_tool.execute(operation="create_application", application_id="AI_Drug_Discovery", title="AI-Powered Drug Discovery Platform", inventor="Dr. Jane Doe")
        print("Application created.")

        # 2. Draft the abstract section
        print("\n--- Drafting abstract for 'AI_Drug_Discovery' ---")
        abstract_content = "A novel platform utilizing artificial intelligence for accelerated drug discovery, focusing on molecular synthesis and protein folding prediction."
        patent_tool.execute(operation="draft_section", application_id="AI_Drug_Discovery", section_name="abstract", content=abstract_content)
        print("Abstract drafted.")

        # 3. Simulate a prior art search
        print("\n--- Simulating prior art search for 'AI_Drug_Discovery' ---")
        search_keywords = ["AI drug discovery", "molecular synthesis AI", "protein folding prediction"]
        prior_art_results = patent_tool.execute(operation="simulate_prior_art_search", application_id="AI_Drug_Discovery", keywords=search_keywords)
        print(json.dumps(prior_art_results, indent=2))

        # 4. Update application status
        print("\n--- Updating status to 'review' ---")
        patent_tool.execute(operation="update_status", application_id="AI_Drug_Discovery", new_status="review")
        print("Status updated.")

        # 5. Get application details
        print("\n--- Getting full details for 'AI_Drug_Discovery' ---")
        details = patent_tool.execute(operation="get_application_details", application_id="AI_Drug_Discovery")
        print(json.dumps(details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")