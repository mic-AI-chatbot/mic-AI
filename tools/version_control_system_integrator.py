import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated GitHub repository data
mock_github_repo = {
    "pull_requests": {},
    "issues": {}
}

class GitHubIntegratorTool(BaseTool):
    """
    A tool to simulate interactions with a GitHub repository, like managing pull requests and issues.
    """
    def __init__(self, tool_name: str = "github_integrator_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates interactions with a GitHub repository (pull requests, issues)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'create_pr', 'list_prs', 'merge_pr', 'create_issue', 'list_issues'."
                },
                "pr_id": {"type": "integer", "description": "The ID of a pull request."},
                "issue_id": {"type": "integer", "description": "The ID of an issue."},
                "title": {"type": "string", "description": "Title for a new PR or issue."},
                "body": {"type": "string", "description": "Body content for a new PR or issue."},
                "source_branch": {"type": "string", "description": "The source branch for a new PR."},
                "target_branch": {"type": "string", "description": "The target branch for a new PR.", "default": "main"}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            actions = {
                "create_pr": self._create_pr,
                "list_prs": self._list_prs,
                "merge_pr": self._merge_pr,
                "create_issue": self._create_issue,
                "list_issues": self._list_issues,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in GitHubIntegratorTool: {e}")
            return {"error": str(e)}

    def _create_pr(self, title: str, body: str, source_branch: str, target_branch: str = "main", **kwargs) -> Dict:
        if not all([title, body, source_branch]):
            raise ValueError("'title', 'body', and 'source_branch' are required.")
        
        pr_id = len(mock_github_repo["pull_requests"]) + 1
        new_pr = {
            "id": pr_id,
            "title": title,
            "body": body,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        mock_github_repo["pull_requests"][pr_id] = new_pr
        logger.info(f"Simulated creation of PR #{pr_id}.")
        return {"message": "Pull request created successfully.", "pull_request": new_pr}

    def _list_prs(self, **kwargs) -> Dict:
        return {"pull_requests": list(mock_github_repo["pull_requests"].values())}

    def _merge_pr(self, pr_id: int, **kwargs) -> Dict:
        if not pr_id:
            raise ValueError("'pr_id' is required.")
        pr = mock_github_repo["pull_requests"].get(pr_id)
        if not pr:
            raise ValueError(f"Pull request with ID {pr_id} not found.")
        if pr["status"] != "open":
            raise ValueError(f"Pull request #{pr_id} is not open and cannot be merged.")
            
        pr["status"] = "merged"
        pr["merged_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Simulated merge of PR #{pr_id}.")
        return {"message": f"Pull request #{pr_id} merged successfully.", "pull_request": pr}

    def _create_issue(self, title: str, body: str, **kwargs) -> Dict:
        if not all([title, body]):
            raise ValueError("'title' and 'body' are required.")
            
        issue_id = len(mock_github_repo["issues"]) + 1
        new_issue = {
            "id": issue_id,
            "title": title,
            "body": body,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        mock_github_repo["issues"][issue_id] = new_issue
        logger.info(f"Simulated creation of Issue #{issue_id}.")
        return {"message": "Issue created successfully.", "issue": new_issue}

    def _list_issues(self, **kwargs) -> Dict:
        return {"issues": list(mock_github_repo["issues"].values())}