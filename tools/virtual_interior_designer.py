import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class VirtualInteriorDesignerTool(BaseTool):
    """
    An advanced tool for virtual interior design, offering style suggestions and complementary color palettes.
    """

    def __init__(self, tool_name: str = "virtual_interior_designer_tool"):
        super().__init__(tool_name)
        self.styles = {
            "living room": ["Minimalist", "Bohemian", "Modern Farmhouse", "Industrial", "Scandinavian"],
            "bedroom": ["Scandinavian", "Coastal", "Industrial", "Bohemian", "Minimalist"],
            "kitchen": ["Traditional", "Contemporary", "Rustic", "Modern Farmhouse", "Industrial"],
            "bathroom": ["Spa-like", "Modern", "Classic", "Industrial"],
            "dining room": ["Formal", "Casual", "Transitional", "Rustic"]
        }
        self.color_palettes = {
            "Minimalist": ["#F5F5DC", "#FFFFFF", "#A9A9A9", "#000000"], # Beige, White, Dark Gray, Black
            "Bohemian": ["#D2B48C", "#F0E68C", "#8B4513", "#228B22", "#FFD700"], # Tan, Khaki, SaddleBrown, ForestGreen, Gold
            "Modern Farmhouse": ["#F5DEB3", "#FFFFFF", "#8B4513", "#696969"], # Wheat, White, SaddleBrown, DimGray
            "Scandinavian": ["#F8F8F8", "#D3D3D3", "#A9A9A9", "#5F9EA0"], # WhiteSmoke, LightGray, DarkGray, CadetBlue
            "Coastal": ["#ADD8E6", "#F0F8FF", "#87CEEB", "#4682B4"], # LightBlue, AliceBlue, SkyBlue, SteelBlue
            "Industrial": ["#696969", "#A9A9A9", "#C0C0C0", "#000000"], # DimGray, DarkGray, Silver, Black
            "Traditional": ["#8B0000", "#DAA520", "#D2B48C", "#556B2F"], # DarkRed, Goldenrod, Tan, OliveDrab
            "Contemporary": ["#2F4F4F", "#DCDCDC", "#6A5ACD", "#FF6347"], # DarkSlateGray, Gainsboro, SlateBlue, Tomato
            "Rustic": ["#8B4513", "#D2B48C", "#A0522D", "#6B8E23"], # SaddleBrown, Tan, Sienna, OliveDrab
            "Spa-like": ["#E0FFFF", "#AFEEEE", "#B0E0E6", "#ADD8E6"], # LightCyan, PaleTurquoise, PowderBlue, LightBlue
            "Classic": ["#F5DEB3", "#D2B48C", "#8B4513", "#696969"], # Wheat, Tan, SaddleBrown, DimGray
            "Formal": ["#4682B4", "#DCDCDC", "#808080", "#000000"], # SteelBlue, Gainsboro, Gray, Black
            "Casual": ["#F0F8FF", "#ADD8E6", "#FFD700", "#228B22"], # AliceBlue, LightBlue, Gold, ForestGreen
            "Transitional": ["#D3D3D3", "#A9A9A9", "#696969", "#2F4F4F"] # LightGray, DarkGray, DimGray, DarkSlateGray
        }

    @property
    def description(self) -> str:
        return "Suggests a design style and color palette for a specified room."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "room_type": {
                    "type": "string",
                    "description": f"The type of room to design. Supported: {list(self.styles.keys())}"
                }
            },
            "required": ["room_type"]
        }

    def execute(self, room_type: str, **kwargs: Any) -> Dict:
        """
        Suggests a design style and color palette for a room.
        """
        try:
            room_lower = room_type.lower()
            if room_lower not in self.styles:
                raise ValueError(f"Room type '{room_type}' not supported. Try one of: {list(self.styles.keys())}")

            # Suggest a style
            suggested_style = random.choice(self.styles[room_lower])  # nosec B311
            
            # Generate the color palette for that style
            palette = self.color_palettes.get(suggested_style, [])

            return {
                "message": "Design suggestion generated successfully.",
                "room_type": room_type,
                "suggested_style": suggested_style,
                "color_palette_hex": palette
            }

        except Exception as e:
            logger.error(f"An error occurred in VirtualInteriorDesignerTool: {e}")
            return {"error": str(e)}
