
import logging
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MathProblemSolverTool(BaseTool):
    """
    A tool to solve single-variable linear algebraic equations and provide
    a step-by-step explanation.
    """

    def __init__(self, tool_name: str = "MathSolver", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "math_problems_data.json")
        self.data: Dict[str, Dict[str, Any]] = self._load_data(self.data_file, default={"problems": {}, "solutions": {}})

    @property
    def description(self) -> str:
        return "Solves single-variable linear equations (e.g., '3x + 7 = 22') and explains the steps."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_problem", "solve_problem"]},
                "problem_id": {"type": "string"},
                "statement": {"type": "string", "description": "The linear equation to solve."},
                "problem_type": {"type": "string", "default": "algebra"}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.data_file, 'w') as f: json.dump(self.data, f, indent=4)

    def add_problem(self, problem_id: str, statement: str, problem_type: str = "algebra") -> Dict[str, Any]:
        """Adds a new mathematical problem to the system."""
        if problem_id in self.data["problems"]:
            raise ValueError(f"Problem with ID '{problem_id}' already exists.")
        
        new_problem = {"problem_id": problem_id, "statement": statement, "problem_type": problem_type}
        self.data["problems"][problem_id] = new_problem
        self._save_data()
        return new_problem

    def solve_problem(self, problem_id: str) -> Dict[str, Any]:
        """Solves a linear equation and generates a step-by-step explanation."""
        problem = self.data["problems"].get(problem_id)
        if not problem: raise ValueError(f"Problem '{problem_id}' not found.")
        
        statement = problem['statement'].replace("Solve for", "").replace(":", "").strip()
        
        # Regex to parse equations like 'ax + b = c' or 'ax - b = c'
        match = re.match(r"(\d+)\s*\*?\s*([a-zA-Z])\s*([+\-])\s*(\d+)\s*=\s*(\d+)", statement)
        
        if not match:
            raise ValueError("Could not parse the equation. Please use the format 'ax + b = c'.")
            
        a, var, op, b, c = match.groups()
        a, b, c = float(a), float(b), float(c)

        explanation = [f"1. Start with the equation: {a}{var} {op} {b} = {c}"]
        
        solution = 0
        if op == '+':
            # ax + b = c  =>  ax = c - b
            c_minus_b = c - b
            explanation.append(f"2. Subtract {b} from both sides: {a}{var} = {c} - {b} => {a}{var} = {c_minus_b}")
            # x = (c - b) / a
            if a == 0: raise ValueError("Cannot solve for 'a' coefficient of zero.")
            solution = c_minus_b / a
            explanation.append(f"3. Divide by {a}: {var} = {c_minus_b} / {a}")
        elif op == '-':
            # ax - b = c  =>  ax = c + b
            c_plus_b = c + b
            explanation.append(f"2. Add {b} to both sides: {a}{var} = {c} + {b} => {a}{var} = {c_plus_b}")
            # x = (c + b) / a
            if a == 0: raise ValueError("Cannot solve for 'a' coefficient of zero.")
            solution = c_plus_b / a
            explanation.append(f"3. Divide by {a}: {var} = {c_plus_b} / {a}")

        explanation.append(f"4. The solution is {var} = {solution}")

        solution_report = {
            "solution_id": f"SOL-{problem_id}", "problem_id": problem_id,
            "solution_value": solution, "explanation": "\n".join(explanation)
        }
        self.data["solutions"][solution_report["solution_id"]] = solution_report
        self._save_data()
        return solution_report

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {"add_problem": self.add_problem, "solve_problem": self.solve_problem}
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MathProblemSolverTool functionality...")
    temp_dir = "temp_math_solver_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    solver_tool = MathProblemSolverTool(data_dir=temp_dir)
    
    try:
        # 1. Add a linear algebra problem
        print("\n--- Adding a problem ---")
        problem_statement = "Solve for x: 3x + 7 = 22"
        solver_tool.execute(operation="add_problem", problem_id="alg001", statement=problem_statement)
        print(f"Problem added: '{problem_statement}'")

        # 2. Solve the problem and get a real step-by-step explanation
        print("\n--- Solving the problem ---")
        solution = solver_tool.execute(operation="solve_problem", problem_id="alg001")
        print("Solution Report:")
        print(f"  Solution: {solution['solution_value']}")
        print("  Explanation:")
        print(solution['explanation'])

        # 3. Add and solve another problem
        print("\n--- Adding and solving another problem ---")
        problem_statement_2 = "5y - 10 = 40"
        solver_tool.execute(operation="add_problem", problem_id="alg002", statement=problem_statement_2)
        solution2 = solver_tool.execute(operation="solve_problem", problem_id="alg002")
        print("Solution Report:")
        print(f"  Solution: {solution2['solution_value']}")
        print("  Explanation:")
        print(solution2['explanation'])

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
