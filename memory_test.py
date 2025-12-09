import os
import psutil
import time
from llama_cpp import Llama

def measure_gguf_memory_usage():
    """
    Measures the memory usage of loading a GGUF model using llama-cpp-python.
    """
    model_filename = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    model_path = os.path.join("E:\\", "mic", "LLM", model_filename)

    if not os.path.exists(model_path):
        print(f"Model file not found at: {model_path}")
        print("Please ensure you have downloaded the model and placed it in the correct directory.")
        return

    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 * 1024)  # in MB
    print(f"Memory before loading model: {mem_before:.2f} MB")

    try:
        print(f"Loading model: {model_path}...")
        
        # Initialize the Llama model from the GGUF file
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,      # Context size
            n_gpu_layers=0,  # Set to 0 to ensure CPU-only for RAM measurement
            verbose=False    # Suppress detailed llama.cpp output
        )
        
        print("Model loaded successfully.")

        mem_after = process.memory_info().rss / (1024 * 1024)  # in MB
        print(f"Memory after loading model: {mem_after:.2f} MB")
        print(f"Memory used by model: {(mem_after - mem_before):.2f} MB")

    except Exception as e:
        print(f"An error occurred while loading the model: {e}")

if __name__ == "__main__":
    measure_gguf_memory_usage()