import asyncio
import os
import sys
from typing import Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.ai_story_and_narrative_generator import AiStoryAndNarrativeGenerator

async def test_ai_story_and_narrative_generator():
    print("Testing AiStoryAndNarrativeGenerator...")
    tool = AiStoryAndNarrativeGenerator()

    # Test case 1: Basic story generation
    print("\nTest Case 1: Basic story generation")
    params1 = {
        "prompt": "A young wizard discovers a hidden power.",
        "genre": "fantasy",
        "max_length": 100
    }
    result1 = await tool.execute(**params1)
    print(f"Result 1: {result1}")
    assert "story" in result1 and isinstance(result1["story"], str) and len(result1["story"]) > 0, "Test Case 1 Failed: No story generated or invalid format."  # nosec B101
    print("Test Case 1 Passed.")

    # Test case 2: Story with specific characters and setting
    print("\nTest Case 2: Story with specific characters and setting")
    params2 = {
        "prompt": "A detective investigates a strange case.",
        "genre": "mystery",
        "characters": "Detective Miles Corbin, a mysterious informant",
        "setting": "a foggy, neon-lit city",
        "max_length": 150
    }
    result2 = await tool.execute(**params2)
    print(f"Result 2: {result2}")
    assert "story" in result2 and isinstance(result2["story"], str) and len(result2["story"]) > 0, "Test Case 2 Failed: No story generated or invalid format."  # nosec B101
    print("Test Case 2 Passed.")

    # Test case 3: Story with plot points
    print("\nTest Case 3: Story with plot points")
    params3 = {
        "prompt": "A scientist invents a time machine.",
        "genre": "sci-fi",
        "plot_points": "first trip to the past; unexpected consequences; a race against time",
        "max_length": 120
    }
    result3 = await tool.execute(**params3)
    print(f"Result 3: {result3}")
    assert "story" in result3 and isinstance(result3["story"], str) and len(result3["story"]) > 0, "Test Case 3 Failed: No story generated or invalid format."  # nosec B101
    print("Test Case 3 Passed.")

    # Test case 4: Empty prompt (should return an error)
    print("\nTest Case 4: Empty prompt")
    params4 = {
        "prompt": ""
    }
    result4 = await tool.execute(**params4)
    print(f"Result 4: {result4}")
    assert "error" in result4 and "Prompt cannot be empty" in result4["error"], "Test Case 4 Failed: Did not return expected error for empty prompt."  # nosec B101
    print("Test Case 4 Passed.")

    print("\nAll tests for AiStoryAndNarrativeGenerator completed.")

if __name__ == "__main__":
    asyncio.run(test_ai_story_and_narrative_generator())
