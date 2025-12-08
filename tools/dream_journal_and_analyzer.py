import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DreamJournalAndAnalyzerTool(BaseTool):
    """
    A tool for journaling dreams and analyzing them for recurring themes and patterns.
    """

    def __init__(self, tool_name: str = "dream_journal_and_analyzer"):
        super().__init__(tool_name)
        self.journal_file = "dream_journal.json"
        self.journal: Dict[str, Dict[str, Any]] = self._load_journal()
        self.common_themes = ["flying", "falling", "chasing", "teeth", "water", "school", "work", "loved ones", "strangers", "success", "failure", "anxiety", "joy"]

    @property
    def description(self) -> str:
        return "Journals dreams, analyzes them for themes and patterns, and provides summaries of entries."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The dream journal operation to perform.",
                    "enum": ["add_dream_entry", "analyze_dream_themes", "get_dream_summary", "list_dream_entries", "get_entry_details"]
                },
                "entry_id": {"type": "string"},
                "date": {"type": "string", "description": "The date of the dream (YYYY-MM-DD)."},
                "dream_text": {"type": "string", "description": "The detailed description of the dream."},
                "num_entries": {"type": "integer", "minimum": 1}
            },
            "required": ["operation"]
        }

    def _load_journal(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.journal_file):
            with open(self.journal_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted journal file '{self.journal_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_journal(self) -> None:
        with open(self.journal_file, 'w') as f:
            json.dump(self.journal, f, indent=4)

    def _extract_keywords_and_themes(self, dream_text: str) -> Dict[str, Any]:
        keywords = [word for word in dream_text.lower().split() if len(word) > 3 and word.isalpha()]
        identified_themes = [theme for theme in self.common_themes if theme in dream_text.lower()]
        return {"keywords": list(set(keywords)), "themes": list(set(identified_themes))}

    def _add_dream_entry(self, entry_id: str, date: str, dream_text: str) -> Dict[str, Any]:
        if not all([entry_id, date, dream_text]):
            raise ValueError("Entry ID, date, and dream text cannot be empty.")
        if entry_id in self.journal: raise ValueError(f"Dream entry '{entry_id}' already exists.")
        
        extracted = self._extract_keywords_and_themes(dream_text)

        new_entry = {
            "entry_id": entry_id, "date": date, "dream_text": dream_text,
            "keywords": extracted["keywords"], "themes": extracted["themes"],
            "recorded_at": datetime.now().isoformat()
        }
        self.journal[entry_id] = new_entry
        self._save_journal()
        return new_entry

    def _analyze_dream_themes(self) -> Dict[str, Any]:
        if not self.journal: return {"message": "No dream entries to analyze."}
        
        theme_counts: Dict[str, int] = {}
        for entry in self.journal.values():
            for theme in entry["themes"]: theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        if not theme_counts: return {"message": "No recurring themes found in your dream journal."}
        
        sorted_themes = sorted(theme_counts.items(), key=lambda item: item[1], reverse=True)
        
        analysis_report = {
            "report_id": f"THEME_REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(), "theme_counts": sorted_themes,
            "summary": "Top recurring themes identified."
        }
        return analysis_report

    def _get_dream_summary(self, num_entries: int = 5) -> List[Dict[str, Any]]:
        if not self.journal: return []
        
        sorted_entries = sorted(self.journal.values(), key=lambda x: (x["date"], x["recorded_at"]), reverse=True)
        recent_entries = sorted_entries[:num_entries]
        
        summarized_entries = []
        for entry in recent_entries:
            summarized_entries.append({
                "entry_id": entry["entry_id"], "date": entry["date"],
                "dream_text_snippet": entry["dream_text"][:100] + "..." if len(entry["dream_text"]) > 100 else entry["dream_text"],
                "themes": entry["themes"]
            })
        return summarized_entries

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_dream_entry":
            return self._add_dream_entry(kwargs.get("entry_id"), kwargs.get("date"), kwargs.get("dream_text"))
        elif operation == "analyze_dream_themes":
            return self._analyze_dream_themes()
        elif operation == "get_dream_summary":
            return self._get_dream_summary(kwargs.get("num_entries", 5))
        elif operation == "list_dream_entries":
            return list(self.journal.values())
        elif operation == "get_entry_details":
            return self.journal.get(kwargs.get("entry_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DreamJournalAndAnalyzerTool functionality...")
    tool = DreamJournalAndAnalyzerTool()
    
    try:
        print("\n--- Adding Dream Entry ---")
        tool.execute(operation="add_dream_entry", entry_id="dream_001", date="2023-10-26", dream_text="I dreamt I was flying over a vast ocean.")
        
        print("\n--- Analyzing Dream Themes ---")
        theme_report = tool.execute(operation="analyze_dream_themes")
        print(json.dumps(theme_report, indent=2))

        print("\n--- Getting Dream Summary ---")
        summary = tool.execute(operation="get_dream_summary", num_entries=1)
        print(json.dumps(summary, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.journal_file): os.remove(tool.journal_file)
        print("\nCleanup complete.")