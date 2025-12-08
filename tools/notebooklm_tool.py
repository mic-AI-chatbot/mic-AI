import logging
import json
import re
import random
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated source documents for NotebookLM
SIMULATED_DOCUMENTS = {
    "Research Paper on AI": {
        "content": "Artificial intelligence (AI) is a rapidly evolving field. Machine learning, a subset of AI, focuses on algorithms that learn from data. Deep learning is a further specialization using neural networks. AI has applications in natural language processing, computer vision, and robotics. Ethical considerations are paramount in AI development.",
        "summary": "AI is a fast-evolving field with machine learning and deep learning as subsets. It has applications in NLP, computer vision, and robotics, with ethics being a key concern."
    },
    "Meeting Notes - Project Alpha": {
        "content": "Meeting on 2023-11-15. Attendees: Alice, Bob, Charlie. Discussed project timeline, resource allocation, and next steps. Decision: Prioritize Feature X. Action Item: Bob to research cloud providers. Deadline: 2023-11-20.",
        "summary": "Project Alpha meeting discussed timeline, resources, and next steps. Decision to prioritize Feature X. Bob to research cloud providers by 2023-11-20."
    }
}

class NotebookLMSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Google's NotebookLM, acting as an
    AI-powered research assistant based on simulated user-uploaded documents.
    """

    def __init__(self, tool_name: str = "NotebookLMSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates NotebookLM: summarizes documents, generates ideas, and answers questions based on uploaded material."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for NotebookLM (e.g., 'summarize document \"Research Paper on AI\"')."
                }
            },
            "required": ["prompt"]
        }

    def _find_document_title(self, prompt: str) -> Optional[str]:
        """Helper to extract document title from prompt."""
        for doc_title in SIMULATED_DOCUMENTS.keys():
            if doc_title.lower() in prompt.lower():
                return doc_title
        return None

    def _simulate_summarize_document(self, document_title: str) -> Dict:
        doc_data = SIMULATED_DOCUMENTS.get(document_title)
        if not doc_data:
            return {"status": "error", "message": f"Document '{document_title}' not found in simulated library."}
        
        return {
            "action": "summarize_document",
            "document_title": document_title,
            "summary": doc_data["summary"]
        }

    def _simulate_answer_question(self, question: str, document_title: Optional[str] = None) -> Dict:
        answer = "I cannot find a direct answer to that question in the provided documents."
        source = "N/A"
        
        if document_title:
            doc_data = SIMULATED_DOCUMENTS.get(document_title)
            if doc_data:
                if "AI" in question and "AI" in doc_data["content"]:
                    answer = "AI is a rapidly evolving field, with subsets like machine learning and deep learning. It has applications in NLP, computer vision, and robotics."
                    source = document_title
                elif "timeline" in question and "timeline" in doc_data["content"]:
                    answer = "The project timeline was discussed, and the deadline for Bob to research cloud providers is 2023-11-20."
                    source = document_title
        
        return {
            "action": "answer_question",
            "question": question,
            "answer": answer,
            "source_document": source
        }

    def _simulate_generate_ideas(self, topic: str) -> Dict:
        ideas = [
            f"Idea 1: Explore {topic} from a historical perspective.",
            f"Idea 2: Analyze the impact of {topic} on society.",
            f"Idea 3: Develop a new application for {topic}."
        ]
        random.shuffle(ideas)
        return {
            "action": "generate_ideas",
            "topic": topic,
            "ideas": ideas[:random.randint(2, 3)]  # nosec B311
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate NotebookLM simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to NotebookLM would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        document_title = self._find_document_title(prompt)

        if "summarize document" in prompt_lower:
            if document_title:
                response_data = self._simulate_summarize_document(document_title)
            else:
                response_data = {"status": "error", "message": "Please specify a document to summarize."}
        elif "answer" in prompt_lower and "based on" in prompt_lower:
            question_match = re.search(r'answer\s+([\'\"]?)(.*?)\1\s+based on', prompt_lower)
            question = question_match.group(2) if question_match else "unknown question"
            response_data = self._simulate_answer_question(question, document_title)
        elif "generate ideas" in prompt_lower:
            topic_match = re.search(r'generate ideas for\s+([\'\"]?)(.*?)\1(?:$)', prompt_lower)
            topic = topic_match.group(2) if topic_match else "general topic"
            response_data = self._simulate_generate_ideas(topic)
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from NotebookLM for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with NotebookLM."
        return response_data

if __name__ == '__main__':
    print("Demonstrating NotebookLMSimulatorTool functionality...")
    
    notebooklm_sim = NotebookLMSimulatorTool()
    
    try:
        # 1. Summarize a document
        print("\n--- Simulating: Summarize 'Research Paper on AI' ---")
        prompt1 = "summarize document 'Research Paper on AI'"
        result1 = notebooklm_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Answer a question based on a document
        print("\n--- Simulating: Answer 'What is AI?' based on 'Research Paper on AI' ---")
        prompt2 = "answer 'What is AI?' based on 'Research Paper on AI'"
        result2 = notebooklm_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # 3. Generate ideas for a topic
        print("\n--- Simulating: Generate ideas for 'Project Alpha' ---")
        prompt3 = "generate ideas for 'Project Alpha'"
        result3 = notebooklm_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # 4. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt4 = "Tell me a joke."
        result4 = notebooklm_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")