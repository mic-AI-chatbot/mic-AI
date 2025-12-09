import os
import importlib.util
import inspect
import logging
import sys
from typing import Dict, Any

# Add the project root to the Python path to ensure tools.base_tool can be found
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

tool_registry: Dict[str, BaseTool] = {}

def load_tools_dynamically():
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
    # Add the directory containing the 'tools' package to sys.path
    # This allows absolute imports like 'tools.base_tool' to work
    tools_parent_dir = os.path.abspath(os.path.join(tools_dir, '..'))
    if tools_parent_dir not in sys.path:
        sys.path.insert(0, tools_parent_dir)

    # Explicitly add the virtual environment's site-packages to sys.path
    # This is a workaround if diffusers is not found due to environment issues
    venv_site_packages = os.path.join(os.path.dirname(sys.executable), '..', 'Lib', 'site-packages')
    if os.path.exists(venv_site_packages) and venv_site_packages not in sys.path:
        sys.path.insert(0, venv_site_packages)

    

    if not os.path.exists(tools_dir):
        logger.error(f"Tools directory not found: {tools_dir}")
        return

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            # Use absolute import path
            full_module_name = f"tools.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
            except Exception as e:
                logger.error(f"Error loading module {full_module_name}: {e}")
                continue

            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                    try:
                        tool_name = ''.join(['_'+c.lower() if c.isupper() else c for c in name]).lstrip('_')
                        tool_instance = obj(tool_name=tool_name)
                        tool_registry[tool_name] = tool_instance
                        logger.info(f"Loaded tool: {tool_name}")
                    except Exception as e:
                        logger.error(f"Error instantiating tool {name} from {full_module_name}: {e}")
    if not tool_registry:
        logger.warning("No tools were loaded into the registry.")

    # Remove the added path to avoid side effects
    if tools_parent_dir in sys.path:
        sys.path.remove(tools_parent_dir)
    if venv_site_packages in sys.path:
        sys.path.remove(venv_site_packages)