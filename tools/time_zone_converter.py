from datetime import datetime
import pytz
import logging
import json
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class TimeZoneConverterTool(BaseTool):
    """
    A tool for converting time between different time zones.
    """

    def __init__(self, tool_name: str = "time_zone_converter_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Converts time between timezones, gets current time in a timezone, and lists timezones."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'convert', 'current_time', 'list_timezones'."
                },
                "time_str": {"type": "string", "description": "Time string to convert (e.g., '2025-11-14 10:30:00')."},
                "from_tz": {"type": "string", "description": "The source IANA timezone (e.g., 'UTC', 'America/New_York')."},
                "to_tz": {"type": "string", "description": "The target IANA timezone."},
                "datetime_format": {
                    "type": "string", 
                    "description": "The format of the time_str.", 
                    "default": "%Y-%m-%d %H:%M:%S"
                },
                "region_filter": {"type": "string", "description": "Filter for list_timezones (e.g., 'America', 'Europe')."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Union[str, Dict, List]:
        try:
            action = action.lower()
            actions = {
                "convert": self._convert_time,
                "current_time": self._get_current_time,
                "list_timezones": self._list_timezones,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            result = actions[action](**kwargs)
            output_format = kwargs.get("output_format", "text")
            return self._format_output(result, output_format)

        except Exception as e:
            logger.error(f"An error occurred in TimeZoneConverterTool: {e}")
            return self._format_output({"error": str(e)}, kwargs.get("output_format", "json"))

    def _convert_time(self, time_str: str, from_tz: str, to_tz: str, datetime_format: str = "%Y-%m-%d %H:%M:%S", **kwargs) -> Dict:
        try:
            dt_object = datetime.strptime(time_str, datetime_format)
            source_tz = pytz.timezone(from_tz)
            target_tz = pytz.timezone(to_tz)
            
            localized_dt = source_tz.localize(dt_object)
            converted_dt = localized_dt.astimezone(target_tz)

            return {
                "original_time": f"{time_str} {from_tz}", 
                "converted_time": f"{converted_dt.strftime(datetime_format)} {to_tz}"
            }
        except pytz.UnknownTimeZoneError as e:
            raise ValueError(f"Unknown timezone: {e}. Use a valid IANA name (e.g., 'America/New_York').")
        except ValueError as e:
            raise ValueError(f"Time string/format mismatch: {e}. Ensure '{time_str}' matches '{datetime_format}'.")

    def _get_current_time(self, to_tz: str, **kwargs) -> Dict:
        try:
            target_tz = pytz.timezone(to_tz)
            current_time = datetime.now(target_tz)
            return {"timezone": to_tz, "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")}
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone '{to_tz}'. Use a valid IANA name.")

    def _list_timezones(self, region_filter: str = None, **kwargs) -> List[str]:
        if region_filter:
            return [tz for tz in pytz.common_timezones if tz.lower().startswith(region_filter.lower())]
        return pytz.common_timezones

    def _format_output(self, result: Union[Dict, List, str], output_format: str) -> Union[str, Dict, List]:
        if output_format == 'json':
            if isinstance(result, (dict, list)):
                return result
            return json.dumps({"message": str(result)})
        else: # text format
            if isinstance(result, dict):
                return "\n".join([f"{k}: {v}" for k, v in result.items()])
            elif isinstance(result, list):
                # For long lists, show a summary
                if len(result) > 50:
                    return f"Found {len(result)} timezones. Here are the first 50:\n" + "\n".join(result[:50])
                return "\n".join(result)
            return str(result)