import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DonorRelationshipManagerTool(BaseTool):
    """
    A tool for simulating donor relationship management.
    """

    def __init__(self, tool_name: str = "donor_relationship_manager"):
        super().__init__(tool_name)
        self.donors_file = "donors.json"
        self.donations_file = "donations.json"
        self.donors: Dict[str, Dict[str, Any]] = self._load_donors()
        self.donations: List[Dict[str, Any]] = self._load_donations()

    @property
    def description(self) -> str:
        return "Manages donor profiles, records donations, and generates reports for donor relationship management."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The donor management operation to perform.",
                    "enum": ["add_donor", "record_donation", "generate_donor_report", "list_donors", "get_donor_details"]
                },
                "donor_id": {"type": "string"},
                "name": {"type": "string"},
                "contact_info": {"type": "object"},
                "preferences": {"type": "object"},
                "amount": {"type": "number", "minimum": 0.01},
                "campaign": {"type": "string"},
                "report_type": {"type": "string", "enum": ["summary", "top_donors"]}
            },
            "required": ["operation"]
        }

    def _load_donors(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.donors_file):
            with open(self.donors_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted donors file '{self.donors_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_donors(self) -> None:
        with open(self.donors_file, 'w') as f:
            json.dump(self.donors, f, indent=4)

    def _load_donations(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.donations_file):
            with open(self.donations_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted donations file '{self.donations_file}'. Starting fresh.")
                    return []
        return []

    def _save_donations(self) -> None:
        with open(self.donations_file, 'w') as f:
            json.dump(self.donations, f, indent=4)

    def _add_donor(self, donor_id: str, name: str, contact_info: Dict[str, Any], preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not all([donor_id, name, contact_info]):
            raise ValueError("Donor ID, name, and contact info cannot be empty.")
        if donor_id in self.donors: raise ValueError(f"Donor '{donor_id}' already exists.")

        new_donor = {
            "donor_id": donor_id, "name": name, "contact_info": contact_info,
            "preferences": preferences or {}, "registered_at": datetime.now().isoformat(),
            "total_donations": 0.0
        }
        self.donors[donor_id] = new_donor
        self._save_donors()
        return new_donor

    def _record_donation(self, donor_id: str, amount: float, campaign: Optional[str] = None) -> Dict[str, Any]:
        donor = self.donors.get(donor_id)
        if not donor: raise ValueError(f"Donor '{donor_id}' not found. Please add the donor first.")
        if amount <= 0: raise ValueError("Donation amount must be positive.")

        donation_id = f"DON-{donor_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_donation = {
            "donation_id": donation_id, "donor_id": donor_id, "amount": amount,
            "campaign": campaign, "donated_at": datetime.now().isoformat()
        }
        self.donations.append(new_donation)
        donor["total_donations"] = donor.get("total_donations", 0.0) + amount
        self._save_donors()
        self._save_donations()
        return new_donation

    def _generate_donor_report(self, report_type: str = "summary") -> Dict[str, Any]:
        if report_type not in ["summary", "top_donors"]: raise ValueError(f"Unsupported report type: '{report_type}'.")

        report_data: Dict[str, Any] = {
            "report_id": f"DONOR_REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "report_type": report_type, "generated_at": datetime.now().isoformat()
        }

        if report_type == "summary":
            total_donors = len(self.donors)
            total_donations_amount = sum(d["amount"] for d in self.donations)
            total_donations_count = len(self.donations)
            report_data.update({
                "total_donors": total_donors, "total_donations_amount": total_donations_amount,
                "total_donations_count": total_donations_count
            })
        elif report_type == "top_donors":
            sorted_donors = sorted(self.donors.values(), key=lambda d: d.get("total_donations", 0.0), reverse=True)
            top_5_donors = sorted_donors[:5]
            report_data["top_donors"] = [{k: v for k, v in d.items() if k != "contact_info"} for d in top_5_donors]
        
        return report_data

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_donor":
            return self._add_donor(kwargs.get("donor_id"), kwargs.get("name"), kwargs.get("contact_info"), kwargs.get("preferences"))
        elif operation == "record_donation":
            return self._record_donation(kwargs.get("donor_id"), kwargs.get("amount"), kwargs.get("campaign"))
        elif operation == "generate_donor_report":
            return self._generate_donor_report(kwargs.get("report_type", "summary"))
        elif operation == "list_donors":
            return list(self.donors.values())
        elif operation == "get_donor_details":
            return self.donors.get(kwargs.get("donor_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DonorRelationshipManagerTool functionality...")
    tool = DonorRelationshipManagerTool()
    
    try:
        print("\n--- Adding Donor ---")
        tool.execute(operation="add_donor", donor_id="donor_alice", name="Alice Wonderland", contact_info={"email": "alice@example.com"})
        
        print("\n--- Recording Donation ---")
        tool.execute(operation="record_donation", donor_id="donor_alice", amount=100.0, campaign="Annual Fund")

        print("\n--- Generating Donor Report ---")
        report = tool.execute(operation="generate_donor_report", report_type="summary")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.donors_file): os.remove(tool.donors_file)
        if os.path.exists(tool.donations_file): os.remove(tool.donations_file)
        print("\nCleanup complete.")
