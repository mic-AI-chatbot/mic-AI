import logging
import json
import re
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated meeting transcripts and data
SIMULATED_MEETINGS = {
    "Project Alpha Sync": {
        "content": "Meeting on 2023-11-15. Attendees: Alice, Bob, Charlie. Discussed project timeline, resource allocation, and next steps. Decision: Prioritize Feature X. Action Item: Bob to research cloud providers. Deadline: 2023-11-20. Alice will update the documentation.",
        "summary": "Project Alpha sync meeting covered timeline, resources, and next steps. Feature X was prioritized. Bob will research cloud providers by 2023-11-20. Alice will update documentation.",
        "action_items": [
            {"owner": "Bob", "task": "research cloud providers", "deadline": "2023-11-20"},
            {"owner": "Alice", "task": "update the documentation", "deadline": "N/A"}
        ],
        "key_decisions": ["Prioritize Feature X"]
    },
    "Q3 Sales Review": {
        "content": "Meeting on 2023-10-20. Attendees: David, Eve. Reviewed Q3 sales performance. Sales were up 15% YoY. Decision: Launch new marketing campaign in Q4. Action Item: Eve to draft campaign brief. Deadline: 2023-10-27.",
        "summary": "Q3 sales review showed 15% YoY growth. New marketing campaign to launch in Q4. Eve to draft campaign brief by 2023-10-27.",
        "action_items": [
            {"owner": "Eve", "task": "draft campaign brief", "deadline": "2023-10-27"}
        ],
        "key_decisions": ["Launch new marketing campaign in Q4"]
    }
}

class NyotaSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Nyota, providing meeting insights,
    summarization, and generating follow-up actions and content based on
    simulated meeting transcripts.
    """

    def __init__(self, tool_name: str = "NyotaSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Nyota: meeting insights, summarization, and creating follow-up actions and content."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for Nyota (e.g., 'summarize meeting \"Project Alpha Sync\"')."
                }
            },
            "required": ["prompt"]
        }

    def _find_meeting_id(self, prompt: str) -> Optional[str]:
        """Helper to extract meeting ID from prompt."""
        for meeting_id in SIMULATED_MEETINGS.keys():
            if meeting_id.lower() in prompt.lower():
                return meeting_id
        return None

    def _simulate_summarize_meeting(self, meeting_id: str) -> Dict:
        meeting_data = SIMULATED_MEETINGS.get(meeting_id)
        if not meeting_data:
            return {"status": "error", "message": f"Meeting '{meeting_id}' not found in simulated data."}
        
        return {
            "action": "summarize_meeting",
            "meeting_id": meeting_id,
            "summary": meeting_data["summary"]
        }

    def _simulate_extract_action_items(self, meeting_id: str) -> Dict:
        meeting_data = SIMULATED_MEETINGS.get(meeting_id)
        if not meeting_data:
            return {"status": "error", "message": f"Meeting '{meeting_id}' not found in simulated data."}
        
        return {
            "action": "extract_action_items",
            "meeting_id": meeting_id,
            "action_items": meeting_data["action_items"]
        }

    def _simulate_create_follow_up_email(self, meeting_id: str) -> Dict:
        meeting_data = SIMULATED_MEETINGS.get(meeting_id)
        if not meeting_data:
            return {"status": "error", "message": f"Meeting '{meeting_id}' not found in simulated data."}
        
        attendees_match = re.search(r'Attendees:\s*(.*?)\.', meeting_data["content"])
        attendees = attendees_match.group(1).split(', ') if attendees_match else ["unknown"]
        
        email_subject = f"Follow-up: {meeting_id}"
        email_body = f"Hi Team:\n\nHere's a summary of our recent meeting '{meeting_id}':\n\n"
        email_body += f"Summary: {meeting_data['summary']}\n\n"
        email_body += "Key Decisions:\n" + "\n".join([f"- {d}" for d in meeting_data["key_decisions"]]) + "\n\n"
        email_body += "Action Items:\n" + "\n".join([f"- {item['task']} (Owner: {item['owner']}, Deadline: {item['deadline']})" for item in meeting_data["action_items"]]) + "\n\n"
        email_body += "Best regards,\nNyota AI (Simulated)"
        
        return {
            "action": "create_follow_up_email",
            "meeting_id": meeting_id,
            "recipients": attendees,
            "subject": email_subject,
            "body": email_body
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate Nyota simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Nyota would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        meeting_id = self._find_meeting_id(prompt)

        if "summarize meeting" in prompt_lower:
            if meeting_id:
                response_data = self._simulate_summarize_meeting(meeting_id)
            else:
                response_data = {"status": "error", "message": "Please specify a meeting to summarize."}
        elif "extract action items" in prompt_lower or "get actions" in prompt_lower:
            if meeting_id:
                response_data = self._simulate_extract_action_items(meeting_id)
            else:
                response_data = {"status": "error", "message": "Please specify a meeting to extract action items from."}
        elif "create follow-up" in prompt_lower or "generate follow-up email" in prompt_lower:
            if meeting_id:
                response_data = self._simulate_create_follow_up_email(meeting_id)
            else:
                response_data = {"status": "error", "message": "Please specify a meeting to create a follow-up for."}
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Nyota AI for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Nyota."
        return response_data

if __name__ == '__main__':
    print("Demonstrating NyotaSimulatorTool functionality...")
    
    nyota_sim = NyotaSimulatorTool()
    
    try:
        # 1. Summarize a meeting
        print("\n--- Simulating: Summarize meeting 'Project Alpha Sync' ---")
        prompt1 = "summarize meeting 'Project Alpha Sync'"
        result1 = nyota_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Extract action items
        print("\n--- Simulating: Extract action items from 'Q3 Sales Review' ---")
        prompt2 = "extract action items from 'Q3 Sales Review'"
        result2 = nyota_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # 3. Create a follow-up email
        print("\n--- Simulating: Create follow-up email for 'Project Alpha Sync' ---")
        prompt3 = "create follow-up email for 'Project Alpha Sync'"
        result3 = nyota_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # 4. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt4 = "What is the weather like?"
        result4 = nyota_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")