import logging
import json
import random
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import BiometricUser
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

class EnrollUserBiometricTool(BaseTool):
    """Enrolls a new user with simulated biometric data into the persistent database."""
    def __init__(self, tool_name="enroll_user_biometric"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Enrolls a new user with simulated biometric data (a numerical vector) and a security level into the persistent database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "A unique ID for the user to enroll."},
                "biometric_vector": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Simulated biometric data as a numerical vector (e.g., [0.1, 0.2, 0.3]). Must be a list of numbers."
                },
                "security_level": {"type": "string", "description": "The desired security level for authentication.", "enum": ["low", "medium", "high"], "default": "medium"}
            },
            "required": ["user_id", "biometric_vector"]
        }

    def execute(self, user_id: str, biometric_vector: List[float], security_level: str = "medium", **kwargs: Any) -> str:
        if not isinstance(biometric_vector, list) or not all(isinstance(x, (int, float)) for x in biometric_vector):
            return json.dumps({"error": "biometric_vector must be a list of numbers."})

        db = next(get_db())
        try:
            new_biometric_user = BiometricUser(
                user_id=user_id,
                biometric_vector=json.dumps(biometric_vector),
                security_level=security_level,
                enrollment_date=datetime.now().isoformat() + "Z"
            )
            db.add(new_biometric_user)
            db.commit()
            db.refresh(new_biometric_user)
            report = {"message": f"User '{user_id}' successfully enrolled with biometric data at security level '{security_level}'."}
        except IntegrityError:
            db.rollback()
            report = {"error": f"User '{user_id}' is already enrolled. Use a different user_id or update existing data."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error enrolling user biometric data: {e}")
            report = {"error": f"Failed to enroll user biometric data: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class AuthenticateUserBiometricTool(BaseTool):
    """Authenticates a user by comparing provided biometric data against enrolled data."""
    def __init__(self, tool_name="authenticate_user_biometric"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Authenticates a user by comparing provided biometric data against their enrolled data using a simple matching algorithm and simulated liveness detection."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user to authenticate."},
                "provided_biometric_vector": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "The biometric data provided by the user for authentication."
                }
            },
            "required": ["user_id", "provided_biometric_vector"]
        }

    def execute(self, user_id: str, provided_biometric_vector: List[float], **kwargs: Any) -> str:
        db = next(get_db())
        try:
            enrolled_user_data = db.query(BiometricUser).filter(BiometricUser.user_id == user_id).first()
            if not enrolled_user_data:
                return json.dumps({"authenticated": False, "reason": f"User '{user_id}' not enrolled."})
            
            enrolled_vector = np.array(json.loads(enrolled_user_data.biometric_vector))
            provided_vector = np.array(provided_biometric_vector)

            if len(enrolled_vector) != len(provided_vector):
                return json.dumps({"authenticated": False, "reason": "Provided biometric data has incorrect format/length compared to enrolled data."})

            # Simulate matching using Euclidean distance
            distance = np.linalg.norm(enrolled_vector - provided_vector)
            
            # Threshold for matching (can be adjusted based on security_level)
            match_threshold = 0.5 # Default example threshold
            if enrolled_user_data.security_level == "high":
                match_threshold = 0.2
            elif enrolled_user_data.security_level == "low":
                match_threshold = 0.8

            is_match = distance < match_threshold
            
            # Simulate liveness detection (random chance, higher for high security)
            liveness_passed = random.choice([True, False])  # nosec B311
            if enrolled_user_data.security_level == "high":
                liveness_passed = random.random() < 0.9 # 90% chance to pass liveness for high security  # nosec B311
            elif enrolled_user_data.security_level == "low":
                liveness_passed = random.random() < 0.6 # 60% chance to pass liveness for low security  # nosec B311


            if is_match and liveness_passed:
                return json.dumps({"authenticated": True, "message": f"User '{user_id}' successfully authenticated."})
            else:
                reason = []
                if not is_match:
                    reason.append(f"Biometric data mismatch (distance: {distance:.2f}, threshold: {match_threshold:.2f}).")
                if not liveness_passed:
                    reason.append("Liveness detection failed.")
                return json.dumps({"authenticated": False, "reason": ". ".join(reason)})
        except Exception as e:
            logger.error(f"Error authenticating user biometric data: {e}")
            return json.dumps({"authenticated": False, "reason": f"Failed to authenticate user: {e}"})
        finally:
            db.close()

class GetEnrolledUsersTool(BaseTool):
    """Lists all enrolled users in the biometric authentication system."""
    def __init__(self, tool_name="get_enrolled_users"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all users currently enrolled in the biometric authentication system, showing their user IDs and security levels."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            users = db.query(BiometricUser).order_by(BiometricUser.enrollment_date.desc()).all()
            user_list = [{
                "user_id": u.user_id,
                "security_level": u.security_level,
                "enrollment_date": u.enrollment_date
            } for u in users]
            report = {
                "total_enrolled_users": len(user_list),
                "enrolled_users": user_list
            }
        except Exception as e:
            logger.error(f"Error listing enrolled users: {e}")
            report = {"error": f"Failed to list enrolled users: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
