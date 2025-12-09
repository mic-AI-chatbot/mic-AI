import os
import importlib
import inspect
import logging
from pathlib import Path
import sys
import multiprocessing

# Add the project root to the Python path to allow for absolute imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# --- Logger Setup ---
LOG_FILE = 'tool_audit.log'

def setup_logging():
    """Sets up the logger for the main process and subprocesses."""
    # In the main process, overwrite the log file to clear it.
    if multiprocessing.current_process().name == 'MainProcess':
        # This avoids a potential PermissionError on os.remove() if the file is locked.
        # Opening with 'w' mode simply truncates the file.
        with open(LOG_FILE, 'w'):
            pass
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(processName)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler() # Also print to console
        ]
    )

def check_tool(tool_file: Path):
    """
    This function runs in a separate process to check a single tool.
    It imports the tool, finds the BaseTool subclass, and tries to instantiate it.
    """
    # Each subprocess needs to configure its own logging
    setup_logging() 
    
    module_name = f"tools.{tool_file.stem}"
    tool_class = None
    
    try:
        # --- Import the module ---
        # This is where heavy models might be loaded
        from tools.base_tool import BaseTool
        module = importlib.import_module(module_name)
        
        # --- Find the BaseTool subclass ---
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseTool) and obj is not BaseTool:
                tool_class = obj
                break
        
        if not tool_class:
            raise TypeError(f"No class inheriting from BaseTool found in {tool_file.name}")

        # --- Instantiate the class ---
        instance = tool_class()
        
        logging.info(f"SUCCESS: {module_name} ({tool_class.__name__})")
        return True

    except Exception as e:
        class_name_str = f" ({tool_class.__name__})" if tool_class else ""
        # Log the specific error for the failed tool
        logging.error(f"FAILURE: {module_name}{class_name_str} - {type(e).__name__}: {e}")
        return False

def audit_tools_main():
    """
    Main audit function that spawns a separate process for each tool check.
    """
    setup_logging()
    
    tools_dir = Path("tools")
    tool_files = sorted([f for f in tools_dir.glob("*.py") if f.is_file() and f.name not in ["__init__.py", "base_tool.py"]])
    
    total_tools = len(tool_files)
    successful_tools = 0
    failed_tools = 0

    logging.info(f"Starting tool audit in subprocess mode. Found {total_tools} tool files to check.")
    
    # Use a multiprocessing context for robustness
    ctx = multiprocessing.get_context('spawn')

    for tool_file in tool_files:
        process = ctx.Process(target=check_tool, args=(tool_file,), name=tool_file.stem)
        process.start()
        process.join(timeout=120) # Give each tool 2 minutes to load before timing out

        if process.is_alive():
            logging.error(f"TIMEOUT: {tool_file.stem} took too long to load and was terminated.")
            process.terminate()
            process.join()
            failed_tools += 1
        elif process.exitcode == 0:
            # A clean exit code is not enough, we need to check the log for success
            # For simplicity, we assume the subprocess logs its own status.
            # A more robust solution would use a Queue to return results.
            # We will re-evaluate the logs at the end.
            pass
        else:
            logging.error(f"CRASH: {tool_file.stem} exited with code {process.exitcode}.")
            failed_tools += 1
            
    logging.info("--- Audit Scan Complete ---")
    logging.info("Analyzing log file for final counts...")
    
    # Re-read the log file to get the final count
    with open(LOG_FILE, 'r') as f:
        log_content = f.read()
        successful_tools = log_content.count("SUCCESS:")
        # Total failures is more complex due to timeouts and crashes,
        # but we can approximate by subtracting successes from total.
        failed_tools = total_tools - successful_tools

    logging.info("--- Audit Final Results ---")
    logging.info(f"Total tools checked: {total_tools}")
    logging.info(f"Successful instantiations: {successful_tools}")
    logging.info(f"Failed/Crashed/Timeout: {failed_tools}")


if __name__ == "__main__":
    audit_tools_main()