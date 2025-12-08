

import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
from collections import Counter

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# A simple list of common English stop words
STOP_WORDS = set([
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', "can't", 'cannot',
    'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few',
    'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll",
    "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll",
    "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most',
    "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our',
    'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should',
    "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves',
    'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those',
    'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're",
    "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who',
    "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're",
    "you've", 'your', 'yours', 'yourself', 'yourselves'
])

class ExtractiveSummarizerTool(BaseTool):
    """
    Performs extractive summarization on long texts using a classic NLP sentence-scoring algorithm.
    """

    def __init__(self, tool_name: str = "ExtractiveSummarizer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "summarization_data.json")
        self.data = self._load_data(self.data_file, default={"documents": {}, "summaries": {}})

    @property
    def description(self) -> str:
        return "Summarizes long text by extracting the most important sentences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_document", "generate_summary", "list_documents", "get_summary_details"]},
                "doc_id": {"type": "string"}, "title": {"type": "string"}, "content": {"type": "string"},
                "summary_id": {"type": "string"},
                "summary_length": {"type": "string", "default": "medium", "enum": ["short", "medium", "long"]}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.data_file, 'w') as f: json.dump(self.data, f, indent=4)

    def add_document(self, doc_id: str, title: str, content: str) -> Dict[str, Any]:
        """Adds a new document to the system."""
        if not all([doc_id, title, content]):
            raise ValueError("Document ID, title, and content are required.")
        if doc_id in self.data["documents"]:
            raise ValueError(f"Document with ID '{doc_id}' already exists.")
        
        new_doc = {"doc_id": doc_id, "title": title, "content": content, "added_at": datetime.now().isoformat()}
        self.data["documents"][doc_id] = new_doc
        self._save_data()
        self.logger.info(f"Document '{title}' ({doc_id}) added.")
        return new_doc

    def _extractive_summarize(self, content: str, length: str) -> str:
        """Performs extractive summarization."""
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', content)
        if not sentences: return ""

        words = [word.lower() for word in re.findall(r'\b\w+\b', content) if word.lower() not in STOP_WORDS]
        word_freq = Counter(words)
        
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            sentence_words = [word.lower() for word in re.findall(r'\b\w+\b', sentence)]
            score = sum(word_freq[word] for word in sentence_words)
            sentence_scores[i] = score

        length_map = {"short": 0.15, "medium": 0.3, "long": 0.5}
        num_sentences = int(len(sentences) * length_map[length])
        num_sentences = max(1, num_sentences) # Ensure at least one sentence

        sorted_sentences = sorted(sentence_scores.items(), key=lambda item: item[1], reverse=True)
        top_sentence_indices = sorted([item[0] for item in sorted_sentences[:num_sentences]])
        
        summary = ' '.join([sentences[i] for i in top_sentence_indices])
        return summary

    def generate_summary(self, summary_id: str, doc_id: str, summary_length: str = "medium") -> Dict[str, Any]:
        """Generates a real extractive summary of a document."""
        document = self.data["documents"].get(doc_id)
        if not document: raise ValueError(f"Document with ID '{doc_id}' not found.")
        if summary_id in self.data["summaries"]: raise ValueError(f"Summary with ID '{summary_id}' already exists.")
        
        summary_text = self._extractive_summarize(document["content"], summary_length)
        
        new_summary = {
            "summary_id": summary_id, "doc_id": doc_id, "summary_length": summary_length,
            "generated_summary": summary_text, "generated_at": datetime.now().isoformat()
        }
        self.data["summaries"][summary_id] = new_summary
        self._save_data()
        self.logger.info(f"Summary '{summary_id}' generated for document '{doc_id}'.")
        return new_summary

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lists all added documents (excluding full content)."""
        return [{k: v for k, v in doc.items() if k != "content"} for doc in self.data["documents"].values()]

    def get_summary_details(self, summary_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the full details of a specific summary."""
        return self.data["summaries"].get(summary_id)

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "add_document": self.add_document, "generate_summary": self.generate_summary,
            "list_documents": self.list_documents, "get_summary_details": self.get_summary_details
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating ExtractiveSummarizerTool functionality...")
    temp_dir = "temp_summarizer_data"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    summarizer_tool = ExtractiveSummarizerTool(data_dir=temp_dir)
    
    long_text = "Advancements in quantum computing represent a paradigm shift. These systems leverage quantum-mechanical phenomena, such as superposition and entanglement, to perform computations. Unlike classical computers that use bits, quantum computers use qubits. This fundamental difference allows them to solve complex problems that are intractable for classical systems. Key applications include cryptography, where quantum algorithms threaten current encryption standards, and drug discovery, where simulating molecular interactions becomes feasible. However, building stable, fault-tolerant quantum computers remains a significant engineering challenge. Qubit coherence times are short, and error rates are high. Researchers are actively developing new materials and error-correction codes to overcome these hurdles. The field is a collaborative effort between physics, computer science, and engineering, promising a transformative future."

    try:
        # --- Add a document ---
        print("\n--- Adding a document ---")
        summarizer_tool.execute(
            operation="add_document", doc_id="qc_paper_01",
            title="The Future of Quantum Computing", content=long_text
        )
        print("Document 'qc_paper_01' added.")

        # --- Generate a real summary ---
        print("\n--- Generating a 'short' summary ---")
        summary = summarizer_tool.execute(
            operation="generate_summary", summary_id="qc_summary_short",
            doc_id="qc_paper_01", summary_length="short"
        )
        print("Generated Summary:")
        print(summary['generated_summary'])

        # --- List documents ---
        print("\n--- Listing all documents ---")
        docs = summarizer_tool.execute(operation="list_documents")
        print(json.dumps(docs, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        import shutil
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
