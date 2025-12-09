import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

FEEDBACK_FILE = "user_feedback.json"

class UserFeedbackCollectionTool(BaseTool):
    """
    A tool to collect, manage, and analyze user feedback from a JSON file.
    """
    def __init__(self, tool_name: str = "user_feedback_collection_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Collects, lists, and analyzes user feedback stored in a local JSON file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'submit', 'list', or 'analyze'."
                },
                "feedback_text": {"type": "string", "description": "The text of the feedback (for 'submit')."},
                "rating": {"type": "integer", "description": "A numerical rating (e.g., 1-5) (for 'submit')."},
                "user_id": {"type": "string", "description": "The ID of the user submitting feedback.", "default": "anonymous"},
                "filter_by_rating": {"type": "integer", "description": "Only show feedback with this rating (for 'list')."}
            },
            "required": ["action"]
        }

    def _load_feedback(self) -> List[Dict[str, Any]]:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def _save_feedback(self, feedback_data: List[Dict[str, Any]]):
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(feedback_data, f, indent=4)

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            actions = {
                "submit": self._submit_feedback,
                "list": self._list_feedback,
                "analyze": self._analyze_feedback,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in UserFeedbackCollectionTool: {e}")
            return {"error": str(e)}

    def _submit_feedback(self, feedback_text: str, rating: Optional[int] = None, user_id: str = "anonymous", **kwargs) -> Dict:
        if not feedback_text:
            raise ValueError("'feedback_text' is required for the 'submit' action.")
            
        feedback_data = self._load_feedback()
        
        feedback_entry = {
            "feedback_id": f"FB-{len(feedback_data) + 1}",
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "feedback_text": feedback_text,
            "rating": rating
        }
        feedback_data.append(feedback_entry)
        self._save_feedback(feedback_data)
        
        return {"message": "Feedback submitted successfully.", "feedback_entry": feedback_entry}

    def _list_feedback(self, filter_by_rating: Optional[int] = None, **kwargs) -> Dict:
        feedback_data = self._load_feedback()
        if not feedback_data:
            return {"message": "No feedback has been submitted yet."}
            
        if filter_by_rating is not None:
            feedback_data = [fb for fb in feedback_data if fb.get("rating") == filter_by_rating]
            if not feedback_data:
                return {"message": f"No feedback found with a rating of {filter_by_rating}."}

        return {"feedback_list": feedback_data}

    def _analyze_feedback(self, **kwargs) -> Dict:
        feedback_data = self._load_feedback()
        if not feedback_data:
            return {"message": "No feedback available to analyze."}

        total_entries = len(feedback_data)
        
        # Calculate average rating
        ratings = [fb["rating"] for fb in feedback_data if fb.get("rating") is not None]
        average_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Find common keywords (simple approach)
        all_text = " ".join([fb["feedback_text"].lower() for fb in feedback_data])
        words = [word for word in all_text.split() if len(word) > 4] # Basic filtering
        common_words = {word: words.count(word) for word in set(words)}
        # Get top 5 common words
        top_5_words = sorted(common_words.items(), key=lambda item: item[1], reverse=True)[:5]

        return {
            "analysis_summary": {
                "total_feedback_entries": total_entries,
                "average_rating": round(average_rating, 2) if average_rating else "N/A",
                "top_keywords": top_5_words
            }
        }