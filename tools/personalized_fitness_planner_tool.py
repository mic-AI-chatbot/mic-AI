
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalizedFitnessPlannerTool(BaseTool):
    """
    A tool that simulates a personalized fitness planner, generating workout
    plans based on user goals, fitness level, and available equipment.
    """

    def __init__(self, tool_name: str = "PersonalizedFitnessPlanner", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.users_file = os.path.join(self.data_dir, "fitness_user_profiles.json")
        self.plans_file = os.path.join(self.data_dir, "workout_plans.json")
        
        # User profiles: {user_id: {name: ..., fitness_level: ..., goal: ..., equipment: []}}
        self.user_profiles: Dict[str, Dict[str, Any]] = self._load_data(self.users_file, default={})
        # Workout plans: {user_id: {plan_id: {duration_days: ..., plan: []}}}
        self.workout_plans: Dict[str, Dict[str, Any]] = self._load_data(self.plans_file, default={})

    @property
    def description(self) -> str:
        return "Simulates personalized fitness planning: generates workout plans based on user data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_user_profile", "generate_workout_plan", "get_workout_plan"]},
                "user_id": {"type": "string"},
                "name": {"type": "string"},
                "fitness_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                "goal": {"type": "string", "enum": ["lose weight", "build muscle", "improve endurance"]},
                "equipment": {"type": "array", "items": {"type": "string"}, "enum": ["gym", "home_weights", "bodyweight"]},
                "duration_days": {"type": "integer", "minimum": 7, "maximum": 90}
            },
            "required": ["operation", "user_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_user_profiles(self):
        with open(self.users_file, 'w') as f: json.dump(self.user_profiles, f, indent=2)

    def _save_workout_plans(self):
        with open(self.plans_file, 'w') as f: json.dump(self.workout_plans, f, indent=2)

    def create_user_profile(self, user_id: str, name: str, fitness_level: str, goal: str, equipment: List[str]) -> Dict[str, Any]:
        """Creates a new user profile for fitness planning."""
        if user_id in self.user_profiles: raise ValueError(f"User '{user_id}' already exists.")
        
        new_profile = {
            "id": user_id, "name": name, "fitness_level": fitness_level, "goal": goal, "equipment": equipment,
            "created_at": datetime.now().isoformat()
        }
        self.user_profiles[user_id] = new_profile
        self._save_user_profiles()
        return new_profile

    def generate_workout_plan(self, user_id: str, duration_days: int) -> Dict[str, Any]:
        """Generates a personalized workout plan for a user."""
        user = self.user_profiles.get(user_id)
        if not user: raise ValueError(f"User '{user_id}' not found. Create profile first.")
        
        plan_id = f"plan_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        workout_plan = {"plan_id": plan_id, "user_id": user_id, "duration_days": duration_days, "plan": []}

        # Rule-based plan generation
        exercises_by_type = {
            "strength": {
                "bodyweight": ["Push-ups", "Squats", "Lunges", "Plank"],
                "home_weights": ["Dumbbell Rows", "Goblet Squats", "Overhead Press"],
                "gym": ["Bench Press", "Deadlifts", "Squats", "Pull-ups"]
            },
            "cardio": ["Running", "Cycling", "Jumping Jacks", "Burpees"],
            "flexibility": ["Stretching", "Yoga"]
        }

        for day in range(1, duration_days + 1):
            day_plan = {"day": day, "focus": "", "exercises": []}
            
            if user["goal"] == "build muscle":
                day_plan["focus"] = "Strength Training"
                equipment_options = user["equipment"]
                selected_equipment = random.choice(equipment_options)  # nosec B311
                
                for _ in range(random.randint(3, 5)): # 3-5 exercises  # nosec B311
                    exercise = random.choice(exercises_by_type["strength"][selected_equipment])  # nosec B311
                    sets = 3 if user["fitness_level"] == "beginner" else 4
                    reps = 10 if user["fitness_level"] == "beginner" else 8
                    day_plan["exercises"].append({"name": exercise, "sets": sets, "reps": reps})
            
            elif user["goal"] == "lose weight":
                day_plan["focus"] = random.choice(["Cardio", "Full Body Strength"])  # nosec B311
                if day_plan["focus"] == "Cardio":
                    day_plan["exercises"].append({"name": random.choice(exercises_by_type["cardio"]), "duration_minutes": random.randint(20, 45)})  # nosec B311
                else:
                    selected_equipment = random.choice(user["equipment"])  # nosec B311
                    for _ in range(random.randint(2, 4)):  # nosec B311
                        exercise = random.choice(exercises_by_type["strength"][selected_equipment])  # nosec B311
                        day_plan["exercises"].append({"name": exercise, "sets": 3, "reps": 12})
            
            workout_plan["plan"].append(day_plan)

        if user_id not in self.workout_plans: self.workout_plans[user_id] = {}
        self.workout_plans[user_id][plan_id] = workout_plan
        self._save_workout_plans()
        return workout_plan

    def get_workout_plan(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated workout plan for a user."""
        if user_id not in self.workout_plans or plan_id not in self.workout_plans[user_id]:
            raise ValueError(f"Workout plan '{plan_id}' for user '{user_id}' not found.")
        return self.workout_plans[user_id][plan_id]

    def execute(self, operation: str, user_id: str, **kwargs: Any) -> Any:
        if operation == "create_user_profile":
            return self.create_user_profile(user_id, kwargs['name'], kwargs['fitness_level'], kwargs['goal'], kwargs['equipment'])
        elif operation == "generate_workout_plan":
            return self.generate_workout_plan(user_id, kwargs['duration_days'])
        elif operation == "get_workout_plan":
            return self.get_workout_plan(user_id, kwargs['plan_id'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PersonalizedFitnessPlannerTool functionality...")
    temp_dir = "temp_fitness_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    planner_tool = PersonalizedFitnessPlannerTool(data_dir=temp_dir)
    
    try:
        # 1. Create a user profile
        print("\n--- Creating user profile for 'user_john' ---")
        planner_tool.execute(operation="create_user_profile", user_id="user_john", name="John Doe", fitness_level="intermediate", goal="build muscle", equipment=["gym"])
        print("Profile created.")

        # 2. Generate a workout plan for John
        print("\n--- Generating workout plan for 'user_john' (30 days) ---")
        john_plan = planner_tool.execute(operation="generate_workout_plan", user_id="user_john", duration_days=30)
        print(json.dumps(john_plan, indent=2))

        # 3. Create another user profile
        print("\n--- Creating user profile for 'user_jane' ---")
        planner_tool.execute(operation="create_user_profile", user_id="user_jane", name="Jane Smith", fitness_level="beginner", goal="lose weight", equipment=["bodyweight"])
        print("Profile created.")

        # 4. Generate a workout plan for Jane
        print("\n--- Generating workout plan for 'user_jane' (14 days) ---")
        jane_plan = planner_tool.execute(operation="generate_workout_plan", user_id="user_jane", duration_days=14)
        print(json.dumps(jane_plan, indent=2))

        # 5. Get John's workout plan
        print("\n--- Getting workout plan for 'user_john' ---")
        johns_plan_retrieved = planner_tool.execute(operation="get_workout_plan", user_id="user_john", plan_id=john_plan["plan_id"])
        print(json.dumps(johns_plan_retrieved, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
