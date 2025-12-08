import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class NegotiationSession:
    """Represents a single negotiation session with parties, topic, offers, and status."""
    def __init__(self, session_id: str, parties: List[str], topic: str, initial_offers: Dict[str, Any], reservation_values: Dict[str, Any]):
        self.session_id = session_id
        self.parties = parties
        self.topic = topic
        self.initial_offers = initial_offers
        self.reservation_values = reservation_values
        self.status = "in_progress" # in_progress, concluded_agreement, concluded_no_agreement
        self.offers_history: List[Dict[str, Any]] = []
        self.current_offer: Dict[str, Any] = {}

    def record_offer(self, party_name: str, offer_details: Dict[str, Any]):
        self.offers_history.append({"party": party_name, "offer": offer_details, "timestamp": datetime.now().isoformat()})
        self.current_offer = {"party": party_name, "offer": offer_details}

    def evaluate_offer(self, offer_details: Dict[str, Any], offering_party: str, responding_party: str) -> Dict[str, Any]:
        """Simulates an AI agent evaluating an offer based on reservation values."""
        # This is a simplified evaluation for a single numerical 'price' topic.
        # Real negotiation agents would use more complex utility functions.
        if self.topic == "price":
            offered_price = offer_details.get("price")
            if offered_price is None:
                return {"decision": "reject", "reason": "Offer missing 'price' detail."}

            responding_party_res_value = self.reservation_values.get(responding_party, {}).get("price")
            offering_party_res_value = self.reservation_values.get(offering_party, {}).get("price")

            if responding_party_res_value is None or offering_party_res_value is None:
                return {"decision": "counter", "reason": "Missing reservation values for comparison. Suggesting counter."}

            # Logic for buyer (lower price is better) vs. seller (higher price is better)
            # Assuming parties[0] is the buyer and parties[1] is the seller for simplicity
            if offering_party == self.parties[0]: # Buyer is offering
                # Responding party (seller) evaluates buyer's offer
                if offered_price >= responding_party_res_value: # Buyer's offer meets or exceeds seller's reservation
                    return {"decision": "accept", "reason": "Offer meets or exceeds reservation value."}
                elif offered_price < responding_party_res_value and offered_price > offering_party_res_value:
                    # Offer is below seller's reservation but above buyer's own reservation
                    counter_price = offered_price + random.uniform(50, 200) # Seller counters higher  # nosec B311
                    return {"decision": "counter", "counter_offer": {"price": round(counter_price, 2)}, "reason": "Offer too low, but within negotiation range. Suggesting counter."}
                else:
                    return {"decision": "reject", "reason": "Offer too far from reservation value."}
            else: # Seller is offering
                # Responding party (buyer) evaluates seller's offer
                if offered_price <= responding_party_res_value: # Seller's offer meets or is below buyer's reservation
                    return {"decision": "accept", "reason": "Offer meets or is below reservation value."}
                elif offered_price > responding_party_res_value and offered_price < offering_party_res_value:
                    # Offer is above buyer's reservation but below seller's own reservation
                    counter_price = offered_price - random.uniform(50, 200) # Buyer counters lower  # nosec B311
                    return {"decision": "counter", "counter_offer": {"price": round(counter_price, 2)}, "reason": "Offer too high, but within negotiation range. Suggesting counter."}
                else:
                    return {"decision": "reject", "reason": "Offer too far from reservation value."}
        
        return {"decision": "counter", "reason": "Complex topic or non-numerical, suggesting a counter-offer for further discussion."}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "parties": self.parties,
            "topic": self.topic,
            "status": self.status,
            "initial_offers": self.initial_offers,
            "reservation_values": self.reservation_values,
            "current_offer": self.current_offer,
            "offers_history_count": len(self.offers_history)
        }

