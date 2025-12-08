import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool
from scipy.stats import chi2_contingency
import numpy as np

logger = logging.getLogger(__name__)

# In-memory storage for simulated A/B tests.
# This dictionary holds the state of all A/B tests, including variations,
# user counts, conversion data, and the running status.
ab_tests: Dict[str, Dict[str, Any]] = {}

class CreateABTestTool(BaseTool):
    """
    A tool to create a new A/B test definition. This sets up the test structure,
    including its unique ID, the variations to be tested, and the metric for success.
    """
    def __init__(self, tool_name="create_a_b_test"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new A/B test definition with specified variations and success metric."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_id": {"type": "string", "description": "A unique identifier for the A/B test."},
                "variations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of variation names (e.g., [\"control\", \"variant_a\"])."
                },
                "success_metric": {"type": "string", "description": "The metric to measure success (e.g., \"conversion_rate\", \"click_through_rate\")."}
            },
            "required": ["test_id", "variations", "success_metric"]
        }

    def execute(self, test_id: str, variations: List[str], success_metric: str, **kwargs: Any) -> str:
        """Creates and initializes a new A/B test."""
        if test_id in ab_tests:
            return f"Error: A/B test with ID '{test_id}' already exists."
        
        if not variations or len(variations) < 2:
            return "Error: At least two variations are required for an A/B test."

        ab_tests[test_id] = {
            "variations": {variation: {"users": 0, "conversions": 0} for variation in variations},
            "success_metric": success_metric,
            "is_running": False
        }
        logger.info(f"A/B test '{test_id}' created with variations: {variations} and success metric: {success_metric}")
        return f"A/B test '{test_id}' created successfully."

class StartABTestTool(BaseTool):
    """
    A tool to start a previously created A/B test.
    Starting a test makes it active and allows users to be allocated to its variations.
    """
    def __init__(self, tool_name="start_a_b_test"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Starts an existing A/B test, making it active for user allocation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_id": {"type": "string", "description": "The ID of the A/B test to start."}
            },
            "required": ["test_id"]
        }

    def execute(self, test_id: str, **kwargs: Any) -> str:
        """Starts a specified A/B test."""
        if test_id not in ab_tests:
            return f"Error: A/B test with ID '{test_id}' not found."
        
        if ab_tests[test_id]["is_running"]:
            return f"Warning: A/B test '{test_id}' is already running."

        ab_tests[test_id]["is_running"] = True
        logger.info(f"A/B test '{test_id}' started.")
        return f"A/B test '{test_id}' started successfully."

class AllocateUserToABTestTool(BaseTool):
    """
    A tool to allocate a user to a variation in a running A/B test.
    This simulates bucketing a user into one of the test variations.
    """
    def __init__(self, tool_name="allocate_user_to_a_b_test"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Allocates a user to a variation in a running A/B test and returns the assigned variation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_id": {"type": "string", "description": "The ID of the A/B test."},
                "user_id": {"type": "string", "description": "The ID of the user to allocate."}
            },
            "required": ["test_id", "user_id"]
        }

    def execute(self, test_id: str, user_id: str, **kwargs: Any) -> str:
        """Allocates a user to a variation of an A/B test."""
        if test_id not in ab_tests:
            return f"Error: A/B test with ID '{test_id}' not found."
        
        if not ab_tests[test_id]["is_running"]:
            return f"Error: A/B test '{test_id}' is not running."

        variations = list(ab_tests[test_id]["variations"].keys())
        # Simple, deterministic allocation based on user_id hash.
        # This ensures a user is always allocated to the same variation.
        variation_index = hash(user_id) % len(variations)
        assigned_variation = variations[variation_index]

        ab_tests[test_id]["variations"][assigned_variation]["users"] += 1
        logger.info(f"User '{user_id}' allocated to variation '{assigned_variation}' in test '{test_id}'.")
        
        return f"User '{user_id}' is allocated to the '{assigned_variation}' variation."

