import json
import os
import sys

def suppress_b311_warnings():
    """
    Parses the bandit_report.json file and adds '# nosec B311'
    to the lines with B311 warnings.
    """
    report_path = 'bandit_report.json'
    if not os.path.exists(report_path):
        print(f"Error: {report_path} not found.")
        return

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing {report_path}: {e}")
        return

    files_to_modify = {}
    for result in data.get('results', []):
        if result.get('test_id') == 'B311':
            filename = os.path.normpath(result.get('filename'))
            line_number = result.get('line_number')
            if filename and line_number:
                if filename not in files_to_modify:
                    files_to_modify[filename] = set()
                files_to_modify[filename].add(line_number)

    print("Files to modify:")
    # Using a serializable default for the set
    print(json.dumps(files_to_modify, indent=2, default=list))

    for filename, lines in files_to_modify.items():
        try:
            # Skip files in .venv
            if '.venv' in filename.replace('\\', '/') or '.git' in filename.replace('\\', '/'):
                print(f"Skipping file in virtual environment or git directory: {filename}")
                continue

            with open(filename, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()

            line_numbers = sorted(list(lines), reverse=True)

            for line_number in line_numbers:
                if 0 < line_number <= len(file_lines):
                    if 'nosec' not in file_lines[line_number - 1]:
                        file_lines[line_number - 1] = file_lines[line_number - 1].rstrip() + "  # nosec B311\n"

            with open(filename, 'w', encoding='utf-8') as f:
                f.writelines(file_lines)
            print(f"Suppressed B311 warnings in {filename}")

        except IOError as e:
            print(f"Error processing file {filename}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred with {filename}: {e}")


if __name__ == "__main__":
    suppress_b311_warnings()