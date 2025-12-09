import logging
import json
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class UnitConverterTool(BaseTool):
    """
    A tool for converting values between different units of measurement.
    """

    def __init__(self, tool_name: str = "unit_converter_tool"):
        super().__init__(tool_name)
        # A comprehensive dictionary of conversion factors
        self.conversion_factors = {
            "length": {
                "meters": {"feet": 3.28084, "inches": 39.3701, "centimeters": 100, "kilometers": 0.001, "miles": 0.000621371},
                "feet": {"meters": 0.3048, "inches": 12, "centimeters": 30.48, "kilometers": 0.0003048, "miles": 0.000189394},
                "inches": {"meters": 0.0254, "feet": 0.0833333, "centimeters": 2.54, "kilometers": 2.54e-5, "miles": 1.5783e-5},
                "centimeters": {"meters": 0.01, "feet": 0.0328084, "inches": 0.393701, "kilometers": 1e-5, "miles": 6.2137e-6},
                "kilometers": {"meters": 1000, "feet": 3280.84, "inches": 39370.1, "centimeters": 100000, "miles": 0.621371},
                "miles": {"meters": 1609.34, "feet": 5280, "inches": 63360, "centimeters": 160934, "kilometers": 1.60934}
            },
            "weight": {
                "kilograms": {"pounds": 2.20462, "grams": 1000, "ounces": 35.274, "metric tons": 0.001},
                "pounds": {"kilograms": 0.453592, "grams": 453.592, "ounces": 16, "metric tons": 0.000453592},
                "grams": {"kilograms": 0.001, "pounds": 0.00220462, "ounces": 0.035274, "metric tons": 1e-6},
                "ounces": {"kilograms": 0.0283495, "pounds": 0.0625, "grams": 28.3495, "metric tons": 2.835e-5},
                "metric tons": {"kilograms": 1000, "pounds": 2204.62, "grams": 1e6, "ounces": 35274}
            },
            "temperature": {
                "celsius": {"fahrenheit": lambda c: (c * 9/5) + 32, "kelvin": lambda c: c + 273.15},
                "fahrenheit": {"celsius": lambda f: (f - 32) * 5/9, "kelvin": lambda f: (f - 32) * 5/9 + 273.15},
                "kelvin": {"celsius": lambda k: k - 273.15, "fahrenheit": lambda k: (k - 273.15) * 9/5 + 32}
            },
            "volume": {
                "liters": {"milliliters": 1000, "gallons": 0.264172, "quarts": 1.05669, "cubic meters": 0.001},
                "milliliters": {"liters": 0.001, "gallons": 0.000264172, "quarts": 0.00105669, "cubic meters": 1e-6},
                "gallons": {"liters": 3.78541, "milliliters": 3785.41, "quarts": 4, "cubic meters": 0.00378541},
                "quarts": {"liters": 0.946353, "milliliters": 946.353, "gallons": 0.25, "cubic meters": 0.000946353},
                "cubic meters": {"liters": 1000, "milliliters": 1e6, "gallons": 264.172, "quarts": 1056.69}
            }
        }
        # Create a reverse mapping from unit to category for easy lookup
        self.unit_categories = {unit: category for category, units in self.conversion_factors.items() for unit in units}

    @property
    def description(self) -> str:
        return "Converts values between various units of measurement (length, weight, temperature, etc.)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform: 'convert' or 'list_units'.",
                    "default": "convert"
                },
                "value": {"type": "number", "description": "The numerical value to convert."},
                "from_unit": {"type": "string", "description": "The unit to convert from (e.g., 'meters', 'kg', 'celsius')."},
                "to_unit": {"type": "string", "description": "The unit to convert to (e.g., 'feet', 'pounds', 'fahrenheit')."}
            },
            "required": ["action"]
        }

    def execute(self, action: str = "convert", **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            if action == "convert":
                value = kwargs.get("value")
                from_unit = kwargs.get("from_unit")
                to_unit = kwargs.get("to_unit")
                if value is None or from_unit is None or to_unit is None:
                    raise ValueError("'value', 'from_unit', and 'to_unit' are required for 'convert' action.")
                
                converted_value = self._convert(value, from_unit, to_unit)
                return {
                    "original_value": value, 
                    "from_unit": from_unit, 
                    "to_unit": to_unit, 
                    "converted_value": round(converted_value, 4)
                }
            elif action == "list_units":
                return self._list_units()
            else:
                raise ValueError(f"Invalid action '{action}'. Supported actions are 'convert', 'list_units'.")

        except Exception as e:
            logger.error(f"An error occurred during unit conversion: {e}")
            return {"error": str(e)}

    def _convert(self, value: float, from_unit: str, to_unit: str) -> float:
        from_unit_lower = from_unit.lower()
        to_unit_lower = to_unit.lower()

        if not isinstance(value, (int, float)):
            raise TypeError("Invalid value. Value must be a number.")

        from_category = self.unit_categories.get(from_unit_lower)
        if not from_category:
            raise ValueError(f"Unknown unit: '{from_unit}'. Use 'list_units' to see available units.")
        
        to_category = self.unit_categories.get(to_unit_lower)
        if not to_category:
            raise ValueError(f"Unknown unit: '{to_unit}'. Use 'list_units' to see available units.")

        if from_category != to_category:
            raise ValueError(f"Cannot convert between different categories: from {from_category} to {to_category}.")

        # Handle direct conversion
        category_conversions = self.conversion_factors[from_category]
        conversion_factor = category_conversions.get(from_unit_lower, {}).get(to_unit_lower)

        if conversion_factor:
            return conversion_factor(value) if callable(conversion_factor) else value * conversion_factor
        
        # Handle indirect conversion (e.g., inches to meters via feet)
        # For this implementation, we will require direct conversion paths for simplicity.
        # A more advanced version could build a graph to find conversion paths.
        raise ValueError(f"Conversion from '{from_unit}' to '{to_unit}' is not directly supported.")

    def _list_units(self) -> Dict[str, List[str]]:
        return {category: list(units.keys()) for category, units in self.conversion_factors.items()}