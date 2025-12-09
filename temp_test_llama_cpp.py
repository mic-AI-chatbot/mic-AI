import sys
try:
    from llama_cpp import LlamaCpp
    print("LlamaCpp imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)