class NegotiationManager:
    """Manages all active and historical negotiation sessions, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NegotiationManager, cls).__new__(cls)
            cls._instance.sessions: Dict[str, NegotiationSession] = {}
        return cls._instance

    def create_session(self, session_id: str, parties: List[str], topic: str, initial_offers: Dict[str, Any], reservation_values: Dict[str, Any]) -> NegotiationSession:
        session = NegotiationSession(session_id, parties, topic, initial_offers, reservation_values)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> NegotiationSession:
        return self.sessions.get(session_id)

negotiation_manager = NegotiationManager()

class StartNegotiationTool(BaseTool):
    """Starts a new negotiation session with defined parameters."""
    def __init__(self, tool_name="start_negotiation"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Starts a new negotiation session between specified parties on a given topic, with initial offers and reservation values."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "A unique identifier for the negotiation session."},
                "parties": {"type": "array", "items": {"type": "string"}, "description": "A list of participants in the negotiation (e.g., ['Buyer', 'Seller'])."},
                "topic": {"type": "string", "description": "The topic or subject of the negotiation (e.g., 'price', 'contract_terms')."},
                "initial_offers": {"type": "object", "description": "Initial offer from each party (e.g., {'Buyer': {'price': 800}, 'Seller': {'price': 1200}})."},
                "reservation_values": {"type": "object", "description": "Reservation value for each party (e.g., {'Buyer': {'price': 1000}, 'Seller': {'price': 900}}). This is the worst acceptable outcome."}
            },
            "required": ["session_id", "parties", "topic", "initial_offers", "reservation_values"]
        }

    def execute(self, session_id: str, parties: List[str], topic: str, initial_offers: Dict[str, Any], reservation_values: Dict[str, Any], **kwargs: Any) -> str:
        if session_id in negotiation_manager.sessions:
            return json.dumps({"error": f"Negotiation session '{session_id}' already exists."})
        
        session = negotiation_manager.create_session(session_id, parties, topic, initial_offers, reservation_values)
        
        report = {
            "message": f"Negotiation session '{session_id}' started.",
            "session_details": session.to_dict()
        }
        return json.dumps(report, indent=2)

class MakeNegotiationOfferTool(BaseTool):
    """Makes an offer in a negotiation session and gets a simulated response."""
    def __init__(self, tool_name="make_negotiation_offer"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Makes an offer in an ongoing negotiation session and receives a simulated response (accept, reject, or counter-offer) from the other party."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The ID of the negotiation session."},
                "offering_party": {"type": "string", "description": "The name of the party making the offer."},
                "offer_details": {"type": "object", "description": "A dictionary detailing the offer (e.g., {'price': 1000})."}
            },
            "required": ["session_id", "offering_party", "offer_details"]
        }

    def execute(self, session_id: str, offering_party: str, offer_details: Dict[str, Any], **kwargs: Any) -> str:
        session = negotiation_manager.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Negotiation session '{session_id}' not found."})
        if session.status != "in_progress":
            return json.dumps({"error": f"Negotiation session '{session_id}' is not in progress. Current status: {session.status}."})
        if offering_party not in session.parties:
            return json.dumps({"error": f"Party '{offering_party}' is not part of session '{session_id}'."})

        session.record_offer(offering_party, offer_details)
        
        # Determine the responding party
        responding_party = [p for p in session.parties if p != offering_party][0]
        
        evaluation = session.evaluate_offer(offer_details, offering_party, responding_party)
        
        report = {
            "message": f"Offer made by '{offering_party}'.",
            "offer": offer_details,
            "response_from": responding_party,
            "evaluation": evaluation
        }
        if evaluation.get("decision") == "accept":
            session.status = "concluded_agreement"
            report["message"] += " Offer accepted! Negotiation concluded with agreement."
        elif evaluation.get("decision") == "reject":
            report["message"] += " Offer rejected."
        elif evaluation.get("decision") == "counter":
            report["message"] += " Counter-offer suggested."

        return json.dumps(report, indent=2)

class GetNegotiationStatusTool(BaseTool):
    """Retrieves the current status and history of a negotiation session."""
    def __init__(self, tool_name="get_negotiation_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status, last offer, and a summary of the negotiation history for a specified session."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"session_id": {"type": "string", "description": "The ID of the negotiation session."}},
            "required": ["session_id"]
        }

    def execute(self, session_id: str, **kwargs: Any) -> str:
        session = negotiation_manager.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Negotiation session '{session_id}' not found."})
        
        report = {
            "session_details": session.to_dict(),
            "last_offer": session.current_offer,
            "full_history_count": len(session.offers_history)
        }
        return json.dumps(report, indent=2)

class ConcludeNegotiationTool(BaseTool):
    """Concludes a negotiation session."""
    def __init__(self, tool_name="conclude_negotiation"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Concludes a negotiation session, marking it as either agreed or no agreement."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "The ID of the negotiation session."},
                "agreement_reached": {"type": "boolean", "description": "True if an agreement was reached, False otherwise."}
            },
            "required": ["session_id", "agreement_reached"]
        }

    def execute(self, session_id: str, agreement_reached: bool, **kwargs: Any) -> str:
        session = negotiation_manager.get_session(session_id)
        if not session:
            return json.dumps({"error": f"Negotiation session '{session_id}' not found."})
        
        if agreement_reached:
            session.status = "concluded_agreement"
            message = "Negotiation concluded with an agreement."
        else:
            session.status = "concluded_no_agreement"
            message = "Negotiation concluded with no agreement reached."
        
        report = {
            "message": message,
            "session_details": session.to_dict()
        }
        return json.dumps(report, indent=2)