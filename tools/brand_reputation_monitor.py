import logging
import json
import random
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import BrandMention
from sqlalchemy.exc import IntegrityError

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Sentiment analysis will not be available.")

logger = logging.getLogger(__name__)

class MentionGenerator:
    """Generates mock brand mentions for simulation."""
    def generate_mention_text(self, brand_name: str, keywords: List[str]) -> str:
        templates = [
            f"I absolutely love the new product from {brand_name}! It's a game-changer.",
            f"Had a terrible experience with {brand_name}'s customer service. So disappointed and frustrated.",
            f"Just tried {brand_name}'s latest offering. It's okay, nothing special, but gets the job done.",
            f"Highly recommend {brand_name} for their {random.choice(keywords if keywords else ['innovation', 'quality'])}. Truly impressed!",  # nosec B311
            f"Why is {brand_name} always so {random.choice(['expensive', 'slow', 'buggy'])}? Needs improvement.",  # nosec B311
            f"Excited to see what {brand_name} does next with {random.choice(keywords if keywords else ['AI', 'sustainability'])}."  # nosec B311
        ]
        return random.choice(templates)  # nosec B311

class SentimentAnalysisModel:
    """Manages the sentiment analysis model, using a singleton pattern for lazy loading."""
    _classifier = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentimentAnalysisModel, cls).__new__(cls)
        return cls._instance

    def get_classifier(self):
        """Lazily loads the sentiment analysis model on first use."""
        if self._classifier is None:
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for sentiment analysis are not installed. Please install 'transformers' and 'torch'.")
                # Set a marker to prevent repeated load attempts
                self._classifier = "unavailable"
            else:
                try:
                    logger.info("Initializing sentiment analysis model (distilbert-base-uncased-finetuned-sst-2-english)...")
                    # The pipeline will be loaded here, on first actual use
                    self._classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
                    logger.info("Sentiment analysis model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load sentiment analysis model: {e}")
                    self._classifier = "unavailable"
        
        if self._classifier == "unavailable":
            return None
        return self._classifier

    def analyze_sentiment(self, text: str) -> str:
        classifier = self.get_classifier()
        if not classifier:
            return "neutral" # Fallback if model failed to load
        try:
            result = classifier(text)[0]
            label = result['label'].lower()
            # The model typically returns 'positive' or 'negative'. We map to our categories.
            if label == "positive": return "positive"
            if label == "negative": return "negative"
            return "neutral" # Default for other labels or if score is low/unclear
        except Exception as e:
            logger.error(f"Sentiment analysis failed for text '{text[:50]}...': {e}")
            return "neutral"

sentiment_model_instance = SentimentAnalysisModel()
mention_generator = MentionGenerator()

