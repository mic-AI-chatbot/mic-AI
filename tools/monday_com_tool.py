import logging
import json
import re
import random
from datetime import datetime
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated Monday.com data
SIMULATED_MONDAY_BOARDS = {
    "Project X": {
        "description": "Main board for Project X development.",
        "items": {
            "Task 1: Implement Feature A": {"status": "Working on it", "assigned_to": "Alice", "due_date": "2023-12-01"},
            "Task 2: Review Design": {"status": "Stuck", "assigned_to": "Bob", "due_date": "2023-11-20"},
            "Task 3: Write Documentation": {"status": "Done", "assigned_to": "Charlie", "due_date": "2023-11-15"}
        }
    },
    "Marketing Campaign": {
        "description": "Tracking marketing activities.",
        "items": {
            "Ad Creative Development": {"status": "Working on it", "assigned_to": "David", "due_date": "2023-11-25"},
            "Launch Social Media": {"status": "Done", "assigned_to": "Eve", "due_date": "2023-11-10"}
        }
    }
}

class MondayComSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Monday.com's AI features,
    generating structured JSON responses for tasks like summarizing boards,
    creating items, and updating statuses.
    """

    def __init__(self, tool_name: str = "MondayComSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Monday.com AI actions: summarizing boards, creating tasks, updating statuses."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt describing the action to perform on Monday.com."
                }
            },
            "required": ["prompt"]
        }

    def _find_board_and_item(self, prompt: str) -> Dict[str, str]:
        """Helper to extract board and item names from prompt."""
        board_match = re.search(r'on board\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt, re.IGNORECASE)
        item_match = re.search(r'task\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt, re.IGNORECASE)
        
        board_name = board_match.group(2) if board_match else None
        item_name = item_match.group(2) if item_match else None
        
        # Try to infer board if not explicitly mentioned but item is unique
        if not board_name and item_name:
            for b_name, b_data in SIMULATED_MONDAY_BOARDS.items():
                if item_name in b_data["items"]:
                    board_name = b_name
                    break

        return {"board_name": board_name, "item_name": item_name}

    def _simulate_summarize_board(self, board_name: str) -> Dict:
        board_data = SIMULATED_MONDAY_BOARDS.get(board_name)
        if not board_data:
            return {"status": "error", "message": f"Board '{board_name}' not found."}
        
        total_items = len(board_data["items"])
        done_items = sum(1 for item in board_data["items"].values() if item["status"] == "Done")
        working_items = sum(1 for item in board_data["items"].values() if item["status"] == "Working on it")
        
        summary = f"Board '{board_name}' has {total_items} items. {done_items} are Done, {working_items} are Working on it. "
        summary += f"Description: {board_data['description']}"
        
        return {
            "action": "summarize_board",
            "board_name": board_name,
            "summary": summary,
            "details": {"total_items": total_items, "done_items": done_items, "working_on_it_items": working_items}
        }

    def _simulate_create_task(self, board_name: str, task_name: str, assigned_to: str = "Unassigned", due_date: str = "") -> Dict:
        if board_name not in SIMULATED_MONDAY_BOARDS:
            return {"status": "error", "message": f"Board '{board_name}' not found."}
        if task_name in SIMULATED_MONDAY_BOARDS[board_name]["items"]:
            return {"status": "error", "message": f"Task '{task_name}' already exists on board '{board_name}'."}
        
        new_item = {"status": "To Do", "assigned_to": assigned_to, "due_date": due_date, "created_at": datetime.now().isoformat()}
        SIMULATED_MONDAY_BOARDS[board_name]["items"][task_name] = new_item
        
        return {
            "action": "create_task",
            "board_name": board_name,
            "task_name": task_name,
            "status": "created",
            "item_details": new_item
        }

    def _simulate_update_status(self, board_name: str, item_name: str, new_status: str) -> Dict:
        if board_name not in SIMULATED_MONDAY_BOARDS:
            return {"status": "error", "message": f"Board '{board_name}' not found."}
        if item_name not in SIMULATED_MONDAY_BOARDS[board_name]["items"]:
            return {"status": "error", "message": f"Task '{item_name}' not found on board '{board_name}'."}
        
        old_status = SIMULATED_MONDAY_BOARDS[board_name]["items"][item_name]["status"]
        SIMULATED_MONDAY_BOARDS[board_name]["items"][item_name]["status"] = new_status
        
        return {
            "action": "update_task_status",
            "board_name": board_name,
            "task_name": item_name,
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": datetime.now().isoformat()
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate Monday.com simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Monday.com would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        board_item_info = self._find_board_and_item(prompt_lower)
        board_name = board_item_info["board_name"]
        item_name = board_item_info["item_name"]

        if "summarize board" in prompt_lower:
            if board_name:
                response_data = self._simulate_summarize_board(board_name)
            else:
                response_data = {"status": "error", "message": "Please specify a board to summarize."}
        elif "create task" in prompt_lower or "add item" in prompt_lower:
            if board_name and item_name:
                assigned_to_match = re.search(r'assigned to\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt_lower)
                assigned_to = assigned_to_match.group(2).title() if assigned_to_match else "Unassigned"
                due_date_match = re.search(r'due by\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt_lower)
                due_date = due_date_match.group(2) if due_date_match else ""
                response_data = self._simulate_create_task(board_name, item_name, assigned_to, due_date)
            else:
                response_data = {"status": "error", "message": "Please specify a board and task name to create."}
        elif "update status" in prompt_lower or "change status" in prompt_lower:
            status_match = re.search(r'to\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt_lower)
            new_status = status_match.group(2).title() if status_match else None
            if board_name and item_name and new_status:
                response_data = self._simulate_update_status(board_name, item_name, new_status)
            else:
                response_data = {"status": "error", "message": "Please specify a board, task name, and new status."}
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Monday.com AI for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Monday.com."
        return response_data

if __name__ == '__main__':
    print("Demonstrating MondayComSimulatorTool functionality...")
    
    monday_sim = MondayComSimulatorTool()
    
    try:
        # --- Scenario 1: Summarize a board ---
        print("\n--- Simulating: Summarize board 'Project X' ---")
        prompt1 = "summarize board 'Project X'"
        result1 = monday_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # --- Scenario 2: Create a new task ---
        print("\n--- Simulating: Create task 'Plan Sprint' on board 'Project X' assigned to 'Eve' due by '2023-11-28' ---")
        prompt2 = "create task 'Plan Sprint' on board 'Project X' assigned to 'Eve' due by '2023-11-28'"
        result2 = monday_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))
        
        # --- Scenario 3: Update task status ---
        print("\n--- Simulating: Update status of 'Task 1: Implement Feature A' on board 'Project X' to 'Done' ---")
        prompt3 = "update status of 'Task 1: Implement Feature A' on board 'Project X' to 'Done'"
        result3 = monday_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))

        # --- Scenario 4: Generic query ---
        print("\n--- Simulating: Generic query ---")
        prompt4 = "What is the weather today?"
        result4 = monday_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")