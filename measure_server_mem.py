import subprocess
import psutil
import time
import os
import sys

def measure_server_memory():
    """
    Starts the server, waits for it to initialize, and measures its memory usage.
    """
    # Ensure we use the python from the virtual environment
    python_executable = os.path.join('E:\\', 'mic', 'venv', 'Scripts', 'python.exe')
    
    server_command = [
        python_executable,
        "-m", "uvicorn",
        "server:app",
        "--host", "127.0.0.1",
        "--port", "8001"
    ]

    print(f"Starting server with command: {' '.join(server_command)}")
    
    # Start the server as a background process
    try:
        server_process = subprocess.Popen(
            server_command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    except FileNotFoundError:
        print(f"Error: Could not find the python executable at {python_executable}")
        return

    print(f"Server started with PID: {server_process.pid}. Waiting 15 seconds for initialization...")
    time.sleep(15) # Wait 15 seconds for the server to fully start up

    try:
        # Check if the process is still running
        if server_process.poll() is not None:
             raise psutil.NoSuchProcess(server_process.pid)

        process = psutil.Process(server_process.pid)
        
        # Get memory usage of the parent process and all its children
        mem_usage = process.memory_info().rss
        children = process.children(recursive=True)
        for child in children:
            try:
                mem_usage += child.memory_info().rss
            except psutil.NoSuchProcess:
                continue # Child might have terminated

        mem_usage_mb = mem_usage / (1024 * 1024) # in MB
        print(f"Server baseline memory usage (including child processes): {mem_usage_mb:.2f} MB")

    except psutil.NoSuchProcess:
        print("Server process not found. It might have crashed on startup.")
        stdout, stderr = server_process.communicate()
        print("\n--- STDOUT ---")
        print(stdout.decode(errors='ignore'))
        print("\n--- STDERR ---")
        print(stderr.decode(errors='ignore'))

    finally:
        if server_process.poll() is None:
            print("Terminating server process group.")
            # Terminate the entire process group
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(server_process.pid)])
            print("Server terminated.")

if __name__ == "__main__":
    measure_server_memory()
