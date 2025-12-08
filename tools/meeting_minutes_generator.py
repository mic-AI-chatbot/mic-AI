import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Union
import spacy
from collections import Counter

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'.")
    nlp = None

class MeetingMinutesGeneratorTool(BaseTool):
    """
    A tool for generating structured meeting minutes, including a summary,
    key topics, action items, and decisions from a meeting transcript.
    """

    def __init__(self, tool_name: str = "MeetingMinutesGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        if nlp is None:
            raise RuntimeError("spaCy model 'en_core_web_sm' is not available.")

    @property
    def description(self) -> str:
        return "Generates meeting minutes by extracting topics, action items, and decisions from a transcript."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "transcript": {"type": "string", "description": "The full text of the meeting transcript."},
                "output_format": {"type": "string", "enum": ["json", "text", "markdown"], "default": "json"}
            },
            "required": ["transcript"]
        }

    def _extract_key_topics(self, doc: spacy.tokens.Doc) -> List[str]:
        """Extracts key topics based on the most frequent nouns."""
        nouns = [token.lemma_.lower() for token in doc if token.pos_ == "NOUN" and not token.is_stop and len(token.text) > 3]
        topic_counts = Counter(nouns)
        return [topic for topic, count in topic_counts.most_common(5)]

    def _extract_action_items_and_decisions(self, doc: spacy.tokens.Doc) -> Dict[str, List[Any]]:
        """Extracts action items and decisions using keyword matching and NER."""
        action_items = []
        decisions = []
        action_keywords = ["action item", "to-do", "will do", "i will", "we will", "assign to", "needs to"]
        decision_keywords = ["we decided", "the decision is", "we agreed", "it was decided", "we will move forward with"]

        for sent in doc.sents:
            sent_text_lower = sent.text.lower()
            if any(keyword in sent_text_lower for keyword in action_keywords):
                person = "Unassigned"
                for ent in sent.ents:
                    if ent.label_ == "PERSON":
                        person = ent.text
                        break
                action_items.append({"assigned_to": person, "task": sent.text.strip()})
            elif any(keyword in sent_text_lower for keyword in decision_keywords):
                decisions.append(sent.text.strip())
        
        return {"action_items": action_items, "decisions": decisions}

    def _generate_summary(self, doc: spacy.tokens.Doc, num_sentences: int = 3) -> str:
        """Generates an extractive summary based on sentence importance."""
        # Simple scoring: longer sentences with more nouns are more important.
        sentence_scores = []
        for sent in doc.sents:
            score = len(sent.text.split()) # Base score on length
            score += sum(1 for token in sent if token.pos_ == "NOUN") # Add score for nouns
            sentence_scores.append((sent.text.strip(), score))
        
        sorted_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
        top_sentences_text = [s[0] for s in sorted_sentences[:num_sentences]]
        return " ".join(top_sentences_text)

    def _format_output(self, data: Dict[str, Any], output_format: str) -> Union[str, Dict[str, Any]]:
        """Formats the extracted information into the desired output format."""
        if output_format == "json":
            return data

        title = data.get("title", "Meeting Minutes")
        date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        if output_format == "text":
            lines = [f"{title}", f"Date: {date}", "\n--- SUMMARY ---", data['summary'], "\n--- KEY TOPICS ---"]
            lines.extend(f"- {topic}" for topic in data['key_topics'])
            lines.append("\n--- ACTION ITEMS ---")
            lines.extend(f"- {item['task']} (Assigned to: {item['assigned_to']})" for item in data['action_items'])
            lines.append("\n--- DECISIONS ---")
            lines.extend(f"- {decision}" for decision in data['decisions'])
            return "\n".join(lines)

        if output_format == "markdown":
            lines = [f"# {title}", f"**Date:** {date}", "\n## Summary", data['summary'], "\n## Key Topics"]
            lines.extend(f"* {topic}" for topic in data['key_topics'])
            lines.append("\n## Action Items")
            lines.extend(f"* {item['task']} (**Assigned to:** {item['assigned_to']})" for item in data['action_items'])
            lines.append("\n## Decisions")
            lines.extend(f"* {decision}" for decision in data['decisions'])
            return "\n".join(lines)
            
        return data # Fallback to JSON

    def execute(self, transcript: str, output_format: str = "json", **kwargs: Any) -> Union[str, Dict[str, Any]]:
        """
        Processes a meeting transcript to generate structured minutes.
        """
        doc = nlp(transcript)
        
        extracted_info = self._extract_action_items_and_decisions(doc)
        
        minutes_data = {
            "title": "Meeting Minutes",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": self._generate_summary(doc),
            "key_topics": self._extract_key_topics(doc),
            "action_items": extracted_info["action_items"],
            "decisions": extracted_info["decisions"]
        }
        
        return self._format_output(minutes_data, output_format)

if __name__ == '__main__':
    print("Demonstrating MeetingMinutesGeneratorTool functionality...")
    
    generator_tool = MeetingMinutesGeneratorTool()
    
    sample_transcript = """
    Hello everyone, let's start the weekly sync. The main topic today is the Q4 product launch.
    Based on our discussion, we decided to move forward with the 'Phoenix' marketing campaign.
    This is a major step. Regarding the timeline, we agreed that the launch date is set for December 15th.
    Now for tasks. Alice, I will assign to you the job of finalizing the press release.
    Bob needs to deploy the final build to the staging server by Friday. This is an important action item.
    I will also follow up with the design team. A key decision is that the new logo will be used.
    """
    
    try:
        # 1. Generate JSON output (default)
        print("\n--- Generating minutes in JSON format ---")
        json_output = generator_tool.execute(transcript=sample_transcript)
        print(json.dumps(json_output, indent=2))

        # 2. Generate plain text output
        print("\n\n--- Generating minutes in TEXT format ---")
        text_output = generator_tool.execute(transcript=sample_transcript, output_format="text")
        print(text_output)

        # 3. Generate Markdown output
        print("\n\n--- Generating minutes in MARKDOWN format ---")
        markdown_output = generator_tool.execute(transcript=sample_transcript, output_format="markdown")
        print(markdown_output)

    except Exception as e:
        print(f"\nAn error occurred: {e}")