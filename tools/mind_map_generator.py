import logging
import os
import json
from typing import Dict, Any, List, Union
import spacy
from collections import Counter
import PyPDF2

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'.")
    nlp = None

class MindMapGeneratorTool(BaseTool):
    """
    A tool for generating a textual mind map from text content or a PDF,
    using NLP to identify topics, sub-topics, and key details.
    """

    def __init__(self, tool_name: str = "MindMapGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        if nlp is None:
            raise RuntimeError("spaCy model 'en_core_web_sm' is not available.")

    @property
    def description(self) -> str:
        return "Generates a textual mind map from text or a PDF using NLP analysis."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_content": {"type": "string", "description": "The text content or absolute path to a PDF document."},
                "input_type": {"type": "string", "enum": ["text", "pdf"], "description": "The type of input provided ('text' or 'pdf')."}
            },
            "required": ["input_content", "input_type"]
        }

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extracts text from a PDF file."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                return "".join(page.extract_text() for page in reader.pages)
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {e}")

    def _generate_mind_map_structure(self, text: str) -> Dict:
        """Generates a hierarchical mind map structure using NLP."""
        doc = nlp(text)

        # Find the main topic (most frequent noun chunk)
        noun_chunks = [chunk.text.strip().lower() for chunk in doc.noun_chunks if len(chunk.text.split()) < 4]
        main_topic = Counter(noun_chunks).most_common(1)[0][0] if noun_chunks else "Document Analysis"

        # Find sub-topics (sentences containing the main topic or other important nouns)
        all_nouns = [token.lemma_.lower() for token in doc if token.pos_ == "NOUN" and not token.is_stop]
        top_nouns = {item[0] for item in Counter(all_nouns).most_common(5)}
        
        sub_topics = []
        processed_sents = set()

        for sent in doc.sents:
            if len(sub_topics) >= 5: break
            sent_text = sent.text.strip()
            if sent_text in processed_sents: continue

            # A sentence is a potential sub-topic if it contains important nouns
            if any(noun in sent.text.lower() for noun in top_nouns):
                details = [chunk.text.strip() for chunk in sent.noun_chunks if chunk.text.lower() != main_topic]
                sub_topics.append({"title": sent_text, "details": details[:3]}) # Max 3 details
                processed_sents.add(sent_text)
        
        return {"main_topic": main_topic.title(), "sub_topics": sub_topics}

    def _format_as_text(self, mind_map_data: Dict) -> str:
        """Formats the mind map data into an indented text string."""
        lines = [f"Main Topic: {mind_map_data['main_topic']}"]
        for sub_topic in mind_map_data.get("sub_topics", []):
            lines.append(f"  - Sub-topic: {sub_topic['title']}")
            for detail in sub_topic.get("details", []):
                lines.append(f"    - Detail: {detail}")
        return "\n".join(lines)

    def execute(self, input_content: str, input_type: str, **kwargs: Any) -> str:
        """
        Generates and formats a mind map from the provided content.
        """
        content_to_analyze = ""
        if input_type == "text":
            content_to_analyze = input_content
        elif input_type == "pdf":
            content_to_analyze = self._extract_text_from_pdf(input_content)
        else:
            raise ValueError("Invalid input_type. Must be 'text' or 'pdf'.")

        if not content_to_analyze.strip():
            return "Error: No content to generate a mind map from."

        mind_map_structure = self._generate_mind_map_structure(content_to_analyze)
        
        return self._format_as_text(mind_map_structure)

if __name__ == '__main__':
    print("Demonstrating MindMapGeneratorTool functionality...")
    
    generator_tool = MindMapGeneratorTool()
    
    sample_text = """
    The future of renewable energy is a critical topic for global sustainability.
    Solar power continues to be a leading contender, with advancements in photovoltaic efficiency.
    These new solar panels are cheaper to produce. Wind energy is another major player,
    especially offshore wind farms which can generate substantial power. However, wind turbines
    face challenges in terms of maintenance and environmental impact. Finally, geothermal energy
    offers a consistent power source by tapping into the Earth's heat, making it a reliable baseline provider.
    """
    
    try:
        print("\n--- Generating mind map from sample text ---")
        mind_map_output = generator_tool.execute(input_content=sample_text, input_type="text")
        print(mind_map_output)

        # Demonstrate PDF functionality (requires a dummy PDF)
        dummy_pdf_path = "dummy_document.pdf"
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            c = canvas.Canvas(dummy_pdf_path, pagesize=letter)
            textobject = c.beginText(40, 750)
            for line in sample_text.strip().split('\n'):
                textobject.textLine(line.strip())
            c.drawText(textobject)
            c.save()
            
            print(f"\n--- Generating mind map from dummy PDF: {dummy_pdf_path} ---")
            pdf_mind_map = generator_tool.execute(input_content=dummy_pdf_path, input_type="pdf")
            print(pdf_mind_map)
        except ImportError:
            print("\nSkipping PDF demonstration: 'reportlab' is not installed.")
        finally:
            if os.path.exists(dummy_pdf_path):
                os.remove(dummy_pdf_path)

    except Exception as e:
        print(f"\nAn error occurred: {e}")