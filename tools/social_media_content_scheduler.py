import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SocialMediaSchedulerSimulatorTool(BaseTool):
    """
    A tool that simulates social media content scheduling, allowing for
    scheduling posts, publishing them, and tracking their status.
    """

    def __init__(self, tool_name: str = "SocialMediaSchedulerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.scheduled_posts_file = os.path.join(self.data_dir, "scheduled_posts.json")
        self.published_posts_file = os.path.join(self.data_dir, "published_posts.json")
        
        # Scheduled posts: {post_id: {platform: ..., content: ..., schedule_time: ..., status: ...}}
        self.scheduled_posts: Dict[str, Dict[str, Any]] = self._load_data(self.scheduled_posts_file, default={})
        # Published posts: {post_id: {platform: ..., content: ..., published_at: ...}}
        self.published_posts: Dict[str, Dict[str, Any]] = self._load_data(self.published_posts_file, default={})

    @property
    def description(self) -> str:
        return "Simulates social media content scheduling: schedule, publish, and track posts."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["schedule_post", "publish_post", "get_post_status", "list_scheduled_posts"]},
                "post_id": {"type": "string"},
                "platform": {"type": "string", "enum": ["Facebook", "Twitter", "Instagram", "LinkedIn"]},
                "post_content": {"type": "string"},
                "schedule_time": {"type": "string", "description": "YYYY-MM-DD HH:MM (24-hour format)"}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_scheduled_posts(self):
        with open(self.scheduled_posts_file, 'w') as f: json.dump(self.scheduled_posts, f, indent=2)

    def _save_published_posts(self):
        with open(self.published_posts_file, 'w') as f: json.dump(self.published_posts, f, indent=2)

    def schedule_post(self, post_id: str, platform: str, post_content: str, schedule_time: str) -> Dict[str, Any]:
        """Schedules a social media post."""
        if post_id in self.scheduled_posts: raise ValueError(f"Post '{post_id}' already scheduled.")
        
        try: datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")
        except ValueError: raise ValueError("Invalid schedule_time format. Please use YYYY-MM-DD HH:MM.")

        new_post = {
            "id": post_id, "platform": platform, "content": post_content,
            "schedule_time": schedule_time, "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        self.scheduled_posts[post_id] = new_post
        self._save_scheduled_posts()
        return new_post

    def publish_post(self, post_id: str) -> Dict[str, Any]:
        """Simulates publishing a scheduled post."""
        post = self.scheduled_posts.get(post_id)
        if not post: raise ValueError(f"Post '{post_id}' not found in scheduled posts.")
        
        post["status"] = "published"
        post["published_at"] = datetime.now().isoformat()
        self.published_posts[post_id] = post # Move to published
        del self.scheduled_posts[post_id] # Remove from scheduled
        self._save_scheduled_posts()
        self._save_published_posts()
        return {"status": "success", "message": f"Post '{post_id}' published."}

    def get_post_status(self, post_id: str) -> Dict[str, Any]:
        """Retrieves the status of a scheduled or published post."""
        if post_id in self.scheduled_posts: return self.scheduled_posts[post_id]
        if post_id in self.published_posts: return self.published_posts[post_id]
        raise ValueError(f"Post '{post_id}' not found.")

    def list_scheduled_posts(self) -> List[Dict[str, Any]]:
        """Lists all scheduled posts."""
        return list(self.scheduled_posts.values())

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "schedule_post":
            post_id = kwargs.get('post_id')
            platform = kwargs.get('platform')
            post_content = kwargs.get('post_content')
            schedule_time = kwargs.get('schedule_time')
            if not all([post_id, platform, post_content, schedule_time]):
                raise ValueError("Missing 'post_id', 'platform', 'post_content', or 'schedule_time' for 'schedule_post' operation.")
            return self.schedule_post(post_id, platform, post_content, schedule_time)
        elif operation == "publish_post":
            post_id = kwargs.get('post_id')
            if not post_id:
                raise ValueError("Missing 'post_id' for 'publish_post' operation.")
            return self.publish_post(post_id)
        elif operation == "get_post_status":
            post_id = kwargs.get('post_id')
            if not post_id:
                raise ValueError("Missing 'post_id' for 'get_post_status' operation.")
            return self.get_post_status(post_id)
        elif operation == "list_scheduled_posts":
            # No additional kwargs required for list_scheduled_posts
            return self.list_scheduled_posts()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SocialMediaSchedulerSimulatorTool functionality...")
    temp_dir = "temp_social_scheduler_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    scheduler_tool = SocialMediaSchedulerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Schedule a post
        print("\n--- Scheduling post 'POST-001' ---")
        scheduler_tool.execute(operation="schedule_post", post_id="POST-001", platform="Twitter", post_content="Exciting news coming soon!", schedule_time="2025-12-01 10:00")
        print("Post scheduled.")

        # 2. Get post status
        print("\n--- Getting status for 'POST-001' ---")
        status1 = scheduler_tool.execute(operation="get_post_status", post_id="POST-001")
        print(json.dumps(status1, indent=2))

        # 3. Publish the post
        print("\n--- Publishing post 'POST-001' ---")
        scheduler_tool.execute(operation="publish_post", post_id="POST-001")
        print("Post published.")

        # 4. Get post status again
        print("\n--- Getting status for 'POST-001' after publishing ---")
        status2 = scheduler_tool.execute(operation="get_post_status", post_id="POST-001")
        print(json.dumps(status2, indent=2))

        # 5. Schedule another post
        print("\n--- Scheduling post 'POST-002' ---")
        scheduler_tool.execute(operation="schedule_post", post_id="POST-002", platform="Facebook", post_content="Check out our latest blog post!", schedule_time="2025-12-05 14:30")
        print("Post scheduled.")

        # 6. List scheduled posts
        print("\n--- Listing scheduled posts ---")
        scheduled_list = scheduler_tool.execute(operation="list_scheduled_posts", post_id="any") # post_id is not used for list_scheduled_posts
        print(json.dumps(scheduled_list, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")