class MonitorBrandMentionsTool(BaseTool):
    """Monitors online platforms for mentions of a specified brand and records new mentions."""
    def __init__(self, tool_name="monitor_brand_mentions"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Monitors online platforms for mentions of a specified brand, optionally filtering by keywords, and records new mentions with sentiment analysis."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "brand_name": {"type": "string", "description": "The name of the brand to monitor."},
                "keywords": {"type": "array", "items": {"type": "string"}, "description": "Optional: Specific keywords to look for within mentions.", "default": []},
                "num_mentions_to_simulate": {"type": "integer", "description": "The number of mock mentions to simulate and record.", "default": 1}
            },
            "required": ["brand_name"]
        }

    def execute(self, brand_name: str, keywords: List[str] = None, num_mentions_to_simulate: int = 1, **kwargs: Any) -> str:
        if keywords is None:
            keywords = []
        
        recorded_mentions = []
        db = next(get_db())
        try:
            for _ in range(num_mentions_to_simulate):
                mention_text = mention_generator.generate_mention_text(brand_name, keywords)
                sentiment = sentiment_model_instance.analyze_sentiment(mention_text)
                source = random.choice(["Twitter", "Facebook", "News Article", "Blog", "Forum"])  # nosec B311
                timestamp = datetime.now().isoformat() + "Z"
                
                new_mention = BrandMention(
                    brand_name=brand_name,
                    text=mention_text,
                    sentiment=sentiment,
                    source=source,
                    timestamp=timestamp
                )
                db.add(new_mention)
                db.flush() # Use flush to get ID before commit if needed, or commit after loop
                recorded_mentions.append({"id": new_mention.id, "text": mention_text, "sentiment": sentiment, "source": source})
            db.commit()
            report = {
                "message": f"Simulated monitoring for '{brand_name}' completed. {len(recorded_mentions)} new mentions recorded.",
                "recorded_mentions": recorded_mentions
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error recording brand mentions: {e}")
            report = {"error": f"Failed to record brand mentions: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class AnalyzeBrandSentimentTool(BaseTool):
    """Analyzes the overall sentiment of collected brand mentions."""
    def __init__(self, tool_name="analyze_brand_sentiment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes the overall sentiment (positive, negative, neutral) of collected brand mentions over a specified period."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "brand_name": {"type": "string", "description": "The name of the brand to analyze sentiment for."},
                "time_period": {"type": "string", "description": "The time period for analysis (e.g., 'last_24_hours', 'last_7_days', 'all_time'). (Currently for documentation only).", "default": "all_time"}
            },
            "required": ["brand_name"]
        }

    def execute(self, brand_name: str, time_period: str = "all_time", **kwargs: Any) -> str:
        db = next(get_db())
        try:
            mentions = db.query(BrandMention).filter(BrandMention.brand_name == brand_name).order_by(BrandMention.timestamp.desc()).all()
            if not mentions:
                return json.dumps({"error": f"No mentions found for brand '{brand_name}'."})
                
            sentiment_counts = Counter(m.sentiment for m in mentions)
            total_mentions = len(mentions)
            
            positive_percent = (sentiment_counts["positive"] / total_mentions) * 100 if total_mentions > 0 else 0
            negative_percent = (sentiment_counts["negative"] / total_mentions) * 100 if total_mentions > 0 else 0
            neutral_percent = (sentiment_counts["neutral"] / total_mentions) * 100 if total_mentions > 0 else 0

            overall_sentiment = "neutral"
            if positive_percent > negative_percent + 10: # If positive is significantly higher
                overall_sentiment = "positive"
            elif negative_percent > positive_percent + 10: # If negative is significantly higher
                overall_sentiment = "negative"
                
            report = {
                "brand_name": brand_name,
                "time_period": time_period,
                "sentiment_summary": {
                    "total_mentions": total_mentions,
                    "positive_mentions": sentiment_counts["positive"],
                    "negative_mentions": sentiment_counts["negative"],
                    "neutral_mentions": sentiment_counts["neutral"],
                    "positive_percent": round(positive_percent, 2),
                    "negative_percent": round(negative_percent, 2),
                    "neutral_percent": round(neutral_percent, 2),
                    "overall_sentiment_assessment": overall_sentiment
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing brand sentiment: {e}")
            report = {"error": f"Failed to analyze brand sentiment: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetBrandMentionDetailsTool(BaseTool):
    """Retrieves all recorded mentions for a specific brand."""
    def __init__(self, tool_name="get_brand_mention_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves all recorded mentions for a specific brand, including their text, sentiment, and source."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"brand_name": {"type": "string", "description": "The name of the brand to retrieve mentions for."}},
            "required": ["brand_name"]
        }

    def execute(self, brand_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            mentions = db.query(BrandMention).filter(BrandMention.brand_name == brand_name).order_by(BrandMention.timestamp.desc()).all()
            if not mentions:
                return json.dumps({"error": f"No mentions found for brand '{brand_name}'."})
            
            mention_list = [{
                "id": m.id,
                "brand_name": m.brand_name,
                "text": m.text,
                "sentiment": m.sentiment,
                "source": m.source,
                "timestamp": m.timestamp
            } for m in mentions]
            report = {
                "brand_name": brand_name,
                "total_mentions": len(mention_list),
                "mentions": mention_list
            }
        except Exception as e:
            logger.error(f"Error getting brand mention details: {e}")
            report = {"error": f"Failed to get brand mention details: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
