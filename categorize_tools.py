import os
import re

def categorize_tool(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if re.search(r'get_llm', content) or re.search(r'LlamaLLM', content):
        return 'llm'
    
    if re.search(r'placeholder', content, re.IGNORECASE):
        return 'placeholder'
    elif re.search(r'simulate', content, re.IGNORECASE):
        return 'simulation'
    
    return 'other'

def main():
    tools_dir = 'E:/mic/tools'
    categorization = {'llm': [], 'placeholder': [], 'simulation': [], 'other': []}
    
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and not filename.startswith('__') and not filename.startswith('test_') and filename != 'base_tool.py':
            file_path = os.path.join(tools_dir, filename)
            category = categorize_tool(file_path)
            categorization[category].append(filename)

    print("Tool Categorization Summary:")
    for category, files in categorization.items():
        print(f"- {category.capitalize()}: {len(files)} tools")

    # Optional: print the files in each category
    for category, files in categorization.items():
        print(f"\n{category.capitalize()} Tools:")
        for f in files:
            print(f"  - {f}")

if __name__ == '__main__':
    main()
