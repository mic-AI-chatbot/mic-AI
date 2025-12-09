
import unittest
import sys
import os

# Add the 'mic' directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the tool module directly
import mic.tools.abstractive_summarization_tool as summarization_tool

# Access classes and ab_tests from the imported module
AbstractiveSummarizationTool = summarization_tool.AbstractiveSummarizationTool
summarization_cache = summarization_tool.summarization_cache

class TestAbstractiveSummarizationTool(unittest.TestCase):
    def setUp(self):
        self.tool = AbstractiveSummarizationTool()
        summarization_cache.clear() # Clear cache before each test

    def test_empty_text_input(self):
        result = self.tool.execute(text="")
        self.assertIn("Error: Input text cannot be empty.", result)

    def test_text_too_short(self):
        result = self.tool.execute(text="short text", min_length=30)
        self.assertIn("Error: Input text is too short.", result)

    def test_summarization_success(self):
        # This test requires the model to be loaded successfully.
        # If the model loading fails in __init__, self.summarizer will be None.
        if self.tool.summarizer is None:
            self.skipTest("Summarization model not loaded, skipping test.")

        text = "The quick brown fox jumps over the lazy dog. This is a classic sentence used for testing. It contains all letters of the alphabet. We are testing the summarization tool with this text."
        result = self.tool.execute(text=text, max_length=20, min_length=10)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        self.assertLessEqual(len(result.split()), 20) # Check max_length (approx)

    def test_summarization_with_cache(self):
        if self.tool.summarizer is None:
            self.skipTest("Summarization model not loaded, skipping test.")

        text = "This is a test sentence for caching. It should be summarized and then retrieved from cache."
        max_length = 20
        min_length = 10

        # First call, should populate cache
        summary1 = self.tool.execute(text=text, max_length=max_length, min_length=min_length, use_cache=True)
        self.assertIn(f"{text}:{max_length}:{min_length}", summarization_cache)
        self.assertEqual(summarization_cache[f"{text}:{max_length}:{min_length}"], summary1)

        # Second call, should use cache
        summary2 = self.tool.execute(text=text, max_length=max_length, min_length=min_length, use_cache=True)
        self.assertEqual(summary1, summary2)

    def test_summarization_without_cache(self):
        if self.tool.summarizer is None:
            self.skipTest("Summarization model not loaded, skipping test.")

        text = "This text should not be cached."
        max_length = 20
        min_length = 10
        
        self.tool.execute(text=text, max_length=max_length, min_length=min_length, use_cache=False)
        self.assertNotIn(f"{text}:{max_length}:{min_length}", summarization_cache)

if __name__ == "__main__":
    unittest.main()
