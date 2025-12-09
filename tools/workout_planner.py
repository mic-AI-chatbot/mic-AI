import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated workout plans and an exercise database
workout_plans: Dict[str, Dict[str, Any]] = {}
exercise_database = {
    "chest": ["Push-ups", "Bench Press (Dumbbell)", "Dumbbell Flyes"],
    "back": ["Pull-ups", "Bent-over Rows", "Lat Pulldowns"],
    "legs": ["Squats", "Lunges", "Deadlifts (Romanian)"],
    "shoulders": ["Overhead Press", "Lateral Raises", "Front Raises"],
    "arms": ["Bicep Curls", "Tricep Dips", "Hammer Curls"],
    "core": ["Plank", "Crunches", "Leg Raises"]
}

class WorkoutPlanner(BaseTool):
    def __init__(self, tool_name):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates workout planning: generate plans, find exercises, and track progress."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'generate_plan', 'find_exercises', 'track_progress', 'get_plan_details', 'list_exercises'."
                },
                "plan_name": {"type": "string", "description": "The unique name for the workout plan."},
                "fitness_goal": {
                    "type": "string", 
                    "description": "The user's fitness goal (e.g., 'muscle_gain', 'weight_loss', 'endurance')."
                },
                "intensity": {
                    "type": "string", 
                    "description": "The desired intensity ('beginner', 'intermediate', 'advanced').",
                    "default": "intermediate"
                },
                "duration_weeks": {"type": "integer", "description": "The duration of the plan in weeks.", "default": 4},
                "muscle_group": {"type": "string", "description": "The muscle group for finding exercises (e.g., 'chest', 'legs')."},
                "user_id": {"type": "string", "description": "The ID of the user for tracking progress."},
                "workout_data": {"type": "object", "description": "Data for tracking progress (e.g., {'date': '2023-11-15', 'exercises_completed': 5})."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            plan_name = kwargs.get("plan_name")
            user_id = kwargs.get("user_id")

            if action in ['generate_plan', 'get_plan_details'] and not plan_name:
                raise ValueError(f"'plan_name' is required for the '{action}' action.")
            if action == 'track_progress' and not user_id:
                raise ValueError("'user_id' is required for 'track_progress' action.")

            actions = {
                "generate_plan": self._generate_workout_plan,
                "find_exercises": self._find_exercises,
                "track_progress": self._track_progress,
                "get_plan_details": self._get_plan_details,
                "list_exercises": self._list_exercises,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WorkoutPlannerTool: {e}")
            return {"error": str(e)}

    def _generate_workout_plan(self, plan_name: str, fitness_goal: str, intensity: str = "intermediate", duration_weeks: int = 4, **kwargs) -> Dict:
        if not fitness_goal:
            raise ValueError("'fitness_goal' is required to generate a plan.")
        if plan_name in workout_plans:
            raise ValueError(f"Workout plan '{plan_name}' already exists.")
            
        logger.info(f"Generating workout plan '{plan_name}' for goal '{fitness_goal}'.")
        
        plan_details = {
            "goal": fitness_goal,
            "intensity": intensity,
            "duration_weeks": duration_weeks,
            "weekly_schedule": {}
        }

        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for week in range(1, duration_weeks + 1):
            plan_details["weekly_schedule"][f"Week {week}"] = {}
            for day in days_of_week:
                if random.random() < 0.6: # Simulate 3-4 workout days per week  # nosec B311
                    muscle_groups = random.sample(list(exercise_database.keys()), random.randint(1, 2))  # nosec B311
                    exercises_for_day = []
                    for mg in muscle_groups:
                        exercises_for_day.extend(random.sample(exercise_database[mg], random.randint(1, 2)))  # nosec B311
                    
                    plan_details["weekly_schedule"][f"Week {week}"][day] = {
                        "focus": ", ".join(muscle_groups),
                        "exercises": exercises_for_day,
                        "reps_sets": "3 sets of 8-12 reps" if intensity != "beginner" else "3 sets of 10-15 reps"
                    }
                else:
                    plan_details["weekly_schedule"][f"Week {week}"][day] = "Rest Day"
        
        workout_plans[plan_name] = plan_details
        return {"message": "Workout plan generated successfully.", "details": plan_details}

    def _find_exercises(self, muscle_group: Optional[str] = None, **kwargs) -> Dict:
        if muscle_group and muscle_group not in exercise_database:
            raise ValueError(f"Muscle group '{muscle_group}' not recognized. Supported: {list(exercise_database.keys())}")
            
        if muscle_group:
            exercises = exercise_database[muscle_group]
        else:
            exercises = [ex for mg_list in exercise_database.values() for ex in mg_list]
            
        return {"exercises": exercises}

    def _track_progress(self, user_id: str, workout_data: Dict[str, Any], **kwargs) -> Dict:
        # This is a simple simulation. In a real system, this would update a user's profile.
        logger.info(f"Simulating progress tracking for user '{user_id}'.")
        return {"message": "Progress tracked successfully.", "user_id": user_id, "workout_data": workout_data}

    def _get_plan_details(self, plan_name: str, **kwargs) -> Dict:
        if plan_name not in workout_plans:
            raise ValueError(f"Workout plan '{plan_name}' not found.")
        return {"plan_details": workout_plans[plan_name]}

    def _list_exercises(self, **kwargs) -> Dict:
        return {"exercise_database": exercise_database}