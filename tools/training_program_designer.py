import logging
import random
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated training programs
training_programs: Dict[str, Dict[str, Any]] = {}

class TrainingProgramDesignerTool(BaseTool):
    """
    A tool for simulating the design and management of training programs.
    """
    def __init__(self, tool_name: str = "training_program_designer_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates designing, updating, and viewing training programs with weekly breakdowns."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string", 
                    "description": "The command: 'design', 'update', 'get_details', 'list_all'."
                },
                "program_name": {"type": "string", "description": "The unique name of the training program."},
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of learning goals for the program (for 'design')."
                },
                "duration_weeks": {"type": "integer", "description": "The total duration of the program in weeks (for 'design')."},
                "add_goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Goals to add to an existing program (for 'update')."
                }
            },
            "required": ["command"]
        }

    def execute(self, command: str, **kwargs: Any) -> Dict:
        try:
            command = command.lower()
            program_name = kwargs.get("program_name")

            if command != 'list_all' and not program_name:
                raise ValueError("'program_name' is required for this command.")

            actions = {
                "design": self._design_program,
                "update": self._update_program,
                "get_details": self._get_program_details,
                "list_all": self._list_all_programs,
            }
            if command not in actions:
                raise ValueError(f"Invalid command. Supported: {list(actions.keys())}")

            return actions[command](program_name=program_name, **kwargs)

        except Exception as e:
            logger.error(f"An error occurred in TrainingProgramDesignerTool: {e}")
            return {"error": str(e)}

    def _design_program(self, program_name: str, goals: List[str], duration_weeks: int, **kwargs) -> Dict:
        if not goals or not duration_weeks:
            raise ValueError("'goals' and 'duration_weeks' are required for designing a program.")
        
        logger.info(f"Designing training program: {program_name}")
        if program_name in training_programs:
            raise ValueError(f"Training program '{program_name}' already exists.")
        
        # Simulate generating a weekly plan
        weekly_plan = {}
        shuffled_goals = random.sample(goals, len(goals))  # nosec B311
        for week in range(1, duration_weeks + 1):
            # Assign one or two goals per week
            goals_for_week = [shuffled_goals[i % len(shuffled_goals)] for i in range(week-1, week)]
            weekly_plan[f"Week {week}"] = {
                "focus": ", ".join(goals_for_week),
                "activities": ["Read documentation", "Complete practical exercise", "Team review session"]
            }

        training_programs[program_name] = {
            "program_name": program_name,
            "goals": goals,
            "duration_weeks": duration_weeks,
            "status": "designed",
            "weekly_plan": weekly_plan
        }
        
        return {
            "message": f"Training program '{program_name}' designed successfully.",
            "details": training_programs[program_name]
        }

    def _update_program(self, program_name: str, add_goals: Optional[List[str]] = None, **kwargs) -> Dict:
        logger.info(f"Updating program: {program_name}")
        if program_name not in training_programs:
            raise ValueError(f"Training program '{program_name}' not found.")
        
        program = training_programs[program_name]
        if add_goals:
            original_goals = set(program["goals"])
            original_goals.update(add_goals)
            program["goals"] = list(original_goals)
            # Here you could also regenerate the weekly plan, but for simulation we'll just add the goals.
            logger.info(f"Added goals to '{program_name}': {add_goals}")

        return {"message": f"Program '{program_name}' updated.", "details": program}

    def _get_program_details(self, program_name: str, **kwargs) -> Dict:
        logger.info(f"Getting details for program: {program_name}")
        if program_name not in training_programs:
            raise ValueError(f"Training program '{program_name}' not found.")
        
        return {"details": training_programs[program_name]}

    def _list_all_programs(self, **kwargs) -> Dict:
        if not training_programs:
            return {"message": "No training programs have been designed yet."}
        
        summary_list = [
            {
                "program_name": details["program_name"],
                "duration_weeks": details["duration_weeks"],
                "num_goals": len(details["goals"])
            }
            for name, details in training_programs.items()
        ]
        return {"designed_programs": summary_list}