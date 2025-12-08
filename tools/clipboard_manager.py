import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import ClipboardHistoryEntry
from sqlalchemy.exc import IntegrityError

# Deferring pyperclip import
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    pyperclip = None
    PYPERCLIP_AVAILABLE = False
    logging.warning("pyperclip library not found. Clipboard tools will not be fully functional. Please install it with 'pip install pyperclip'.")

logger = logging.getLogger(__name__)

class GetClipboardContentTool(BaseTool):
    """Retrieves the current content of the clipboard."""
    def __init__(self, tool_name="get_clipboard_content"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current text content from the system clipboard."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        if not PYPERCLIP_AVAILABLE:
            return json.dumps({"error": "The 'pyperclip' library is not installed. Please install it with 'pip install pyperclip'."})
        try:
            content = pyperclip.paste()
            return json.dumps({"content": content}, indent=2)
        except Exception as e:
            logger.error(f"Error getting clipboard content: {e}")
            return json.dumps({"error": f"Could not retrieve clipboard content: {e}"})

class SetClipboardContentTool(BaseTool):
    """Sets the clipboard content and records it in persistent history."""
    def __init__(self, tool_name="set_clipboard_content"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Sets the system clipboard to the given text content and records the entry in persistent history."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"content": {"type": "string", "description": "The text content to place on the clipboard."}},
            "required": ["content"]
        }

    def execute(self, content: str, **kwargs: Any) -> str:
        if not PYPERCLIP_AVAILABLE:
            return json.dumps({"error": "The 'pyperclip' library is not installed. Please install it with 'pip install pyperclip'."})
        
        db = next(get_db())
        try:
            pyperclip.copy(content)
            timestamp = datetime.now().isoformat() + "Z"
            new_entry = ClipboardHistoryEntry(
                content=content,
                content_type="text",
                timestamp=timestamp
            )
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            return json.dumps({"message": "Content copied to clipboard and recorded in history.", "content": content}, indent=2)
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting clipboard content: {e}")
            return json.dumps({"error": f"Could not set clipboard content: {e}"})
        finally:
            db.close()

class ClearClipboardTool(BaseTool):
    """Clears the clipboard's text content."""
    def __init__(self, tool_name="clear_clipboard"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Clears the clipboard's text content. Note: This does not clear the persistent clipboard history."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        if not PYPERCLIP_AVAILABLE:
            return json.dumps({"error": "The 'pyperclip' library is not installed. Please install it with 'pip install pyperclip'."})
        try:
            pyperclip.copy("")
            return json.dumps({"message": "Clipboard cleared."})
        except Exception as e:
            logger.error(f"Error clearing clipboard: {e}")
            return json.dumps({"error": f"Could not clear clipboard: {e}"})

class GetClipboardHistoryTool(BaseTool):
    """Retrieves the recent history of clipboard content from the persistent database."""
    def __init__(self, tool_name="get_clipboard_history"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the recent history of content that was set on the clipboard from the persistent database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_entries": {"type": "integer", "description": "The maximum number of recent entries to retrieve. Defaults to 10.", "default": 10}
            },
            "required": []
        }

    def execute(self, max_entries: int = 10, **kwargs: Any) -> str:
        if max_entries <= 0:
            return json.dumps({"error": "max_entries must be a positive integer."})
        
        db = next(get_db())
        try:
            history = db.query(ClipboardHistoryEntry).order_by(ClipboardHistoryEntry.timestamp.desc()).limit(max_entries).all()
            history_list = [{
                "id": h.id,
                "content": h.content,
                "content_type": h.content_type,
                "timestamp": h.timestamp
            } for h in history]
            report = {"total_entries": len(history_list), "history": history_list}
        except Exception as e:
            logger.error(f"Error getting clipboard history: {e}")
            report = {"error": f"Failed to get clipboard history: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
