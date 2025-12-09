import glob
import os
import re

def fix_imports():
    print("Starting to fix missing LLMLoader imports...")
    files_fixed = 0
    tool_files = glob.glob('E:/mic/tools/*.py')

    for file_path in tool_files:
        if os.path.basename(file_path) == '__init__.py':
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Check if LLMLoader is used but not imported
            if 'LLMLoader' in content and 'from mic.llm_loader import LLMLoader' not in content:
                print(f"Fixing missing import in: {os.path.basename(file_path)}")
                # Prepend the import statement
                new_content = 'from mic.llm_loader import LLMLoader\n' + content
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                files_fixed += 1
        except Exception as e:
            print(f"Could not process {os.path.basename(file_path)}: {e}")

    print(f"Finished. Added missing import to {files_fixed} files.")

if __name__ == "__main__":
    fix_imports()

