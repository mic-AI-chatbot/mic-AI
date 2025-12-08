import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class LogoDesignerTool(BaseTool):
    """
    A creative tool to design text-based logos with various styles and icon suggestions.
    """

    def __init__(self, tool_name: str = "LogoDesigner", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.logos_file = os.path.join(self.data_dir, "generated_logos.json")
        self.logos: Dict[str, Dict[str, Any]] = self._load_data(self.logos_file, default={})
        self.icon_suggestions = {
            "tech": ["<CODE>", "{ }", "[ ]", "</>", "💻", "⚙️"], "nature": ["🌳", "🌸", "☀️", "💧", "🌿", "🦋"],
            "food": ["🍔", "🍕", "🍎", "☕", "🥕", "🍦"], "finance": ["💰", "📈", "📊", "🏦", "💵", "🪙"],
            "creative": ["🎨", "💡", "✨", "🎭", "🖌️", "🎶"], "general": ["⭐", "🚀", "✅", "💡", "👍", "🌐"]
        }

    @property
    def description(self) -> str:
        return "Designs text-based logos with multiple styles and suggests complementary icons."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_text_logo", "suggest_icon", "create_branded_logo", "list_logos", "get_logo_details"]},
                "logo_id": {"type": "string"}, "company_name": {"type": "string"},
                "style": {"type": "string", "default": "boxed", "enum": ["boxed", "banner", "spaced"]},
                "theme": {"type": "string", "default": "general"}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_logos(self):
        with open(self.logos_file, 'w') as f: json.dump(self.logos, f, indent=4)

    def _render_art(self, text: str, style: str) -> str:
        """Renders ASCII art based on a chosen style."""
        width = len(text) + 4
        if style == "boxed":
            return f"{'*' * width}\n* {text} *\n{'*' * width}"
        if style == "banner":
            return f"//{'=' * len(text)}\\\\n|| {text} ||\n\\{'=' * len(text)}// "
        if style == "spaced":
            return " ".join(list(text))
        return text

    def generate_text_logo(self, logo_id: str, company_name: str, style: str = "boxed") -> Dict[str, Any]:
        """Generates a text-based logo with a specified style."""
        if not all([logo_id, company_name]):
            raise ValueError("Logo ID and company name are required.")
        if logo_id in self.logos:
            raise ValueError(f"Logo with ID '{logo_id}' already exists.")

        art = self._render_art(company_name, style)
        new_logo = {
            "logo_id": logo_id, "company_name": company_name, "type": "text_logo",
            "style": style, "art": art, "generated_at": datetime.now().isoformat()
        }
        self.logos[logo_id] = new_logo
        self._save_logos()
        self.logger.info(f"Text logo '{logo_id}' generated for '{company_name}' with style '{style}'.")
        return new_logo

    def suggest_icon(self, theme: str = "general") -> str:
        """Suggests a text-based icon based on a theme."""
        theme_lower = theme.lower()
        if theme_lower not in self.icon_suggestions:
            theme_lower = "general"
        return random.choice(self.icon_suggestions[theme_lower])  # nosec B311

    def create_branded_logo(self, logo_id: str, company_name: str, style: str = "boxed", theme: str = "general") -> Dict[str, Any]:
        """Generates a text logo and combines it with a suggested icon."""
        logo_data = self.generate_text_logo(logo_id, company_name, style)
        icon = self.suggest_icon(theme)
        
        branded_art = f"{icon} {logo_data['art']} {icon}"
        logo_data["branded_art"] = branded_art
        logo_data["icon"] = icon
        
        self.logos[logo_id] = logo_data  # Update logo data with branded art
        self._save_logos()
        self.logger.info(f"Created branded logo for '{logo_id}'.")
        return logo_data

    def list_logos(self, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all generated logos, with optional filtering."""
        filtered = list(self.logos.values())
        if company_name:
            filtered = [logo for logo in filtered if logo.get("company_name") == company_name]
        return filtered

    def get_logo_details(self, logo_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the full details of a specific logo."""
        return self.logos.get(logo_id)

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "generate_text_logo": self.generate_text_logo, "suggest_icon": self.suggest_icon,
            "create_branded_logo": self.create_branded_logo, "list_logos": self.list_logos,
            "get_logo_details": self.get_logo_details
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating LogoDesignerTool functionality...")
    temp_dir = "temp_logo_designer_data"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    designer_tool = LogoDesignerTool(data_dir=temp_dir)
    
    try:
        # --- Generate a logo with a specific style ---
        print("\n--- Generating a 'banner' style logo ---")
        logo1 = designer_tool.execute(
            operation="generate_text_logo", logo_id="acme_banner",
            company_name="Acme Corp", style="banner"
        )
        print(logo1['art'])

        # --- Create a fully branded logo (text + icon) ---
        print("\n--- Creating a branded 'tech' logo ---")
        branded_logo = designer_tool.execute(
            operation="create_branded_logo", logo_id="inno_tech",
            company_name="Innovate Inc.", style="boxed", theme="tech"
        )
        print(branded_logo['branded_art'])
        
        # --- Get just an icon suggestion ---
        print("\n--- Suggesting a 'finance' icon ---")
        icon = designer_tool.execute(operation="suggest_icon", theme="finance")
        print(f"Suggested Icon: {icon}")

        # --- List logos ---
        print("\n--- Listing all logos ---")
        all_logos = designer_tool.execute(operation="list_logos")
        print(f"Found {len(all_logos)} logos.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        import shutil
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")