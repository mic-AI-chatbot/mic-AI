import logging
import json
import re
import random
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated knowledge base with facts and sources
SIMULATED_KNOWLEDGE_BASE = {
    "AI": {
        "answer": "Artificial intelligence (AI) is a broad field of computer science that enables machines to perform tasks typically requiring human intelligence.",
        "sources": ["Smith, J. (2022). 'Foundations of AI'. Tech Press.", "Wikipedia. 'Artificial Intelligence'."]
    },
    "Quantum Computing": {
        "answer": "Quantum computing utilizes quantum-mechanical phenomena like superposition and entanglement to perform computations, potentially solving problems intractable for classical computers.",
        "sources": ["IBM Quantum Experience. 'What is Quantum Computing?'.", "Johnson, A. (2023). 'Quantum Algorithms Explained'. Science Journal."]
    },
    "Climate Change": {
        "answer": "Climate change refers to long-term shifts in temperatures and weather patterns, primarily caused by human activities, especially the burning of fossil fuels.",
        "sources": ["NASA. 'Climate Change: Vital Signs of the Planet'.", "IPCC. 'Sixth Assessment Report'."]
    }
}

class PerplexityAISimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Perplexity AI, providing factual
    answers with simulated sources, guiding research, and supporting domain-specific searches.
    """

    def __init__(self, tool_name: str = "PerplexityAISimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Perplexity AI: factual answers with sources, guiding research, domain-specific searches."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for Perplexity AI (e.g., 'answer \"What is AI?\"')."
                }
            },
            "required": ["prompt"]
        }

    def _find_topic_in_kb(self, prompt: str) -> Optional[str]:
        """Helper to extract topic from prompt and check against KB."""
        for topic in SIMULATED_KNOWLEDGE_BASE.keys():
            if topic.lower() in prompt.lower():
                return topic
        return None

    def _simulate_answer_question(self, question: str) -> Dict:
        topic = self._find_topic_in_kb(question)
        if topic:
            data = SIMULATED_KNOWLEDGE_BASE[topic]
            return {
                "action": "answer_question",
                "question": question,
                "answer": data["answer"],
                "sources": data["sources"]
            }
        else:
            return {
                "action": "answer_question",
                "question": question,
                "answer": "I cannot find a definitive answer to that question in my simulated knowledge base.",
                "sources": []
            }

    def _simulate_research_topic(self, topic: str, domain: Optional[str] = None) -> Dict:
        related_questions = [
            f"What are the ethical implications of {topic.lower()}?",
            f"How does {topic.lower()} impact society?",
            f"What are the latest advancements in {topic.lower()}?"
        ]
        random.shuffle(related_questions)
        
        return {
            "action": "research_topic",
            "topic": topic,
            "domain": domain or "General",
            "simulated_results": [
                f"Found 5 relevant articles on '{topic}' in the {domain or 'general'} domain.",
                f"Key insight: {SIMULATED_KNOWLEDGE_BASE.get(topic, {}).get('answer', 'No specific insight found.')}"
            ],
            "related_questions": related_questions[random.randint(2, 3)]  # nosec B311
        }

    def _simulate_cite_sources(self, topic: str) -> Dict:
        data = SIMULATED_KNOWLEDGE_BASE.get(topic)
        if data and data["sources"]:
            return {
                "action": "cite_sources",
                "topic": topic,
                "sources": data["sources"]
            }
        else:
            return {
                "action": "cite_sources",
                "topic": topic,
                "sources": [],
                "message": "No specific sources found in simulated knowledge base for this topic."
            }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate Perplexity AI simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Perplexity AI would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        topic = self._find_topic_in_kb(prompt)

        if "answer" in prompt_lower:
            question_match = re.search(r'answer\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt_lower)
            question = question_match.group(2) if question_match else prompt
            response_data = self._simulate_answer_question(question.title())
        elif "research" in prompt_lower:
            topic_match = re.search(r'research\s+([\'\"]?)(.*?)\1(?:$|\s+in)', prompt_lower)
            research_topic = topic_match.group(2).title() if topic_match else "General Research"
            domain_match = re.search(r'in\s+([\'\"]?)(.*?)\1(?:$)', prompt_lower)
            domain = domain_match.group(2).title() if domain_match else None
            response_data = self._simulate_research_topic(research_topic, domain)
        elif "cite sources" in prompt_lower or "sources for" in prompt_lower:
            cite_topic_match = re.search(r'(?:cite sources for|sources for)\s+([\'\"]?)(.*?)\1(?:$)', prompt_lower)
            cite_topic = cite_topic_match.group(2).title() if cite_topic_match else "General Topic"
            response_data = self._simulate_cite_sources(cite_topic)
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Perplexity AI for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Perplexity AI."
        return response_data

if __name__ == '__main__':
    print("Demonstrating PerplexityAISimulatorTool functionality...")
    
    perplexity_sim = PerplexityAISimulatorTool()
    
    try:
        # 1. Answer a question
        print("\n--- Simulating: Answer 'What is AI?' ---")
        prompt1 = "answer 'What is AI?'"
        result1 = perplexity_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Research a topic in a specific domain
        print("\n--- Simulating: Research 'quantum computing' in academic domain ---")
        prompt2 = "research 'quantum computing' in academic domain"
        result2 = perplexity_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # 3. Cite sources for a topic
        print("\n--- Simulating: Cite sources for 'Climate Change' ---")
        prompt3 = "cite sources for 'Climate Change'"
        result3 = perplexity_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # 4. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt4 = "How do I bake a cake?"
        result4 = perplexity_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")