# mic/tool_registry.py

from typing import Dict
from tools.base_tool import BaseTool
from tools.calendar_management_tool import AdvancedCalendarManagementTool

# Import the specific tool classes you want to use
from tools.conversational_ai_tool import ConversationalAITool
from tools.summarization_tool import SummarizationTool
from tools.code_review_tool import AdvancedCodeReviewTool
from tools.code_debugging_tool import CodeDebuggingTool
from tools.creative_writing_tool import CreativeWritingTool
from tools.web_search_tool import WebSearchTool # Assuming this tool exists and is functional

# Create instances of the tools
tool_instances = [
    ConversationalAITool(),
    SummarizationTool(),
    AdvancedCodeReviewTool(),
    CodeDebuggingTool(),
    CreativeWritingTool(),
    AdvancedCalendarManagementTool(),
    WebSearchTool(),
]

# Build the registry dictionary
tool_registry: Dict[str, BaseTool] = {tool.tool_name: tool for tool in tool_instances}

print(f"Explicitly loaded tools: {list(tool_registry.keys())}")