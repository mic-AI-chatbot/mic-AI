import bcrypt
import re
import html
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .models import User
from .config import SUBSCRIPTION_TIERS

def hash_password(password: str) -> bytes:
    """Hashes a password using bcrypt."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt)

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verifies a password against a bcrypt hash."""
    password_byte_enc = plain_password.encode('utf-8')
    if isinstance(hashed_password, memoryview):
        hashed_password = hashed_password.tobytes()
    return bcrypt.checkpw(password_byte_enc, hashed_password)

def register_user(db: Session, username: str, password: str, email: str, age: int, location: str) -> bool:
    """Registers a new user with basic input validation and secure password hashing."""
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        print("Invalid email format.")
        return False
    if not (0 < age < 120):
        print("Invalid age. Age must be between 1 and 119.")
        return False

    safe_username = html.escape(username)
    safe_email = html.escape(email)
    safe_location = html.escape(location)

    hashed_password = hash_password(password)
    new_user = User(
        username=safe_username,
        password=hashed_password,
        email=safe_email,
        age=age,
        location=safe_location
    )
    db.add(new_user)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        print(f"Username '{username}' or email '{email}' already exists.")
        return False

def verify_user(db: Session, username: str, password: str) -> bool:
    """Verifies user credentials using secure password hashing."""
    user = db.query(User).filter(User.username == username).first()
    if user and user.password:
        return verify_password(password, user.password)
    return False

def get_user_tier(db: Session, username: str) -> str:
    """Gets the subscription tier of a user."""
    user = db.query(User).filter(User.username == username).first()
    return user.subscription_tier if user else None

def update_user_tier(db: Session, username: str, new_tier: str) -> bool:
    """Updates the subscription tier of a user."""
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.subscription_tier = new_tier
        db.commit()
        return True
    return False

def get_user_status(db: Session, username: str) -> Dict[str, Any]:
    """Retrieves the user's subscription tier and usage limits."""
    user = db.query(User).filter(User.username == username).first()
    if user:
        return {
            "username": user.username,
            "subscription_tier": user.subscription_tier,
            "llm_queries_left": user.llm_queries_left,
            "web_searches_left": user.web_searches_left,
            "file_processing_left": user.file_processing_left
        }
    return {}

def has_tool_permission(db: Session, username: str, tool_name: str) -> bool:
    """Checks if a user has permission to use a specific tool."""
    tier = get_user_tier(db, username)
    if not tier:
        return False

    allowed_tools = SUBSCRIPTION_TIERS.get(tier, {}).get("allowed_tools", [])

    if "*" in allowed_tools:
        return True

    return tool_name in allowed_tools
