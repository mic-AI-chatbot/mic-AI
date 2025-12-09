import logging
import os
from typing import Dict, Any, List
from tools.base_tool import BaseTool
from core.tool_agent import run_shell_command

logger = logging.getLogger(__name__)

class VersionControlAssistantTool(BaseTool):
    """
    A tool for assisting with Git version control operations by wrapping git commands.
    """
    def __init__(self, tool_name: str = "version_control_assistant_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "A wrapper for common Git commands like status, commit, push, pull, and branch."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The git action: 'status', 'add', 'commit', 'push', 'pull', 'branch', 'log', 'clone'."
                },
                "repo_path": {
                    "type": "string", 
                    "description": "The local path to the Git repository. Defaults to the current directory.",
                    "default": "."
                },
                "files": {"type": "array", "items": {"type": "string"}, "description": "List of files for the 'add' action."},
                "message": {"type": "string", "description": "Commit message for the 'commit' action."},
                "branch_name": {"type": "string", "description": "Branch name for 'branch' actions."},
                "branch_action": {"type": "string", "description": "Branch action: 'list', 'create', 'delete', 'checkout'.", "default": "list"},
                "repo_url": {"type": "string", "description": "Repository URL for the 'clone' action."},
                "clone_path": {"type": "string", "description": "Path to clone the repository into.", "default": "."}
            },
            "required": ["action"]
        }

    async def execute(self, action: str, repo_path: str = ".", **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            
            if action != "clone" and not os.path.isdir(os.path.join(repo_path, '.git')):
                raise FileNotFoundError(f"'{repo_path}' is not a valid Git repository.")

            actions = {
                "status": self._git_status,
                "add": self._git_add,
                "commit": self._git_commit,
                "push": self._git_push,
                "pull": self._git_pull,
                "branch": self._git_branch,
                "log": self._git_log,
                "clone": self._git_clone,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            result = await actions[action](repo_path=repo_path, **kwargs)
            return result

        except Exception as e:
            logger.error(f"An error occurred in VersionControlAssistantTool: {e}")
            return {"error": str(e)}

    async def _run_git_command(self, repo_path: str, command: str) -> Dict:
        """Helper to run git commands using the run_shell_command tool."""
        full_command = f"git {command}"
        logger.info(f"Executing git command in '{repo_path}': {full_command}")
        result = await run_shell_command(full_command, description=f"Executing git {command}", directory=repo_path)
        if result.get("exit_code") != 0:
            error_message = result.get('stderr', 'Git command failed.')
            raise Exception(error_message)
        return {"output": result.get("stdout", "")}

    async def _git_status(self, repo_path: str, **kwargs) -> Dict:
        return await self._run_git_command(repo_path, "status")

    async def _git_add(self, repo_path: str, files: List[str], **kwargs) -> Dict:
        if not files:
            raise ValueError("'files' list is required for the 'add' action.")
        file_list = " ".join([f'"{f}"' for f in files])
        return await self._run_git_command(repo_path, f"add {file_list}")

    async def _git_commit(self, repo_path: str, message: str, **kwargs) -> Dict:
        if not message:
            raise ValueError("'message' is required for the 'commit' action.")
        return await self._run_git_command(repo_path, f'commit -m "{message}"')

    async def _git_push(self, repo_path: str, **kwargs) -> Dict:
        return await self._run_git_command(repo_path, "push")

    async def _git_pull(self, repo_path: str, **kwargs) -> Dict:
        return await self._run_git_command(repo_path, "pull")

    async def _git_branch(self, repo_path: str, branch_action: str = "list", branch_name: str = None, **kwargs) -> Dict:
        if branch_action == "list":
            return await self._run_git_command(repo_path, "branch")
        elif branch_action == "create":
            if not branch_name: raise ValueError("'branch_name' is required.")
            return await self._run_git_command(repo_path, f"branch {branch_name}")
        elif branch_action == "delete":
            if not branch_name: raise ValueError("'branch_name' is required.")
            return await self._run_git_command(repo_path, f"branch -d {branch_name}")
        elif branch_action == "checkout":
            if not branch_name: raise ValueError("'branch_name' is required.")
            return await self._run_git_command(repo_path, f"checkout {branch_name}")
        else:
            raise ValueError(f"Invalid branch action '{branch_action}'.")

    async def _git_log(self, repo_path: str, **kwargs) -> Dict:
        return await self._run_git_command(repo_path, "log --oneline -n 10")

    async def _git_clone(self, repo_path: str, repo_url: str, clone_path: str = None, **kwargs) -> Dict:
        if not repo_url:
            raise ValueError("'repo_url' is required for the 'clone' action.")
        # Clone path is relative to the repo_path, which is '.' by default for clone
        path = clone_path or ""
        return await self._run_git_command(repo_path, f"clone {repo_url} {path}")
