import logging
import json
import re
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated email data
SIMULATED_EMAIL_THREADS = {
    "thread_001": {
        "subject": "Project Update - Week 45",
        "sender": "alice@example.com",
        "recipients": ["bob@example.com", "charlie@example.com"],
        "messages": [
            {"from": "alice@example.com", "body": "Hi team, here's the project update. We're on track for Feature X. Bob, please review the latest PR. Charlie, the documentation needs updating."},
            {"from": "bob@example.com", "body": "Thanks Alice, I'll get to the PR today. Looks good."},
            {"from": "charlie@example.com", "body": "Got it, Alice. I'll prioritize the documentation updates."}
        ]
    },
    "thread_002": {
        "subject": "Meeting Request - Q4 Planning",
        "sender": "manager@example.com",
        "recipients": ["alice@example.com", "bob@example.com"],
        "messages": [
            {"from": "manager@example.com", "body": "Hi team, let's schedule a meeting for Q4 planning. Please suggest your availability."},
            {"from": "alice@example.com", "body": "I'm free Tuesday afternoon."},
            {"from": "bob@example.com", "body": "Wednesday morning works for me."}
        ]
    }
}

class ShortwaveSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Shortwave, an AI-powered email client,
    generating structured JSON responses for tasks like email bundling,
    summarizing threads, and drafting replies.
    """

    def __init__(self, tool_name: str = "ShortwaveSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Shortwave: AI-powered features for bundling emails, summarizing long threads, and drafting replies."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for Shortwave (e.g., 'summarize thread \"Project Update\"')."
                }
            },
            "required": ["prompt"]
        }

    def _find_thread_by_subject(self, prompt: str) -> Optional[str]:
        """Helper to extract thread subject from prompt and find matching thread ID."""
        for thread_id, thread_data in SIMULATED_EMAIL_THREADS.items():
            if thread_data["subject"].lower() in prompt.lower():
                return thread_id
        return None

    def _simulate_bundle_emails(self, sender: str) -> Dict:
        bundled_threads = []
        for thread_id, thread_data in SIMULATED_EMAIL_THREADS.items():
            if thread_data["sender"].lower().startswith(sender.lower()):
                bundled_threads.append({"thread_id": thread_id, "subject": thread_data["subject"]})
        
        return {
            "action": "bundle_emails",
            "sender": sender,
            "bundled_threads": bundled_threads,
            "message": f"Simulated: Emails from '{sender}' bundled into {len(bundled_threads)} threads."
        }

    def _simulate_summarize_thread(self, thread_id: str) -> Dict:
        thread_data = SIMULATED_EMAIL_THREADS.get(thread_id)
        if not thread_data:
            return {"status": "error", "message": f"Email thread '{thread_id}' not found in simulated data."}
        
        # Simple summary: combine first sentence of each message
        summary = " ".join([msg["body"].split('.')[0] + "." for msg in thread_data["messages"]])
        
        return {
            "action": "summarize_thread",
            "thread_id": thread_id,
            "thread_subject": thread_data["subject"],
            "summary": summary
        }

    def _simulate_draft_reply(self, thread_id: str, recipient: str) -> Dict:
        thread_data = SIMULATED_EMAIL_THREADS.get(thread_id)
        if not thread_data:
            return {"status": "error", "message": f"Email thread '{thread_id}' not found in simulated data."}
        
        last_message_body = thread_data["messages"][-1]["body"]
        draft_body = f"Hi {recipient},\n\nRegarding your last message: '{last_message_body[:50]}...'\n\nThis is a simulated draft reply. Please fill in the details.\n\nBest,\n[Your Name]"
        
        return {
            "action": "draft_reply",
            "thread_id": thread_id,
            "recipient": recipient,
            "subject": f"Re: {thread_data['subject']}",
            "draft_body": draft_body
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate Shortwave simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Shortwave would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        thread_id = self._find_thread_by_subject(prompt)

        if "bundle emails" in prompt_lower:
            sender_match = re.search(r'from\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt_lower)
            sender = sender_match.group(2) if sender_match else "unknown"
            response_data = self._simulate_bundle_emails(sender)
        elif "summarize thread" in prompt_lower:
            if thread_id:
                response_data = self._simulate_summarize_thread(thread_id)
            else:
                response_data = {"status": "error", "message": "Please specify an email thread to summarize."}
        elif "draft reply" in prompt_lower:
            recipient_match = re.search(r'to\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt_lower)
            recipient = recipient_match.group(2) if recipient_match else "unknown"
            if thread_id:
                response_data = self._simulate_draft_reply(thread_id, recipient)
            else:
                response_data = {"status": "error", "message": "Please specify an email thread to reply to."}
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Shortwave for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Shortwave."
        return response_data

if __name__ == '__main__':
    print("Demonstrating ShortwaveSimulatorTool functionality...")
    
    shortwave_sim = ShortwaveSimulatorTool()
    
    try:
        # 1. Bundle emails from a sender
        print("\n--- Simulating: Bundle emails from 'Alice' ---")
        prompt1 = "bundle emails from 'alice@example.com'"
        result1 = shortwave_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Summarize an email thread
        print("\n--- Simulating: Summarize thread 'Project Update - Week 45' ---")
        prompt2 = "summarize thread 'Project Update - Week 45'"
        result2 = shortwave_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # 3. Draft a reply
        print("\n--- Simulating: Draft reply to 'manager@example.com' about 'Meeting Request - Q4 Planning' ---")
        prompt3 = "draft reply to 'manager@example.com' about 'Meeting Request - Q4 Planning'"
        result3 = shortwave_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # 4. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt4 = "What is the capital of France?"
        result4 = shortwave_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")