class RecordConversionTool(BaseTool):
    """
    A tool to record a conversion event for a user in an A/B test.
    This is used to track the success metric for each variation.
    """
    def __init__(self, tool_name="record_conversion"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Records a conversion event for a user who has been allocated to a variation in an A/B test."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_id": {"type": "string", "description": "The ID of the A/B test."},
                "user_id": {"type": "string", "description": "The ID of the user who converted."}
            },
            "required": ["test_id", "user_id"]
        }

    def execute(self, test_id: str, user_id: str, **kwargs: Any) -> str:
        """Records a conversion for a user in a specific A/B test variation."""
        if test_id not in ab_tests:
            return f"Error: A/B test with ID '{test_id}' not found."

        variations = list(ab_tests[test_id]["variations"].keys())
        # The user's variation is determined consistently by their user_id.
        variation_index = hash(user_id) % len(variations)
        assigned_variation = variations[variation_index]

        # Note: This assumes the user was already allocated. In a real system,
        # you might check that first. Here, we just increment the conversion count
        # for the user's assigned variation.
        ab_tests[test_id]["variations"][assigned_variation]["conversions"] += 1
        logger.info(f"Conversion recorded for user '{user_id}' in variation '{assigned_variation}' of test '{test_id}'.")
        
        return f"Conversion recorded for user '{user_id}' in variation '{assigned_variation}'."

class GetABTestResultTool(BaseTool):
    """
    A tool to retrieve the current results of an A/B test.
    This provides statistics for each variation, including user counts, conversion rates,
    and a statistical significance test (chi-squared) to determine if the results are significant.
    """
    def __init__(self, tool_name="get_a_b_test_result"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current results of an A/B test, including conversion rates and statistical significance."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_id": {"type": "string", "description": "The ID of the A/B test to get results for."}
            },
            "required": ["test_id"]
        }

    def execute(self, test_id: str, **kwargs: Any) -> str:
        """Retrieves and calculates the results of a specified A/B test."""
        if test_id not in ab_tests:
            return f"Error: A/B test with ID '{test_id}' not found."

        test_data = ab_tests[test_id]
        results = {}
        contingency_table = []

        for variation, data in test_data["variations"].items():
            users = data["users"]
            conversions = data["conversions"]
            non_conversions = users - conversions
            conversion_rate = (conversions / users) * 100 if users > 0 else 0
            
            results[variation] = {
                "users": users,
                "conversions": conversions,
                f"{test_data['success_metric']}": f"{conversion_rate:.2f}%"
            }
            contingency_table.append([conversions, non_conversions])

        # Determine the winning variation based on conversion rate
        winner = max(results, key=lambda v: float(results[v][test_data['success_metric']].replace('%',''))) if results else None

        # Perform chi-squared test for statistical significance
        significance_result = ""
        if len(contingency_table) >= 2 and np.sum(contingency_table) > 0:
            try:
                chi2, p_value, _, _ = chi2_contingency(np.array(contingency_table))
                significance_level = 0.05  # Standard alpha level
                is_significant = p_value < significance_level
                significance_result = (
                    f"Chi-squared test results: p-value = {p_value:.4f}. "
                    f"The result is {'statistically significant' if is_significant else 'not statistically significant'} "
                    f"at the {significance_level*100}% level."
                )
            except ValueError as e:
                significance_result = f"Could not perform chi-squared test: {e}"
        
        return (f"Results for A/B test '{test_id}': {results}. "
                f"The current winning variation is '{winner}'. "
                f"{significance_result}")


class StopABTestTool(BaseTool):
    """
    A tool to stop a running A/B test.
    This prevents new users from being allocated to the test.
    """
    def __init__(self, tool_name="stop_a_b_test"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Stops a running A/B test, preventing new users from being allocated to it."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_id": {"type": "string", "description": "The ID of the A/B test to stop."}
            },
            "required": ["test_id"]
        }

    def execute(self, test_id: str, **kwargs: Any) -> str:
        """Stops a running A/B test."""
        if test_id not in ab_tests:
            return f"Error: A/B test with ID '{test_id}' not found."
        
        if not ab_tests[test_id]["is_running"]:
            return f"Warning: A/B test '{test_id}' is not currently running."

        ab_tests[test_id]["is_running"] = False
        logger.info(f"A/B test '{test_id}' stopped.")
        return f"A/B test '{test_id}' stopped successfully."