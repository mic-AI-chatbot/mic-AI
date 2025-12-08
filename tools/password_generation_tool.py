
import logging
import secrets
import string
import json
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PasswordGenerationTool(BaseTool):
    """
    A tool for generating strong, random passwords with configurable length
    and character sets.
    """

    def __init__(self, tool_name: str = "PasswordGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates strong, random passwords with configurable length and character sets."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "length": {"type": "integer", "minimum": 8, "default": 16, "description": "The desired length of the password."},
                "include_digits": {"type": "boolean", "default": True, "description": "Whether to include digits (0-9)."},
                "include_symbols": {"type": "boolean", "default": True, "description": "Whether to include symbols (!@#$%^&*)."},
                "include_uppercase": {"type": "boolean", "default": True, "description": "Whether to include uppercase letters (A-Z)."},
                "include_lowercase": {"type": "boolean", "default": True, "description": "Whether to include lowercase letters (a-z)."}
            },
            "required": []
        }

    def execute(self, length: int = 16, include_digits: bool = True, include_symbols: bool = True, include_uppercase: bool = True, include_lowercase: bool = True) -> Dict[str, Any]:
        """
        Generates a strong, random password with configurable length and character sets.
        """
        if length < 8:
            return {"status": "error", "message": "Password length should be at least 8 characters."}

        characters = ""
        if include_digits:
            characters += string.digits
        if include_symbols:
            characters += string.punctuation
        if include_uppercase:
            characters += string.ascii_uppercase
        if include_lowercase:
            characters += string.ascii_lowercase

        if not characters:
            return {"status": "error", "message": "At least one character type (digits, symbols, uppercase, lowercase) must be selected."}

        try:
            password = ''.join(secrets.choice(characters) for _ in range(length))
            return {"status": "success", "generated_password": password, "length": length}
        except Exception as e:
            logger.error(f"An error occurred during password generation: {e}")
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}

if __name__ == '__main__':
    print("Demonstrating PasswordGenerationTool functionality...")
    
    password_generator = PasswordGenerationTool()
    
    try:
        # 1. Generate a password with default settings
        print("\n--- Generating password with default settings (length 16, all types) ---")
        result1 = password_generator.execute()
        print(json.dumps(result1, indent=2))

        # 2. Generate a password with specific criteria (e.g., 12 chars, no symbols)
        print("\n--- Generating password (length 12, no symbols) ---")
        result2 = password_generator.execute(length=12, include_symbols=False)
        print(json.dumps(result2, indent=2))

        # 3. Generate a password with only uppercase letters
        print("\n--- Generating password (length 10, only uppercase) ---")
        result3 = password_generator.execute(length=10, include_digits=False, include_symbols=False, include_lowercase=False)
        print(json.dumps(result3, indent=2))

        # 4. Attempt to generate a too-short password
        print("\n--- Attempting to generate a too-short password (length 5) ---")
        result4 = password_generator.execute(length=5)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
