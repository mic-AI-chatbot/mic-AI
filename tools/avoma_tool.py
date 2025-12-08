import logging
import json
import random
import re
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Avoma tools will not be fully functional.")

logger = logging.getLogger(__name__)

class MeetingSimulator:
    """Generates mock meeting transcripts for demonstration purposes."""
    def generate_transcript(self, topic: str, num_speakers: int = 2, duration_minutes: int = 10) -> str:
        speakers = [f"Speaker {i+1}" for i in range(num_speakers)]
        transcript_lines = []
        
        # Sample dialogue based on common meeting topics
        sample_dialogue = {
            "sales_pitch": [
                "Hello, thanks for joining. Today we're excited to show you our new product.",
                "Our solution addresses key pain points like scalability, cost, and integration.",
                "We believe this will significantly improve your team's efficiency and ROI.",
                "What are your current challenges in this area? How does your existing solution handle X?",
                "The pricing model is flexible, starting at $X per month, with enterprise options.",
                "We can offer a personalized demo next week if you're interested in seeing it in action."
            ],
            "project_update": [
                "Good morning team. Let's go over the project status for Sprint 3.",
                "Task A is on track, currently 80% completed, awaiting final review.",
                "Task B has a slight delay due to unexpected resource allocation issues.",
                "We need to re-evaluate the timeline for phase 2, potentially pushing back by 3 days.",
                "Any blockers or concerns from anyone regarding their current assignments?",
                "Next steps: follow up with engineering on the critical bug fix and update the JIRA board."
            ],
            "customer_support": [
                "Thank you for calling. How can I help you today?",
                "I understand you're having trouble with your internet connection.",
                "Could you please describe the issue in more detail?",
                "Have you tried restarting your router?",
                "Let me check your account details for any service interruptions.",
                "I'll escalate this to our technical team for further investigation."
            ]
        }
        
        dialogue_options = sample_dialogue.get(topic.lower().replace(" ", "_"), sample_dialogue["project_update"])

        for i in range(duration_minutes * 5): # Simulate ~5 lines per minute
            speaker = random.choice(speakers)  # nosec B311
            line = random.choice(dialogue_options)  # nosec B311
            transcript_lines.append(f"[{i//60:02d}:{i%60:02d}] {speaker}: {line}") # Simple timestamp
        
        return "\n".join(transcript_lines)

class AvomaModel:
    """Manages the text generation model for Avoma-like tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AvomaModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for Avoma tools are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for Avoma tools...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

avoma_model_instance = AvomaModel()
meeting_simulator = MeetingSimulator()

class TranscribeAndSummarizeMeetingTool(BaseTool):
    """Generates a mock meeting transcript and summarizes it using an AI model."""
    def __init__(self, tool_name="transcribe_and_summarize_meeting"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a mock meeting transcript based on a topic and summarizes it using an AI model, simulating Avoma's meeting assistant feature."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "meeting_topic": {"type": "string", "description": "The topic of the simulated meeting (e.g., 'sales_pitch', 'project_update', 'customer_support')."},
                "duration_minutes": {"type": "integer", "description": "The duration of the simulated meeting in minutes.", "default": 10}
            },
            "required": ["meeting_topic"]
        }

    def execute(self, meeting_topic: str, duration_minutes: int = 10, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        transcript = meeting_simulator.generate_transcript(meeting_topic, duration_minutes=duration_minutes)
        
        prompt = f"Summarize the following meeting transcript concisely, highlighting key decisions and action items:\n\n{transcript}\n\nSummary:"
        summary = avoma_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 200)
        
        report = {
            "meeting_topic": meeting_topic,
            "duration_minutes": duration_minutes,
            "transcript": transcript,
            "summary": summary
        }
        return json.dumps(report, indent=2)

class AnalyzeMeetingConversationTool(BaseTool):
    """Analyzes a meeting transcript for conversation intelligence using an AI model."""
    def __init__(self, tool_name="analyze_meeting_conversation"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a meeting transcript to extract key topics, identify talk ratios between speakers, and assess overall sentiment using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"transcript": {"type": "string", "description": "The full transcript of the meeting to analyze."}},
            "required": ["transcript"]
        }

    def execute(self, transcript: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        # Simulate talk ratio
        speaker_lines = {}
        total_lines = 0
        for line in transcript.split('\n'):
            match = re.match(r"\[.*?\] (Speaker \d+):", line)
            if match:
                speaker = match.group(1)
                speaker_lines[speaker] = speaker_lines.get(speaker, 0) + 1
                total_lines += 1
        
        talk_ratio = {speaker: round((count / total_lines) * 100, 2) for speaker, count in speaker_lines.items()} if total_lines > 0 else {}

        # Use AI for key topics and sentiment
        prompt_topics = f"Extract the key topics and discussion points from the following meeting transcript:\n\n{transcript}\n\nKey Topics:"
        key_topics = avoma_model_instance.generate_response(prompt_topics, max_length=len(prompt_topics.split()) + 100)

        prompt_sentiment = f"Analyze the overall sentiment of the following meeting transcript (e.g., 'positive', 'neutral', 'negative', 'mixed'):\n\n{transcript}\n\nOverall Sentiment:"
        sentiment = avoma_model_instance.generate_response(prompt_sentiment, max_length=len(prompt_sentiment.split()) + 20)
        
        report = {
            "talk_ratio_percent": talk_ratio,
            "key_topics": key_topics.split('\n'),
            "overall_sentiment": sentiment
        }
        return json.dumps(report, indent=2)

class PerformDealRiskAnalysisTool(BaseTool):
    """Performs deal risk analysis from meeting data using an AI model."""
    def __init__(self, tool_name="perform_deal_risk_analysis"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes meeting transcripts and summaries to assess the risk level of a sales deal (e.g., 'high', 'medium', 'low') and provides reasons, simulating Avoma's revenue intelligence."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "meeting_summary": {"type": "string", "description": "A summary of the sales meeting."},
                "deal_context": {"type": "string", "description": "Additional context about the deal (e.g., 'customer is price-sensitive', 'competitor is offering a discount', 'customer expressed budget concerns')."}
            },
            "required": ["meeting_summary", "deal_context"]
        }

    def execute(self, meeting_summary: str, deal_context: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Analyze the following sales meeting summary and deal context to assess the risk level of the deal (High, Medium, Low). Provide clear reasons for the assessment.\n\nMeeting Summary: {meeting_summary}\nDeal Context: {deal_context}\n\nDeal Risk Assessment (in JSON format with 'risk_level' and 'reasons'):"
        
        generated_text = avoma_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 200)
        
        # Attempt to parse the generated text as JSON
        json_start = generated_text.find('{')
        json_end = generated_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = generated_text[json_start:json_end]
            try:
                return json.dumps(json.loads(json_str), indent=2)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse generated JSON: {json_str}")
                return json.dumps({"raw_output": generated_text, "error": "Generated output was not valid JSON. Manual parsing needed."})
        else:
            return json.dumps({"raw_output": generated_text, "error": "Could not find JSON in generated output. Manual parsing needed."})