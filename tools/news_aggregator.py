from mic.tool_manager import BaseTool
from mic.llm_loader import LLMLoader as LLMLoaderClass

class NewsAggregator(BaseTool):
    def __init__(self, tool_name: str = "News Aggregator", llm_loader: LLMLoaderClass = None):
        super().__init__(tool_name, llm_loader)
        self.llm_loader = llm_loader or LLMLoaderClass()
        self.llm_loader = llm_loader or LLMLoaderClass()

    def run(self, *args, **kwargs):
        # Placeholder for news aggregation logic
        return f"Running {self.tool_name} with args: {kwargs}"

if __name__ == "__main__":
    # Example usage of the NewsAggregator
    tool = NewsAggregator()
    print(tool.run(category="technology"))