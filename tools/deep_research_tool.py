import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DeepResearchTool(BaseTool):
    """
    A tool for simulating multi-step, complex research tasks.
    """

    def __init__(self, tool_name: str = "deep_research_tool"):
        super().__init__(tool_name)
        self.reports_file = "research_reports.json"
        self.knowledge_base_file = "knowledge_base.json"
        self.reports: Dict[str, Dict[str, Any]] = self._load_state(self.reports_file)
        self.knowledge_base: Dict[str, Dict[str, Any]] = self._load_state(self.knowledge_base_file)

    @property
    def description(self) -> str:
        return "Simulates deep research tasks: adds knowledge entries, performs research queries, and generates structured reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The research operation to perform.",
                    "enum": ["add_knowledge_entry", "perform_research", "generate_report", "list_reports", "get_report_details"]
                },
                "entry_id": {"type": "string"},
                "topic": {"type": "string"},
                "content": {"type": "string"},
                "source": {"type": "string"},
                "research_query": {"type": "string"},
                "depth": {"type": "integer", "minimum": 1},
                "report_id": {"type": "string"},
                "findings": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["operation"]
        }

    def _load_state(self, file_path: str) -> Dict[str, Any]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted state file '{file_path}'. Starting fresh.")
                    return {}
        return {}

    def _save_state(self, state: Dict[str, Any], file_path: str) -> None:
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=4)

    def _add_knowledge_entry(self, entry_id: str, topic: str, content: str, source: str) -> Dict[str, Any]:
        if not all([entry_id, topic, content, source]):
            raise ValueError("Entry ID, topic, content, and source cannot be empty.")
        if entry_id in self.knowledge_base:
            raise ValueError(f"Knowledge entry '{entry_id}' already exists.")

        new_entry = {
            "entry_id": entry_id, "topic": topic, "content": content, "source": source,
            "added_at": datetime.now().isoformat()
        }
        self.knowledge_base[entry_id] = new_entry
        self._save_state(self.knowledge_base, self.knowledge_base_file)
        return new_entry

    def _perform_research(self, research_query: str, depth: int = 1) -> Dict[str, Any]:
        if not research_query: raise ValueError("Research query cannot be empty.")

        findings: List[Dict[str, Any]] = []
        for entry_id, entry in self.knowledge_base.items():
            if research_query.lower() in entry["topic"].lower() or research_query.lower() in entry["content"].lower():
                findings.append({
                    "entry_id": entry_id, "topic": entry["topic"],
                    "summary": entry["content"][:100] + "...", "source": entry["source"]
                })
        
        if depth > 1 and len(findings) > 1:
            synthesized_summary = f"Synthesized summary for '{research_query}': Combining insights from {len(findings)} sources. "
            synthesized_summary += "Key points include: " + ", ".join([f.get("topic", "") for f in findings]) + "."
            findings.insert(0, {"type": "synthesis", "content": synthesized_summary})

        research_result = {
            "research_query": research_query, "performed_at": datetime.now().isoformat(), "findings": findings
        }
        return research_result

    def _generate_report(self, report_id: str, research_query: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not all([report_id, research_query, findings]):
            raise ValueError("Report ID, research query, and findings cannot be empty.")
        if report_id in self.reports:
            raise ValueError(f"Report '{report_id}' already exists.")

        report_content = f"## Research Report: {research_query}\n\n"
        report_content += f"**Generated At:** {datetime.now().isoformat()}\n\n"
        report_content += f"### Summary\n"
        
        summary_found = False
        for finding in findings:
            if finding.get("type") == "synthesis":
                report_content += f"{finding['content']}\n\n"
                summary_found = True
                break
        if not summary_found: report_content += "No specific synthesis found. Summarizing individual findings.\n\n"

        report_content += "### Detailed Findings\n"
        for i, finding in enumerate(findings):
            if finding.get("type") != "synthesis":
                report_content += f"- **Finding {i+1}:** {finding.get('topic', 'N/A')}\n"
                report_content += f"  - Summary: {finding.get('summary', finding.get('content', 'N/A'))}\n"
                report_content += f"  - Source: {finding.get('source', 'N/A')}\n\n"
        
        new_report = {
            "report_id": report_id, "research_query": research_query, "generated_at": datetime.now().isoformat(),
            "content": report_content, "findings_summary": findings
        }
        self.reports[report_id] = new_report
        self._save_state(self.reports, self.reports_file)
        return new_report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_knowledge_entry":
            return self._add_knowledge_entry(kwargs.get("entry_id"), kwargs.get("topic"), kwargs.get("content"), kwargs.get("source"))
        elif operation == "perform_research":
            return self._perform_research(kwargs.get("research_query"), kwargs.get("depth", 1))
        elif operation == "generate_report":
            return self._generate_report(kwargs.get("report_id"), kwargs.get("research_query"), kwargs.get("findings"))
        elif operation == "list_reports":
            return [{k: v for k, v in report.items() if k != "content"} for report in self.reports.values()]
        elif operation == "get_report_details":
            return self.reports.get(kwargs.get("report_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DeepResearchTool functionality...")
    tool = DeepResearchTool()
    
    try:
        print("\n--- Adding Knowledge Entry ---")
        tool.execute(operation="add_knowledge_entry", entry_id="ai_ethics_1", topic="AI Ethics", content="AI systems should be fair.", source="Whitepaper")
        
        print("\n--- Performing Research ---")
        research_results = tool.execute(operation="perform_research", research_query="AI Ethics", depth=1)
        print(json.dumps(research_results, indent=2))

        print("\n--- Generating Report ---")
        report_result = tool.execute(operation="generate_report", report_id="report_001", research_query="AI Ethics", findings=research_results["findings"])
        print(json.dumps(report_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.reports_file): os.remove(tool.reports_file)
        if os.path.exists(tool.knowledge_base_file): os.remove(tool.knowledge_base_file)
        print("\nCleanup complete.")
