import unittest
import sys
import os
import re

# Add the 'mic' directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the tool module directly
import mic.tools.a_b_testing_orchestrator as ab_orchestrator_tool

# Access classes and ab_tests from the imported module
CreateABTestTool = ab_orchestrator_tool.CreateABTestTool
StartABTestTool = ab_orchestrator_tool.StartABTestTool
AllocateUserToABTestTool = ab_orchestrator_tool.AllocateUserToABTestTool
RecordConversionTool = ab_orchestrator_tool.RecordConversionTool
GetABTestResultTool = ab_orchestrator_tool.GetABTestResultTool
StopABTestTool = ab_orchestrator_tool.StopABTestTool
ab_tests = ab_orchestrator_tool.ab_tests

class TestCreateABTestTool(unittest.TestCase):
    def setUp(self):
        self.tool = CreateABTestTool()
        ab_tests.clear() # Clear state before each test

    def test_create_new_test(self):
        test_id = "test_001"
        variations = ["control", "variant_a"]
        success_metric = "conversion_rate"
        result = self.tool.execute(test_id=test_id, variations=variations, success_metric=success_metric)
        self.assertIn("created successfully", result)
        self.assertIn(test_id, ab_tests)
        self.assertFalse(ab_tests[test_id]["is_running"])

    def test_create_existing_test(self):
        test_id = "test_002"
        self.tool.execute(test_id=test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        result = self.tool.execute(test_id=test_id, variations=["control", "variant_b"], success_metric="conversion_rate")
        self.assertIn("already exists", result)

    def test_create_test_less_than_two_variations(self):
        test_id = "test_003"
        result = self.tool.execute(test_id=test_id, variations=["control"], success_metric="conversion_rate")
        self.assertIn("At least two variations are required", result)

class TestStartABTestTool(unittest.TestCase):
    def setUp(self):
        self.create_tool = CreateABTestTool()
        self.start_tool = StartABTestTool()
        ab_tests.clear()

    def test_start_existing_test(self):
        test_id = "test_004"
        self.create_tool.execute(test_id=test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        result = self.start_tool.execute(test_id=test_id)
        self.assertIn("started successfully", result)
        self.assertTrue(ab_tests[test_id]["is_running"])

    def test_start_non_existent_test(self):
        test_id = "non_existent_test"
        result = self.start_tool.execute(test_id=test_id)
        self.assertIn("not found", result)

    def test_start_already_running_test(self):
        test_id = "test_005"
        self.create_tool.execute(test_id=test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        self.start_tool.execute(test_id=test_id)
        result = self.start_tool.execute(test_id=test_id)
        self.assertIn("already running", result)

class TestAllocateUserToABTestTool(unittest.TestCase):
    def setUp(self):
        self.create_tool = CreateABTestTool()
        self.start_tool = StartABTestTool()
        self.allocate_tool = AllocateUserToABTestTool()
        ab_tests.clear()
        self.test_id = "test_006"
        self.create_tool.execute(test_id=self.test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        self.start_tool.execute(test_id=self.test_id)

    def test_allocate_user(self):
        user_id = "user_1"
        result = self.allocate_tool.execute(test_id=self.test_id, user_id=user_id)
        self.assertIn("allocated to the", result)
        # Check if user count increased for one of the variations
        total_users = sum(v["users"] for v in ab_tests[self.test_id]["variations"].values())
        self.assertEqual(total_users, 1)

    def test_allocate_user_non_running_test(self):
        test_id = "test_007"
        self.create_tool.execute(test_id=test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        user_id = "user_2"
        result = self.allocate_tool.execute(test_id=test_id, user_id=user_id)
        self.assertIn("is not running", result)

class TestRecordConversionTool(unittest.TestCase):
    def setUp(self):
        self.create_tool = CreateABTestTool()
        self.start_tool = StartABTestTool()
        self.allocate_tool = AllocateUserToABTestTool()
        self.record_tool = RecordConversionTool()
        ab_tests.clear()
        self.test_id = "test_008"
        self.create_tool.execute(test_id=self.test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        self.start_tool.execute(test_id=self.test_id)

    def test_record_conversion(self):
        user_id = "user_3"
        self.allocate_tool.execute(test_id=self.test_id, user_id=user_id)
        result = self.record_tool.execute(test_id=self.test_id, user_id=user_id)
        self.assertIn("Conversion recorded", result)
        # Check if conversion count increased for the allocated variation
        total_conversions = sum(v["conversions"] for v in ab_tests[self.test_id]["variations"].values())
        self.assertEqual(total_conversions, 1)

    def test_record_conversion_non_existent_test(self):
        user_id = "user_4"
        result = self.record_tool.execute(test_id="non_existent_test", user_id=user_id)
        self.assertIn("not found", result)

class TestGetABTestResultTool(unittest.TestCase):
    def setUp(self):
        self.create_tool = CreateABTestTool()
        self.start_tool = StartABTestTool()
        self.allocate_tool = AllocateUserToABTestTool()
        self.record_tool = RecordConversionTool()
        self.get_result_tool = GetABTestResultTool()
        ab_tests.clear()
        self.test_id = "test_009"
        self.create_tool.execute(test_id=self.test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        self.start_tool.execute(test_id=self.test_id)

    def test_get_results_empty_test(self):
        result = self.get_result_tool.execute(test_id=self.test_id)
        self.assertIn("Results for A/B test", result)
        self.assertIn("'users': 0", result)
        self.assertIn("'conversions': 0", result)

    def test_get_results_with_data(self):
        # Simulate some data
        self.allocate_tool.execute(test_id=self.test_id, user_id="user_a")
        self.record_tool.execute(test_id=self.test_id, user_id="user_a") # 1 user, 1 conversion for one variation
        self.allocate_tool.execute(test_id=self.test_id, user_id="user_b") # 1 user, 0 conversion for another variation
        
        result = self.get_result_tool.execute(test_id=self.test_id)
        self.assertIn("Results for A/B test", result)
        # Check for statistical significance message
        self.assertRegex(result, r"The result is (not )?statistically significant")

    def test_get_results_non_existent_test(self):
        result = self.get_result_tool.execute(test_id="non_existent_test_results")
        self.assertIn("not found", result)

class TestStopABTestTool(unittest.TestCase):
    def setUp(self):
        self.create_tool = CreateABTestTool()
        self.start_tool = StartABTestTool()
        self.stop_tool = StopABTestTool()
        ab_tests.clear()
        self.test_id = "test_010"
        self.create_tool.execute(test_id=self.test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        self.start_tool.execute(test_id=self.test_id)

    def test_stop_running_test(self):
        result = self.stop_tool.execute(test_id=self.test_id)
        self.assertIn("stopped successfully", result)
        self.assertFalse(ab_tests[self.test_id]["is_running"])

    def test_stop_non_existent_test(self):
        result = self.stop_tool.execute(test_id="non_existent_stop_test")
        self.assertIn("not found", result)

    def test_stop_already_stopped_test(self):
        test_id = "test_011"
        self.create_tool.execute(test_id=test_id, variations=["control", "variant_a"], success_metric="conversion_rate")
        # Don't start it, so it's already stopped (or never started)
        result = self.stop_tool.execute(test_id=test_id)
        self.assertIn("is not currently running", result)

if __name__ == "__main__":
    unittest.main()