
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    from tools.three_d_scene_renderer import Create3DSceneTool, AddObjectTo3DSceneTool, Render3DSceneTool
    print("Successfully imported the tools from three_d_scene_renderer.py")
    
    # You can also instantiate them to be sure
    create_tool = Create3DSceneTool()
    add_tool = AddObjectTo3DSceneTool()
    render_tool = Render3DSceneTool()
    print("Successfully instantiated the tools.")

except ImportError as e:
    print(f"Failed to import tools: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
