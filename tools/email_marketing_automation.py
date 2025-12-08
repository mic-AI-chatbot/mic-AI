import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

# Assuming EmailSendingTool is available and functional in the same directory or mic.tools
from .email_sending_tool import EmailSendingTool

logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = "subscribers.json"
EMAIL_CAMPAIGNS_FILE = "email_campaigns.json"

class EmailMarketingManager:
    """
    A tool for simulating email marketing automation.
    It allows for managing subscribers, sending campaigns, generating reports,
    and segmenting audiences. Subscriber data and campaign reports are persisted
    in local JSON files.
    """

    def __init__(self):
        """
        Initializes the EmailMarketingManager.
        Loads existing subscriber data and campaign records or creates new ones.
        """
        self.subscribers: List[str] = self._load_subscribers()
        self.campaigns: Dict[str, Dict[str, Any]] = self._load_campaigns()
        self.email_sender = EmailSendingTool() # Initialize the EmailSendingTool

    def _load_subscribers(self) -> List[str]:
        """Loads subscriber emails from a JSON file."""
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted subscribers file '{SUBSCRIBERS_FILE}'. Starting with empty list.")
                    return []
        return []

    def _save_subscribers(self) -> None:
        """Saves current subscriber emails to a JSON file."""
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(self.subscribers, f, indent=4)

    def _load_campaigns(self) -> Dict[str, Dict[str, Any]]:
        """Loads email campaign data from a JSON file."""
        if os.path.exists(EMAIL_CAMPAIGNS_FILE):
            with open(EMAIL_CAMPAIGNS_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted campaigns file '{EMAIL_CAMPAIGNS_FILE}'. Starting with empty campaigns.")
                    return {}
        return {}

    def _save_campaigns(self) -> None:
        """Saves current email campaign data to a JSON file."""
        with open(EMAIL_CAMPAIGNS_FILE, 'w') as f:
            json.dump(self.campaigns, f, indent=4)

    def add_subscriber(self, email: str) -> Dict[str, Any]:
        """
        Adds an email to the subscriber list.

        Args:
            email: The email address to add.

        Returns:
            A dictionary indicating the result of the operation.
        """
        if not email or "@" not in email:
            raise ValueError("Invalid email address format.")
        if email in self.subscribers:
            return {"status": "info", "message": f"Email '{email}' is already subscribed."}
        
        self.subscribers.append(email)
        self._save_subscribers()
        logger.info(f"Email '{email}' added to subscribers.")
        return {"status": "success", "message": f"Email '{email}' added to subscribers."}

    def remove_subscriber(self, email: str) -> Dict[str, Any]:
        """
        Removes an email from the subscriber list.

        Args:
            email: The email address to remove.

        Returns:
            A dictionary indicating the result of the operation.
        """
        if email not in self.subscribers:
            raise ValueError(f"Email '{email}' not found in subscribers.")
        
        self.subscribers.remove(email)
        self._save_subscribers()
        logger.info(f"Email '{email}' removed from subscribers.")
        return {"status": "success", "message": f"Email '{email}' removed from subscribers."}

    def list_subscribers(self) -> List[str]:
        """
        Lists all subscribed email addresses.

        Returns:
            A list of subscribed email addresses.
        """
        return self.subscribers

    def send_campaign(self, campaign_id: str, subject: str, body: str,
                      sender_email: str, sender_password: str,
                      recipient_emails: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Simulates sending an email marketing campaign to all or a segment of subscribers.

        Args:
            campaign_id: A unique ID for this campaign send.
            subject: The subject of the email.
            body: The body content of the email.
            sender_email: The sender's email address.
            sender_password: The sender's email password (for simulation, not for real use).
            recipient_emails: Optional list of specific emails to send to. If None, sends to all subscribers.

        Returns:
            A dictionary containing the campaign send report.
        """
        if not campaign_id or not subject or not body or not sender_email or not sender_password:
            raise ValueError("Campaign ID, subject, body, sender email, and password cannot be empty.")
        if campaign_id in self.campaigns:
            raise ValueError(f"Campaign with ID '{campaign_id}' already exists.")

        recipients = recipient_emails if recipient_emails is not None else self.subscribers
        if not recipients:
            raise ValueError("No recipients to send the campaign to.")

        sent_count = 0
        failed_count = 0
        for email in recipients:
            try:
                # Use the EmailSendingTool to simulate sending
                self.email_sender.send_email(
                    receiver_email=email,
                    subject=subject,
                    body=body,
                    sender_email=sender_email,
                    sender_password=sender_password
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Simulated: Failed to send email to {email}: {e}")
                failed_count += 1
        
        campaign_report = {
            "campaign_id": campaign_id,
            "subject": subject,
            "sent_at": datetime.now().isoformat(),
            "total_recipients": len(recipients),
            "sent_successfully": sent_count,
            "failed_to_send": failed_count,
            "simulated_opens": random.randint(sent_count // 2, sent_count),  # nosec B311
            "simulated_clicks": random.randint(sent_count // 10, sent_count // 5)  # nosec B311
        }
        self.campaigns[campaign_id] = campaign_report
        self._save_campaigns()
        logger.info(f"Campaign '{campaign_id}' sent. Sent: {sent_count}, Failed: {failed_count}.")
        return campaign_report

    def get_campaign_report(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a simulated report on campaign performance.

        Args:
            campaign_id: The ID of the campaign to retrieve the report for.

        Returns:
            A dictionary containing the campaign report, or None if not found.
        """
        return self.campaigns.get(campaign_id)

    def segment_audience(self, segment_id: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates segmenting the audience based on criteria.

        Args:
            segment_id: A unique ID for the audience segment.
            criteria: A dictionary defining the segmentation criteria (e.g., {"age_group": "18-25", "location": "USA"}).

        Returns:
            A dictionary containing the details of the simulated audience segment.
        """
        if not segment_id or not criteria:
            raise ValueError("Segment ID and criteria cannot be empty.")
        
        # Simulate segmentation - for now, just return a random subset of subscribers
        num_segment_members = random.randint(1, len(self.subscribers)) if self.subscribers else 0  # nosec B311
        segment_members = random.sample(self.subscribers, num_segment_members) if num_segment_members > 0 else []  # nosec B311

        segment_details = {
            "segment_id": segment_id,
            "criteria": criteria,
            "members": segment_members,
            "member_count": len(segment_members),
            "generated_at": datetime.now().isoformat()
        }
        logger.info(f"Audience segment '{segment_id}' generated with {len(segment_members)} members.")
        return segment_details

# Example usage (for direct script execution)
if __name__ == '__main__':
    print("Demonstrating EmailMarketingManager functionality...")

    manager = EmailMarketingManager()

    # Clean up previous state for a fresh demo
    if os.path.exists(SUBSCRIBERS_FILE):
        os.remove(SUBSCRIBERS_FILE)
    if os.path.exists(EMAIL_CAMPAIGNS_FILE):
        os.remove(EMAIL_CAMPAIGNS_FILE)
    manager = EmailMarketingManager() # Re-initialize to clear loaded state
    print(f"\nCleaned up state files for fresh demo.")

    # --- Add Subscribers ---
    print("\n--- Adding Subscribers ---")
    try:
        manager.add_subscriber("alice@example.com")
        manager.add_subscriber("bob@example.com")
        manager.add_subscriber("charlie@example.com")
    except Exception as e:
        print(f"Add subscriber failed: {e}")

    # --- List Subscribers ---
    print("\n--- Listing All Subscribers ---")
    all_subscribers = manager.list_subscribers()
    print(json.dumps(all_subscribers, indent=2))

    # --- Segment Audience ---
    print("\n--- Segmenting Audience 'young_tech_enthusiasts' ---")
    segment = manager.segment_audience("young_tech_enthusiasts", {"age_group": "18-25", "interests": "tech"})
    print(json.dumps(segment, indent=2))

    # --- Send Campaign ---
    print("\n--- Sending Campaign 'welcome_series_001' ---")
    try:
        # Note: This will attempt to use the EmailSendingTool, which might require SMTP setup.
        # For a purely simulated environment, ensure EmailSendingTool is mocked or configured not to send real emails.
        campaign_report = manager.send_campaign(
            campaign_id="welcome_series_001",
            subject="Welcome to Our Newsletter!",
            body="Thank you for subscribing. Here's your first email.",
            sender_email="simulated@example.com",
            sender_password="YOUR_SIMULATED_PASSWORD" # Placeholder password for demonstration. Do not use real credentials.
        )
        print(json.dumps(campaign_report, indent=2))
    except Exception as e:
        print(f"Send campaign failed: {e}")

    # --- Get Campaign Report ---
    if campaign_report:
        print(f"\n--- Getting Report for '{campaign_report['campaign_id']}' ---")
        report_details = manager.get_campaign_report(campaign_report['campaign_id'])
        print(json.dumps(report_details, indent=2))

    # --- Remove Subscriber ---
    print("\n--- Removing 'bob@example.com' ---")
    try:
        manager.remove_subscriber("bob@example.com")
    except Exception as e:
        print(f"Remove subscriber failed: {e}")

    # Clean up
    if os.path.exists(SUBSCRIBERS_FILE):
        os.remove(SUBSCRIBERS_FILE)
    if os.path.exists(EMAIL_CAMPAIGNS_FILE):
        os.remove(EMAIL_CAMPAIGNS_FILE)
    print(f"\nCleaned up state files.")