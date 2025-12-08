import logging
import os
import json
import random
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

LEVEL_DESIGN_IDEAS_FILE = "level_design_ideas.json"
LAYOUT_SKETCHES_DIR = "generated_layout_sketches"

class LevelDesignAssistant:
    """
    A tool for simulating assistance to a game level designer.
    It generates ideas, suggests challenges, and creates layout sketches for game levels.
    Design ideas and layouts are persisted in a local JSON file, and simulated
    sketches are stored as placeholder files.
    """

    def __init__(self):
        """
        Initializes the LevelDesignAssistant.
        Loads existing level design ideas or creates new ones.
        Ensures the layout sketches directory exists.
        """
        self.ideas: Dict[str, Dict[str, Any]] = self._load_ideas()
        os.makedirs(LAYOUT_SKETCHES_DIR, exist_ok=True)

    def _load_ideas(self) -> Dict[str, Dict[str, Any]]:
        """Loads level design ideas from a JSON file."""
        if os.path.exists(LEVEL_DESIGN_IDEAS_FILE):
            with open(LEVEL_DESIGN_IDEAS_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted ideas file '{LEVEL_DESIGN_IDEAS_FILE}'. Starting with empty data.")
                    return {}
        return {}

    def _save_ideas(self) -> None:
        """Saves current level design ideas to a JSON file."""
        with open(LEVEL_DESIGN_IDEAS_FILE, 'w') as f:
            json.dump(self.ideas, f, indent=4)

    def generate_level_idea(self, idea_id: str, game_name: str, level_theme: str,
                            desired_elements: List[str]) -> Dict[str, Any]:
        """
        Generates a new level idea based on theme and desired elements.

        Args:
            idea_id: A unique identifier for the level idea.
            game_name: The name of the game.
            level_theme: The theme of the game level (e.g., 'ancient ruins', 'futuristic city').
            desired_elements: A list of desired elements for the level (e.g., 'puzzles', 'enemies', 'traps').

        Returns:
            A dictionary containing the details of the newly generated level idea.
        """
        if not idea_id or not game_name or not level_theme or not desired_elements:
            raise ValueError("Idea ID, game name, level theme, and desired elements cannot be empty.")
        if idea_id in self.ideas:
            raise ValueError(f"Level idea with ID '{idea_id}' already exists.")
        
        # Simulate idea generation
        layout_concept = f"A {level_theme} level with a focus on {random.choice(desired_elements)}. "  # nosec B311
        layout_concept += f"It features {random.randint(1, 3)} main areas and {random.randint(2, 5)} challenges."  # nosec B311

        new_idea = {
            "idea_id": idea_id,
            "game_name": game_name,
            "level_theme": level_theme,
            "desired_elements": desired_elements,
            "layout_concept": layout_concept,
            "generated_at": datetime.now().isoformat(),
            "suggested_challenges": [],
            "layout_sketch_path": None
        }
        self.ideas[idea_id] = new_idea
        self._save_ideas()
        logger.info(f"Level idea '{idea_id}' generated for game '{game_name}'.")
        return new_idea

    def suggest_challenges(self, idea_id: str, challenge_type: str) -> Dict[str, Any]:
        """
        Suggests challenges for a level idea.

        Args:
            idea_id: The ID of the level idea.
            challenge_type: The type of challenge to suggest (e.g., 'combat', 'puzzle', 'platforming').

        Returns:
            A dictionary containing the suggested challenges.
        """
        idea = self.ideas.get(idea_id)
        if not idea:
            raise ValueError(f"Level idea with ID '{idea_id}' not found.")
        if challenge_type not in ["combat", "puzzle", "platforming", "exploration"]:
            raise ValueError(f"Invalid challenge type: '{challenge_type}'.")

        suggested_challenges: List[str] = []
        if challenge_type == "combat":
            suggested_challenges.append("Encounter with a mini-boss guarding a key item.")
            suggested_challenges.append("Wave-based enemy attack in a confined space.")
        elif challenge_type == "puzzle":
            suggested_challenges.append("A logic puzzle involving ancient runes.")
            suggested_challenges.append("Environmental puzzle requiring specific item usage.")
        
        idea["suggested_challenges"].append({
            "type": challenge_type,
            "suggestions": suggested_challenges,
            "generated_at": datetime.now().isoformat()
        })
        self._save_ideas()
        logger.info(f"Challenges suggested for idea '{idea_id}'.")
        return {"idea_id": idea_id, "challenge_type": challenge_type, "suggestions": suggested_challenges}

    def create_layout_sketch(self, idea_id: str, output_file: str) -> Dict[str, Any]:
        """
        Simulates creating a layout sketch (placeholder file) for a level idea.

        Args:
            idea_id: The ID of the level idea.
            output_file: The absolute path to save the simulated sketch file.

        Returns:
            A dictionary containing the updated level idea details with the sketch path.
        """
        idea = self.ideas.get(idea_id)
        if not idea:
            raise ValueError(f"Level idea with ID '{idea_id}' not found.")
        if not os.path.isabs(output_file):
            raise ValueError("Output file path must be an absolute path.")
        
        self._ensure_output_dir_exists(output_file)

        try:
            sketch_content = f"--- Layout Sketch for {idea['name']} ({idea['level_theme']}) ---\n"
            sketch_content += f"Concept: {idea['layout_concept']}\n"
            sketch_content += "\n" + "".join(random.choice(['#', '.', 'X', 'O']) for _ in range(200)) # Simple ASCII sketch  # nosec B311
            
            with open(output_file, 'w') as f:
                f.write(sketch_content)
            
            idea["layout_sketch_path"] = os.path.abspath(output_file)
            self._save_ideas()
            logger.info(f"Layout sketch for idea '{idea_id}' generated at '{output_file}'.")
            return idea
        except Exception as e:
            logger.error(f"Failed to generate sketch for '{idea_id}': {e}")
            raise RuntimeError(f"Sketch generation failed: {e}")

    def list_ideas(self, game_name: Optional[str] = None, level_theme: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists all generated level ideas, optionally filtered by game name or level theme.

        Args:
            game_name: Optional game name to filter ideas by.
            level_theme: Optional level theme to filter ideas by.

        Returns:
            A list of dictionaries, each representing a level idea.
        """
        filtered_ideas = list(self.ideas.values())
        if game_name:
            filtered_ideas = [idea for idea in filtered_ideas if idea.get("game_name") == game_name]
        if level_theme:
            filtered_ideas = [idea for idea in filtered_ideas if idea.get("level_theme") == level_theme]
        
        logger.info(f"Listed {len(filtered_ideas)} level ideas.")
        return filtered_ideas

    def get_idea_details(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the full details of a specific level idea.

        Args:
            idea_id: The ID of the level idea to retrieve.

        Returns:
            A dictionary containing the idea's full details, or None if not found.
        """
        return self.ideas.get(idea_id)

    def _ensure_output_dir_exists(self, file_path: str) -> None:
        """Ensures the parent directory for an output file exists."""
        output_dir = os.path.dirname(file_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

# Example usage (for direct script execution)
if __name__ == '__main__':
    print("Demonstrating LevelDesignAssistant functionality...")

    assistant = LevelDesignAssistant()

    # Clean up previous state for a fresh demo
    if os.path.exists(LEVEL_DESIGN_IDEAS_FILE):
        os.remove(LEVEL_DESIGN_IDEAS_FILE)
    if os.path.exists(LAYOUT_SKETCHES_DIR):
        shutil.rmtree(LAYOUT_SKETCHES_DIR)
    assistant = LevelDesignAssistant() # Re-initialize to clear loaded state
    print(f"\nCleaned up {LEVEL_DESIGN_IDEAS_FILE} and {LAYOUT_SKETCHES_DIR} for fresh demo.")

    # --- Generate Level Idea ---
    print("\n--- Generating Level Idea 'ruins_puzzle_level' ---")
    try:
        idea1 = assistant.generate_level_idea(
            idea_id="ruins_puzzle_level",
            game_name="Adventure Quest",
            level_theme="ancient ruins",
            desired_elements=["puzzles", "exploration", "hidden treasures"]
        )
        print(json.dumps(idea1, indent=2))
    except Exception as e:
        print(f"Generate idea failed: {e}")

    # --- Suggest Challenges ---
    if idea1:
        print(f"\n--- Suggesting 'puzzle' Challenges for '{idea1['idea_id']}' ---")
        challenges = assistant.suggest_challenges(idea1['idea_id'], "puzzle")
        print(json.dumps(challenges, indent=2))

    # --- Create Layout Sketch ---
    if idea1:
        print(f"\n--- Creating Layout Sketch for '{idea1['idea_id']}' ---")
        output_sketch_path = os.path.join(LAYOUT_SKETCHES_DIR, f"{idea1['idea_id']}_sketch.txt")
        try:
            sketch_result = assistant.create_layout_sketch(idea1['idea_id'], output_sketch_path)
            print(json.dumps(sketch_result, indent=2))
            if os.path.exists(output_sketch_path):
                print(f"Sketch content:\n{open(output_sketch_path).read()}")
        except Exception as e:
            print(f"Create sketch failed: {e}")

    # --- List Ideas ---
    print("\n--- Listing All Ideas ---")
    all_ideas = assistant.list_ideas()
    print(json.dumps(all_ideas, indent=2))

    print("\n--- Listing Ideas for 'Adventure Quest' ---")
    game_ideas = assistant.list_ideas(game_name="Adventure Quest")
    print(json.dumps(game_ideas, indent=2))

    # --- Get Idea Details ---
    if idea1:
        print(f"\n--- Getting Details for '{idea1['idea_id']}' ---")
        details = assistant.get_idea_details(idea1['idea_id'])
        print(json.dumps(details, indent=2))

    # Clean up
    if os.path.exists(LEVEL_DESIGN_IDEAS_FILE):
        os.remove(LEVEL_DESIGN_IDEAS_FILE)
    if os.path.exists(LAYOUT_SKETCHES_DIR):
        shutil.rmtree(LAYOUT_SKETCHES_DIR)
    print(f"\nCleaned up all demo files and directories.")