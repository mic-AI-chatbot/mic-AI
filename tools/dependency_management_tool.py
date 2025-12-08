import logging
import os
import re
import subprocess  # nosec B404
import json
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DependencyManagementTool(BaseTool):
    """
    A tool for managing project dependencies using various package managers (pip, npm, cargo).
    """

    def __init__(self, tool_name: str = "dependency_management_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Manages project dependencies: adds, removes, checks, lists, updates dependencies, and checks for vulnerabilities."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The dependency management operation to perform.",
                    "enum": ["add_dependency", "remove_dependency", "check_dependency", "list_dependencies", "update_dependency", "check_vulnerabilities"]
                },
                "package_manager": {"type": "string", "enum": ["pip", "npm", "cargo"]},
                "dependency": {"type": "string"},
                "requirements_file": {"type": "string", "default": "requirements.txt"},
                "dependency_name": {"type": "string"} # For check_dependency, remove_dependency
            },
            "required": ["operation", "package_manager"]
        }

    def _run_command(self, command: List[str]) -> Dict[str, Any]:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603
            if result.returncode != 0:
                logger.error(f"Command failed: {' '.join(command)}\nStdout: {result.stdout}\nStderr: {result.stderr}")
                raise RuntimeError(f"Command failed with exit code {result.returncode}: {result.stderr.strip()}")
            return {"stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "returncode": result.returncode}
        except FileNotFoundError:
            raise FileNotFoundError(f"Command '{command[0]}' not found. Is the package manager installed and in PATH?")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while running command: {e}")

    def _read_requirements_file(self, requirements_file: str) -> List[str]:
        if not os.path.exists(requirements_file): return []
        with open(requirements_file, "r") as f: return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    def _write_requirements_file(self, requirements_file: str, lines: List[str]) -> None:
        with open(requirements_file, "w") as f:
            for line in lines: f.write(line + "\n")

    def _add_dependency(self, package_manager: str, dependency: str, requirements_file: str = "requirements.txt") -> Dict[str, Any]:
        package_manager = package_manager.lower()
        if package_manager == "pip":
            dependency_name = re.split(r'[<>=]', dependency)[0].strip()
            lines = self._read_requirements_file(requirements_file)
            found = False
            for i, line in enumerate(lines):
                if re.split(r'[<>=]', line)[0].strip().lower() == dependency_name.lower():
                    lines[i] = dependency; found = True; break
            if not found: lines.append(dependency)
            self._write_requirements_file(requirements_file, lines)
            return {"status": "success", "message": f"Added/Updated '{dependency}' in '{requirements_file}'."}
        elif package_manager == "npm": return self._run_command(["npm", "install", dependency])
        elif package_manager == "cargo": return self._run_command(["cargo", "add", dependency])
        else: raise ValueError(f"Unsupported package manager: {package_manager}")

    def _remove_dependency(self, package_manager: str, dependency_name: str, requirements_file: str = "requirements.txt") -> Dict[str, Any]:
        package_manager = package_manager.lower()
        if package_manager == "pip":
            lines = self._read_requirements_file(requirements_file)
            lines_to_keep = [line for line in lines if re.split(r'[<>=]', line)[0].strip().lower() != dependency_name.lower()]
            if len(lines_to_keep) == len(lines): raise ValueError(f"Dependency '{dependency_name}' not found in '{requirements_file}'.")
            self._write_requirements_file(requirements_file, lines_to_keep)
            return {"status": "success", "message": f"Removed '{dependency_name}' from '{requirements_file}'."}
        elif package_manager == "npm": return self._run_command(["npm", "uninstall", dependency_name])
        elif package_manager == "cargo": return self._run_command(["cargo", "remove", dependency_name])
        else: raise ValueError(f"Unsupported package manager: {package_manager}")

    def _check_dependency(self, package_manager: str, dependency_name: str, requirements_file: str = "requirements.txt") -> Dict[str, Any]:
        package_manager = package_manager.lower()
        if package_manager == "pip":
            lines = self._read_requirements_file(requirements_file)
            for line in lines:
                if re.split(r'[<>=]', line)[0].strip().lower() == dependency_name.lower(): return {"status": "found", "details": line.strip()}
            return {"status": "not_found", "details": f"Dependency '{dependency_name}' not found in '{requirements_file}'."}
        elif package_manager == "npm":
            result = self._run_command(["npm", "list", dependency_name])
            if dependency_name in result["stdout"]: return {"status": "found", "details": result["stdout"]}
            return {"status": "not_found", "details": result["stderr"]}
        elif package_manager == "cargo":
            result = self._run_command(["cargo", "tree", dependency_name])
            if dependency_name in result["stdout"]: return {"status": "found", "details": result["stdout"]}
            return {"status": "not_found", "details": result["stderr"]}
        else: raise ValueError(f"Unsupported package manager: {package_manager}")

    def _list_dependencies(self, package_manager: str, requirements_file: str = "requirements.txt") -> Dict[str, Any]:
        package_manager = package_manager.lower()
        if package_manager == "pip": return {"status": "success", "dependencies": self._read_requirements_file(requirements_file)}
        elif package_manager == "npm": return {"status": "success", "dependencies": self._run_command(["npm", "list"])["stdout"].splitlines()}
        elif package_manager == "cargo": return {"status": "success", "dependencies": self._run_command(["cargo", "tree"])["stdout"].splitlines()}
        else: raise ValueError(f"Unsupported package manager: {package_manager}")

    def _update_dependency(self, package_manager: str, dependency: Optional[str] = None, requirements_file: str = "requirements.txt") -> Dict[str, Any]:
        package_manager = package_manager.lower()
        if package_manager == "pip":
            if dependency: return self._run_command(["pip", "install", "--upgrade", dependency])
            else: return self._run_command(["pip", "install", "--upgrade", "-r", requirements_file])
        elif package_manager == "npm":
            if dependency: return self._run_command(["npm", "update", dependency])
            else: return self._run_command(["npm", "update"])
        elif package_manager == "cargo":
            if dependency: return self._run_command(["cargo", "update", "-p", dependency])
            else: return self._run_command(["cargo", "update"])
        else: raise ValueError(f"Unsupported package manager: {package_manager}")

    def _check_vulnerabilities(self, package_manager: str, requirements_file: str = "requirements.txt") -> Dict[str, Any]:
        package_manager = package_manager.lower()
        if package_manager == "pip":
            try: result = self._run_command(["pip-audit", "-r", requirements_file]); return {"status": "success", "report": result["stdout"]}
            except RuntimeError as e:
                if "pip-audit" in str(e):
                    try: result = self._run_command(["safety", "check", "-r", requirements_file]); return {"status": "success", "report": result["stdout"]}
                    except RuntimeError as e_safety: return {"status": "error", "message": f"Please install 'pip-audit' or 'safety' for pip vulnerability checking. Error: {e_safety}"}
                return {"status": "error", "message": str(e)}
        elif package_manager == "npm": return self._run_command(["npm", "audit"])
        elif package_manager == "cargo": return self._run_command(["cargo", "audit"])
        else: raise ValueError(f"Unsupported package manager: {package_manager}")

    def execute(self, operation: str, package_manager: str, **kwargs: Any) -> Dict[str, Any]:
        if operation == "add_dependency":
            return self._add_dependency(package_manager, kwargs.get("dependency"), kwargs.get("requirements_file", "requirements.txt"))
        elif operation == "remove_dependency":
            return self._remove_dependency(package_manager, kwargs.get("dependency_name"), kwargs.get("requirements_file", "requirements.txt"))
        elif operation == "check_dependency":
            return self._check_dependency(package_manager, kwargs.get("dependency_name"), kwargs.get("requirements_file", "requirements.txt"))
        elif operation == "list_dependencies":
            return self._list_dependencies(package_manager, kwargs.get("requirements_file", "requirements.txt"))
        elif operation == "update_dependency":
            return self._update_dependency(package_manager, kwargs.get("dependency"), kwargs.get("requirements_file", "requirements.txt"))
        elif operation == "check_vulnerabilities":
            return self._check_vulnerabilities(package_manager, kwargs.get("requirements_file", "requirements.txt"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DependencyManagementTool functionality...")
    tool = DependencyManagementTool()
    
    dummy_req_file = "dummy_requirements.txt"
    
    try:
        with open(dummy_req_file, "w") as f: f.write("requests==2.28.1\n")

        print("\n--- Adding Dependency ---")
        tool.execute(operation="add_dependency", package_manager="pip", dependency="pandas==1.5.0", requirements_file=dummy_req_file)
        
        print("\n--- Listing Dependencies ---")
        list_result = tool.execute(operation="list_dependencies", package_manager="pip", requirements_file=dummy_req_file)
        print(json.dumps(list_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(dummy_req_file): os.remove(dummy_req_file)
        print("\nCleanup complete.")