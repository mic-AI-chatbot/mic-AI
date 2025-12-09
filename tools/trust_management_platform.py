import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated trust scores
trust_scores: Dict[str, Dict[str, Any]] = {}

class TrustManagementPlatformTool(BaseTool):
    """
    A tool to simulate a trust management platform for digital entities.
    """
    def __init__(self, tool_name: str = "trust_management_platform_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates a trust platform: assessing, updating, and reporting on entity trust scores."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform: 'assess', 'update_score', 'get_report', 'list_entities'."
                },
                "entity_id": {"type": "string", "description": "The unique ID of the entity (e.g., user ID, device ID)."},
                "interaction_context": {
                    "type": "string",
                    "description": "Context of a new interaction for assessment (e.g., 'successful_transaction', 'failed_login', 'data_sharing_violation')."
                },
                "manual_score": {
                    "type": "number",
                    "description": "A new score to manually set (0.0 to 1.0) for the 'update_score' action."
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            entity_id = kwargs.get("entity_id")

            if action in ['assess', 'update_score', 'get_report'] and not entity_id:
                raise ValueError(f"'entity_id' is required for the '{action}' action.")

            actions = {
                "assess": self._assess_trust,
                "update_score": self._update_trust_score,
                "get_report": self._get_trust_report,
                "list_entities": self._list_entities,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](entity_id=entity_id, **kwargs)

        except Exception as e:
            logger.error(f"An error occurred in TrustManagementPlatformTool: {e}")
            return {"error": str(e)}

    def _initialize_entity(self, entity_id: str):
        """Creates a new entity with a baseline score if it doesn't exist."""
        if entity_id not in trust_scores:
            trust_scores[entity_id] = {
                "score": round(random.uniform(0.4, 0.6), 2),  # nosec B311
                "level": "neutral",
                "history": [],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            logger.info(f"Initialized new entity '{entity_id}' with a baseline trust score.")

    def _assess_trust(self, entity_id: str, interaction_context: str, **kwargs) -> Dict:
        if not interaction_context:
            raise ValueError("'interaction_context' is required for assessment.")
            
        self._initialize_entity(entity_id)
        entity = trust_scores[entity_id]
        current_score = entity["score"]

        # Simulate score adjustment based on context
        adjustments = {
            "successful_transaction": 0.05,
            "positive_review": 0.03,
            "failed_login": -0.1,
            "data_sharing_violation": -0.5,
            "suspicious_activity": -0.2
        }
        adjustment = adjustments.get(interaction_context, 0)
        new_score = max(0.0, min(1.0, current_score + adjustment))
        
        entity["score"] = round(new_score, 2)
        entity["history"].append({
            "context": interaction_context,
            "adjustment": adjustment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._update_trust_level(entity)

        return {"message": "Trust assessment complete.", "entity_id": entity_id, "new_score": entity["score"], "new_level": entity["level"]}

    def _update_trust_score(self, entity_id: str, manual_score: float, **kwargs) -> Dict:
        if manual_score is None or not (0.0 <= manual_score <= 1.0):
            raise ValueError("'manual_score' must be a float between 0.0 and 1.0.")
        
        self._initialize_entity(entity_id)
        entity = trust_scores[entity_id]
        entity["score"] = round(manual_score, 2)
        entity["history"].append({
            "context": "manual_override",
            "adjustment": f"Set to {manual_score}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._update_trust_level(entity)
        
        return {"message": "Trust score manually updated.", "entity_id": entity_id, "new_score": entity["score"], "new_level": entity["level"]}

    def _get_trust_report(self, entity_id: str, **kwargs) -> Dict:
        if entity_id not in trust_scores:
            return {"error": f"Entity '{entity_id}' not found."}
        return {"trust_report": trust_scores[entity_id]}

    def _list_entities(self, **kwargs) -> Dict:
        if not trust_scores:
            return {"message": "No entities are being tracked."}
        
        summary = {
            entity_id: {
                "score": data["score"],
                "level": data["level"]
            } for entity_id, data in trust_scores.items()
        }
        return {"tracked_entities": summary}

    def _update_trust_level(self, entity: Dict[str, Any]):
        """Updates the qualitative trust level based on the numerical score."""
        score = entity["score"]
        if score >= 0.8:
            entity["level"] = "trusted"
        elif score >= 0.6:
            entity["level"] = "reliable"
        elif score >= 0.4:
            entity["level"] = "neutral"
        elif score >= 0.2:
            entity["level"] = "unreliable"
        else:
            entity["level"] = "distrusted"
        entity["last_updated"] = datetime.now(timezone.utc).isoformat()