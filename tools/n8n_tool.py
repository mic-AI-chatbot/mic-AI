import logging
import json
import re
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated n8n workflows
SIMULATED_N8N_WORKFLOWS = {
    "Send Welcome Email": {
        "trigger": "New User Signup",
        "steps": ["Receive new user data", "Generate personalized email", "Send email via SendGrid"],
        "status": "active"
    },
    "Categorize Customer Feedback": {
        "trigger": "New Feedback Submission",
        "steps": ["Receive feedback", "Analyze sentiment (LLM)", "Categorize topic (LLM)", "Save to database"],
        "status": "active"
    },
    "Daily Sales Report": {
        "trigger": "Daily at 9 AM",
        "steps": ["Fetch sales data from CRM", "Generate summary (LLM)", "Send report to Slack"],
        "status": "inactive"
    }
}

class N8nSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with n8n's AI nodes and workflow automation,
    generating structured JSON responses.
    """

    def __init__(self, tool_name: str = "N8nSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates n8n AI nodes for LLM integration, workflow automation, text generation, and data categorization."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt describing the n8n action to perform."
                }
            },
            "required": ["prompt"]
        }

    def _find_workflow_name(self, prompt: str) -> Optional[str]:
        """Helper to extract workflow name from prompt."""
        for wf_name in SIMULATED_N8N_WORKFLOWS.keys():
            if wf_name.lower() in prompt.lower():
                return wf_name
        return None

    def _simulate_trigger_workflow(self, workflow_name: str) -> Dict:
        workflow_data = SIMULATED_N8N_WORKFLOWS.get(workflow_name)
        if not workflow_data:
            return {"status": "error", "message": f"Workflow '{workflow_name}' not found."}
        if workflow_data["status"] == "inactive":
            return {"status": "error", "message": f"Workflow '{workflow_name}' is inactive and cannot be triggered."}
        
        return {
            "action": "trigger_workflow",
            "workflow_name": workflow_name,
            "status": "triggered",
            "simulated_output": f"Workflow '{workflow_name}' successfully triggered. (Simulated)"
        }

    def _simulate_create_workflow(self, prompt: str) -> Dict:
        name_match = re.search(r'create workflow\s+([\'\"]?)(.*?)\1(?:$|\s+to)', prompt, re.IGNORECASE)
        workflow_name = name_match.group(2).title() if name_match else f"New Workflow {random.randint(100, 999)}"  # nosec B311
        
        description_match = re.search(r'to\s+(.*?)(?:$|\s+with)', prompt, re.IGNORECASE)
        description = description_match.group(1) if description_match else "A new automated process."
        
        return {
            "action": "create_workflow",
            "workflow_name": workflow_name,
            "description": description,
            "trigger": "manual",
            "steps": ["Define trigger", "Add nodes", "Activate workflow"],
            "status": "draft"
        }

    def _simulate_summarize_text(self, text_to_summarize: str) -> Dict:
        # Simple simulation: take first few words
        words = text_to_summarize.split()
        summary = " ".join(words[:min(15, len(words))]) + "..." if len(words) > 15 else text_to_summarize
        
        return {
            "action": "summarize_text",
            "input_text_sample": text_to_summarize[:50] + "...",
            "simulated_summary": summary,
            "llm_node_used": True
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate n8n simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to n8n would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        
        if "trigger workflow" in prompt_lower:
            workflow_name = self._find_workflow_name(prompt)
            if workflow_name:
                response_data = self._simulate_trigger_workflow(workflow_name)
            else:
                response_data = {"status": "error", "message": "Please specify a workflow to trigger."}
        elif "create workflow" in prompt_lower:
            response_data = self._simulate_create_workflow(prompt)
        elif "summarize text" in prompt_lower:
            text_match = re.search(r'summarize text\s+([\'\"]?)(.*?)\1(?:$)', prompt_lower)
            text_to_summarize = text_match.group(2) if text_match else "No text provided for summarization."
            response_data = self._simulate_summarize_text(text_to_summarize)
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from n8n AI for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with n8n."
        return response_data

if __name__ == '__main__':
    print("Demonstrating N8nSimulatorTool functionality...")
    
    n8n_sim = N8nSimulatorTool()
    
    try:
        # --- Scenario 1: Trigger a workflow ---
        print("\n--- Simulating: Trigger workflow 'Send Welcome Email' ---")
        prompt1 = "trigger workflow 'Send Welcome Email'"
        result1 = n8n_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # --- Scenario 2: Create a new workflow ---
        print("\n--- Simulating: Create workflow 'Automate Social Posts' to post daily updates ---")
        prompt2 = "create workflow 'Automate Social Posts' to post daily updates"
        result2 = n8n_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # --- Scenario 3: Summarize text ---
        print("\n--- Simulating: Summarize text 'The quick brown fox jumps over the lazy dog. This is a test sentence.' ---")
        prompt3 = "summarize text 'The quick brown fox jumps over the lazy dog. This is a test sentence.'"
        result3 = n8n_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # --- Scenario 4: Generic query ---
        print("\n--- Simulating: Generic query ---")
        prompt4 = "What is the current time?"
        result4 = n8n_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")