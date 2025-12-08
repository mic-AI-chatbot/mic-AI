import logging
import os
import json
import random
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RecipeAnalyzerTool(BaseTool):
    """
    A tool that analyzes existing recipes for nutritional information and
    complexity, and allows for rule-based modifications (e.g., making it vegetarian).
    """

    def __init__(self, tool_name: str = "RecipeAnalyzer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.recipes_file = os.path.join(self.data_dir, "analyzed_recipes.json")
        # Recipes structure: {recipe_id: {title: ..., ingredients: [], instructions: [], analysis: {}}}
        self.analyzed_recipes: Dict[str, Dict[str, Any]] = self._load_data(self.recipes_file, default={})

    @property
    def description(self) -> str:
        return "Analyzes recipes for nutritional info/complexity and allows rule-based modifications (e.g., vegetarian)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_recipe", "analyze_recipe", "modify_recipe", "get_recipe_details"]},
                "recipe_id": {"type": "string"},
                "title": {"type": "string"},
                "recipe_text": {"type": "string", "description": "The full text of the recipe to analyze."},
                "modifications": {"type": "object", "description": "e.g., {'make_vegetarian': True, 'reduce_sugar_by_percent': 25}"}
            },
            "required": ["operation", "recipe_id"]
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
        with open(self.recipes_file, 'w') as f: json.dump(self.analyzed_recipes, f, indent=2)

    def add_recipe(self, recipe_id: str, title: str, recipe_text: str) -> Dict[str, Any]:
        """Adds a new recipe to be analyzed."""
        if recipe_id in self.analyzed_recipes: raise ValueError(f"Recipe '{recipe_id}' already exists.")
        
        new_recipe = {
            "id": recipe_id, "title": title, "original_text": recipe_text,
            "ingredients": [], "instructions": [], "analysis": {},
            "added_at": datetime.now().isoformat()
        }
        self.analyzed_recipes[recipe_id] = new_recipe
        self._save_data()
        return new_recipe

    def analyze_recipe(self, recipe_id: str) -> Dict[str, Any]:
        """Analyzes an existing recipe for ingredients, instructions, and basic nutritional info."""
        recipe = self.analyzed_recipes.get(recipe_id)
        if not recipe: raise ValueError(f"Recipe '{recipe_id}' not found. Add it first.")
        
        text = recipe["original_text"].lower()
        
        # Simple ingredient extraction
        ingredients = re.findall(r'(\d+\s*(?:cup|oz|g|tbsp|tsp)?\s*\w+\s*\w*)', text)
        recipe["ingredients"] = list(set(ingredients)) # Unique ingredients
        
        # Simple instruction extraction (sentences starting with verbs)
        instructions = re.findall(r'([A-Z][a-z]*\s+\w+.*?\.)', text)
        recipe["instructions"] = instructions
        
        # Basic nutritional analysis (keyword-based)
        nutritional_info = {"protein_g": 0, "carbs_g": 0, "fat_g": 0}
        if "chicken" in text or "beef" in text or "tofu" in text: nutritional_info["protein_g"] = random.randint(20, 50)  # nosec B311
        if "rice" in text or "pasta" in text or "bread" in text: nutritional_info["carbs_g"] = random.randint(30, 80)  # nosec B311
        if "oil" in text or "butter" in text: nutritional_info["fat_g"] = random.randint(10, 40)  # nosec B311
        
        recipe["analysis"] = {"nutritional_info": nutritional_info, "complexity": random.choice(["easy", "medium", "hard"])}  # nosec B311
        self._save_data()
        return recipe

    def modify_recipe(self, recipe_id: str, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Modifies an existing recipe based on specified rules."""
        recipe = self.analyzed_recipes.get(recipe_id)
        if not recipe: raise ValueError(f"Recipe '{recipe_id}' not found. Add it first.")
        
        modified_recipe = recipe.copy()
        modified_recipe["modifications_applied"] = []

        if modifications.get("make_vegetarian"):
            meat_ingredients = ["chicken", "beef", "pork", "fish", "salmon"]
            for i, ing in enumerate(modified_recipe["ingredients"]):
                if any(meat in ing.lower() for meat in meat_ingredients):
                    modified_recipe["ingredients"][i] = ing.replace(meat, random.choice(["tofu", "tempeh", "lentils"]))  # nosec B311
                    modified_recipe["modifications_applied"].append(f"Replaced '{ing}' with a vegetarian alternative.")
            modified_recipe["title"] = f"Vegetarian {modified_recipe['title']}"
        
        if modifications.get("reduce_sugar_by_percent"):
            percent = modifications["reduce_sugar_by_percent"]
            modified_recipe["instructions"] = [inst.replace("sugar", f"reduced sugar ({percent}% less)") for inst in modified_recipe["instructions"]]
            modified_recipe["modifications_applied"].append(f"Reduced sugar by {percent}%.")

        self._save_data()
        return modified_recipe

    def get_recipe_details(self, recipe_id: str) -> Dict[str, Any]:
        """Retrieves the full details of an analyzed recipe."""
        recipe = self.analyzed_recipes.get(recipe_id)
        if not recipe: raise ValueError(f"Recipe '{recipe_id}' not found.")
        return recipe

    def execute(self, operation: str, recipe_id: str, **kwargs: Any) -> Any:
        if operation == "add_recipe":
            title = kwargs.get('title')
            recipe_text = kwargs.get('recipe_text')
            if not all([title, recipe_text]):
                raise ValueError("Missing 'title' or 'recipe_text' for 'add_recipe' operation.")
            return self.add_recipe(recipe_id, title, recipe_text)
        elif operation == "analyze_recipe":
            # No additional kwargs required for analyze_recipe
            return self.analyze_recipe(recipe_id)
        elif operation == "modify_recipe":
            modifications = kwargs.get('modifications')
            if not modifications:
                raise ValueError("Missing 'modifications' for 'modify_recipe' operation.")
            return self.modify_recipe(recipe_id, modifications)
        elif operation == "get_recipe_details":
            # No additional kwargs required for get_recipe_details
            return self.get_recipe_details(recipe_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RecipeAnalyzerTool functionality...")
    temp_dir = "temp_recipe_analyzer_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    analyzer_tool = RecipeAnalyzerTool(data_dir=temp_dir)
    
    try:
        # 1. Add a sample recipe
        print("\n--- Adding recipe 'Chicken Stir-fry' ---")
        recipe_text = """
        Chicken Stir-fry:
        Ingredients:
        1 lb chicken breast, cut into strips
        2 cups broccoli florets
        1 red bell pepper, sliced
        1/4 cup soy sauce
        1 tbsp ginger, minced
        Instructions:
        1. Heat oil in a large skillet over medium-high heat.
        2. Add chicken and cook until browned.
        3. Add broccoli and bell pepper, stir-fry for 5 minutes.
        4. Stir in soy sauce and ginger. Cook for another 2 minutes.
        5. Serve hot with rice.
        """
        analyzer_tool.execute(operation="add_recipe", recipe_id="chicken_stir_fry", title="Chicken Stir-fry", recipe_text=recipe_text)
        print("Recipe added.")

        # 2. Analyze the recipe
        print("\n--- Analyzing 'chicken_stir_fry' ---")
        analysis_result = analyzer_tool.execute(operation="analyze_recipe", recipe_id="chicken_stir_fry")
        print(json.dumps(analysis_result, indent=2))

        # 3. Modify the recipe to be vegetarian
        print("\n--- Modifying 'chicken_stir_fry' to be vegetarian ---")
        modified_recipe = analyzer_tool.execute(operation="modify_recipe", recipe_id="chicken_stir_fry", modifications={"make_vegetarian": True})
        print(json.dumps(modified_recipe, indent=2))

        # 4. Get details of the original recipe
        print("\n--- Getting details of original 'chicken_stir_fry' ---")
        original_details = analyzer_tool.execute(operation="get_recipe_details", recipe_id="chicken_stir_fry")
        print(json.dumps(original_details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")