import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import ChatbotIntegration
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class IntegrateChatbotTool(BaseTool):
    """Integrates a chatbot with a messaging platform and stores details in a persistent database."""
    def __init__(self, tool_name="integrate_chatbot"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Integrates a chatbot with a messaging platform (e.g., 'Slack', 'Microsoft Teams') using an API key and webhook URL, storing integration details persistently."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "platform_name": {"type": "string", "description": "The name of the platform to integrate with (e.g., 'Slack', 'Microsoft Teams')."},
                "api_key": {"type": "string", "description": "The API key for the platform integration."},
                "webhook_url": {"type": "string", "description": "The webhook URL for receiving messages from the platform."}
            },
            "required": ["platform_name", "api_key", "webhook_url"]
        }

    def execute(self, platform_name: str, api_key: str, webhook_url: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            now = datetime.now().isoformat() + "Z"
            new_integration = ChatbotIntegration(
                platform_name=platform_name,
                api_key=api_key,
                webhook_url=webhook_url,
                status="active",
                integrated_at=now
            )
            db.add(new_integration)
            db.commit()
            db.refresh(new_integration)
            report = {"message": f"Chatbot successfully integrated with '{platform_name}'. Status: active."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"Chatbot is already integrated with '{platform_name}'. Use a different platform name or update existing integration."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error integrating chatbot: {e}")
            report = {"error": f"Failed to integrate chatbot: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class SendChatbotMessageTool(BaseTool):
    """Simulates sending a message through a chatbot integration."""
    def __init__(self, tool_name="send_chatbot_message"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates sending a message to a specified channel or user through an integrated chatbot, logging the message and its destination."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "platform_name": {"type": "string", "description": "The name of the platform the chatbot is integrated with."},
                "channel_or_user": {"type": "string", "description": "The channel ID or user ID to send the message to."},
                "message_text": {"type": "string", "description": "The text content of the message to send."}
            },
            "required": ["platform_name", "channel_or_user", "message_text"]
        }

    def execute(self, platform_name: str, channel_or_user: str, message_text: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            integration = db.query(ChatbotIntegration).filter(ChatbotIntegration.platform_name == platform_name).first()
            if not integration:
                return json.dumps({"error": f"Chatbot not integrated with '{platform_name}'. Please integrate it first."})
                
            # Simulate sending message by logging it
            logger.info(f"Simulated message sent via {platform_name} to {channel_or_user}: {message_text}")
            
            report = {
                "message": f"Simulated message sent to '{channel_or_user}' on '{platform_name}' via chatbot.",
                "sent_message": message_text,
                "destination": channel_or_user,
                "platform": platform_name,
                "integration_status": integration.status
            }
        except Exception as e:
            logger.error(f"Error sending chatbot message: {e}")
            report = {"error": f"Failed to send chatbot message: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class ListChatbotIntegrationsTool(BaseTool):
    """Lists all active chatbot integrations."""
    def __init__(self, tool_name="list_chatbot_integrations"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all active chatbot integrations, showing the platform name and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            integrations = db.query(ChatbotIntegration).order_by(ChatbotIntegration.integrated_at.desc()).all()
            integration_list = [{
                "platform_name": i.platform_name,
                "status": i.status,
                "integrated_at": i.integrated_at
            } for i in integrations]
            report = {
                "total_integrations": len(integration_list),
                "integrations": integration_list
            }
        except Exception as e:
            logger.error(f"Error listing chatbot integrations: {e}")
            report = {"error": f"Failed to list chatbot integrations: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
