import os
import glob
import re

def fix_tool_init_methods():
    tools_dir = 'E:\\mic\\tools'
    tool_files = glob.glob(os.path.join(tools_dir, '*.py'))
    files_fixed = 0
    
    # Regex to find the incorrect __init__ signature `def __init__(self):`
    init_pattern = re.compile(r'def __init__\(self\):')
    # Regex to find a super().__init__ call with a hardcoded tool_name
    super_pattern = re.compile(r'super\(\).__init__\(tool_name=.*?\)')

    print(f"Scanning {len(tool_files)} tool files in '{tools_dir}'...")

    for file_path in tool_files:
        if os.path.basename(file_path) in ['__init__.py', 'base_tool.py']:
            continue

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Only proceed if it looks like a tool file with the specific problem
            if 'BaseTool' in content and init_pattern.search(content):
                
                # First, replace the __init__ signature
                # 'def __init__(self):' -> 'def __init__(self, tool_name):'
                new_content = init_pattern.sub('def __init__(self, tool_name):', content)
                
                # Then, replace the hardcoded super() call
                # 'super().__init__(tool_name="...")' -> 'super().__init__(tool_name=tool_name)'
                new_content = super_pattern.sub('super().__init__(tool_name=tool_name)', new_content)

                if new_content != content:
                    print(f"Fixing file: {os.path.basename(file_path)}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    files_fixed += 1

        except Exception as e:
            print(f"Error processing file {os.path.basename(file_path)}: {e}")

    print(f"\nFinished. Corrected {files_fixed} files.")

if __name__ == "__main__":
    fix_tool_init_methods()
