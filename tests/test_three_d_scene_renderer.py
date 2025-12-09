import unittest
import sys
import os

# Add the 'mic' directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the tool module directly
import mic.tools.three_d_scene_renderer as three_d_renderer_tool

# Access classes and ab_tests from the imported module
Create3DSceneTool = three_d_renderer_tool.Create3DSceneTool
AddObjectTo3DSceneTool = three_d_renderer_tool.AddObjectTo3DSceneTool
Render3DSceneTool = three_d_renderer_tool.Render3DSceneTool
scenes = three_d_renderer_tool.scenes

import matplotlib.pyplot as plt # Keep this import for the Render3DSceneTool test
import numpy as np # Keep this import for the Render3DSceneTool test

class TestCreate3DSceneTool(unittest.TestCase):
    def setUp(self):
        self.tool = Create3DSceneTool()
        scenes.clear() # Clear scenes before each test to ensure isolation

    def test_create_new_scene(self):
        scene_id = "test_scene_1"
        result = self.tool.execute(scene_id=scene_id)
        self.assertIn("Successfully created", result)
        self.assertIn(scene_id, scenes)
        self.assertEqual(scenes[scene_id], [])

    def test_create_existing_scene(self):
        scene_id = "test_scene_2"
        self.tool.execute(scene_id=scene_id) # Create it once
        result = self.tool.execute(scene_id=scene_id) # Try to create again
        self.assertIn("Error: Scene with ID", result)
        self.assertIn("already exists", result)

class TestAddObjectTo3DSceneTool(unittest.TestCase):
    def setUp(self):
        self.create_tool = Create3DSceneTool()
        self.add_tool = AddObjectTo3DSceneTool()
        scenes.clear() # Clear scenes before each test

    def test_add_object_to_existing_scene(self):
        scene_id = "test_scene_add_obj"
        self.create_tool.execute(scene_id=scene_id)
        
        obj_type = "cube"
        position = {"x": 0, "y": 0, "z": 0}
        scale = {"x": 1, "y": 1, "z": 1}
        color = "red"
        
        result = self.add_tool.execute(scene_id=scene_id, object_type=obj_type, position=position, scale=scale, color=color)
        self.assertIn("Successfully added", result)
        self.assertEqual(len(scenes[scene_id]), 1)
        self.assertEqual(scenes[scene_id][0]["type"], obj_type)

    def test_add_object_to_non_existent_scene(self):
        scene_id = "non_existent_scene"
        obj_type = "sphere"
        position = {"x": 0, "y": 0, "z": 0}
        scale = {"x": 1, "y": 1, "z": 1}
        color = "blue"
        
        result = self.add_tool.execute(scene_id=scene_id, object_type=obj_type, position=position, scale=scale, color=color)
        self.assertIn("Error: Scene with ID", result)
        self.assertIn("not found", result)

class TestRender3DSceneTool(unittest.TestCase):
    def setUp(self):
        self.create_tool = Create3DSceneTool()
        self.add_tool = AddObjectTo3DSceneTool()
        self.render_tool = Render3DSceneTool()
        scenes.clear() # Clear scenes before each test
        self.output_dir = "temp_test_renders"
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        # Clean up generated image files
        for f in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, f))
        os.rmdir(self.output_dir)

    def test_render_empty_scene(self):
        scene_id = "empty_scene"
        self.create_tool.execute(scene_id=scene_id)
        output_path = os.path.join(self.output_dir, "empty_scene.png")
        result = self.render_tool.execute(scene_id=scene_id, output_path=output_path)
        self.assertIn("Scene 'empty_scene' is empty.", result)
        self.assertFalse(os.path.exists(output_path)) # No file should be created for empty scene

    def test_render_scene_with_objects(self):
        scene_id = "scene_with_objects"
        self.create_tool.execute(scene_id=scene_id)
        self.add_tool.execute(scene_id=scene_id, object_type="cube", position={"x": 1, "y": 1, "z": 1}, scale={"x": 1, "y": 1, "z": 1}, color="red")
        self.add_tool.execute(scene_id=scene_id, object_type="sphere", position={"x": -1, "y": -1, "z": -1}, scale={"x": 0.5, "y": 0.5, "z": 0.5}, color="blue")
        
        output_path = os.path.join(self.output_dir, "scene_with_objects.png")
        result = self.render_tool.execute(scene_id=scene_id, output_path=output_path)
        
        self.assertIn("Successfully rendered scene", result)
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(os.path.getsize(output_path) > 0) # Check if file is not empty

    def test_render_non_existent_scene(self):
        scene_id = "non_existent_render_scene"
        output_path = os.path.join(self.output_dir, "non_existent_render_scene.png")
        result = self.render_tool.execute(scene_id=scene_id, output_path=output_path)
        self.assertIn("Error: Scene with ID", result)
        self.assertIn("not found", result)
        self.assertFalse(os.path.exists(output_path))

if __name__ == "__main__":
    unittest.main()