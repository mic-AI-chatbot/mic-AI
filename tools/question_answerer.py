
import logging
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simple in-memory knowledge base for factual answers
KNOWLEDGE_BASE = {
    "what is the capital of france?": "The capital of France is Paris.",
    "who invented the light bulb?": "Thomas Edison is widely credited with inventing the practical incandescent light bulb.",
    "what is the highest mountain in the world?": "Mount Everest is the highest mountain in the world.",
    "what is the chemical symbol for water?": "The chemical symbol for water is H2O.",
    "what is the largest ocean?": "The Pacific Ocean is the largest ocean on Earth."
}

class QuestionAnswererTool(BaseTool):
    """
    A tool that answers factual questions based on its internal knowledge base.
    """

    def __init__(self, tool_name: str = "QuestionAnswerer", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Answers factual questions based on its internal knowledge base."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to be answered."}
            },
            "required": ["question"]
        }

    def execute(self, question: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Answers a factual question based on the internal knowledge base.
        """
        question_lower = question.lower().strip()
        
        answer = KNOWLEDGE_BASE.get(question_lower)
        
        if answer:
            return {"status": "success", "question": question, "answer": answer}
        else:
            # Simple keyword matching for partial answers or related topics
            for kb_question, kb_answer in KNOWLEDGE_BASE.items():
                if any(word in question_lower for word in kb_question.split()):
                    return {"status": "info", "question": question, "answer": f"I don't have a direct answer, but I know about '{kb_question.replace('what is the ', '').replace('who invented the ', '').replace('?', '')}'.", "related_answer": kb_answer}
            
            return {"status": "not_found", "question": question, "answer": "I don't have an answer to that question in my knowledge base."}

if __name__ == '__main__':
    print("Demonstrating QuestionAnswererTool functionality...")
    
    qa_tool = QuestionAnswererTool()
    
    try:
        # 1. Ask a question in the knowledge base
        print("\n--- Asking: 'What is the capital of France?' ---")
        result1 = qa_tool.execute(question="What is the capital of France?")
        print(json.dumps(result1, indent=2))

        # 2. Ask another question in the knowledge base
        print("\n--- Asking: 'Who invented the light bulb?' ---")
        result2 = qa_tool.execute(question="Who invented the light bulb?")
        print(json.dumps(result2, indent=2))
        
        # 3. Ask a question not directly in the knowledge base, but with keywords
        print("\n--- Asking: 'Tell me about water.' ---")
        result3 = qa_tool.execute(question="Tell me about water.")
        print(json.dumps(result3, indent=2))

        # 4. Ask a question not in the knowledge base
        print("\n--- Asking: 'What is the meaning of life?' ---")
        result4 = qa_tool.execute(question="What is the meaning of life?")
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
