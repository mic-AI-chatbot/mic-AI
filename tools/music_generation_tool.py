import logging
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MusicGeneratorSimulatorTool(BaseTool):
    """
    A tool that simulates music generation, creating textual descriptions of
    musical pieces based on genre, duration, and mood.
    """
    def __init__(self, tool_name: str = "MusicGeneratorSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates music generation, creating textual descriptions of pieces based on genre, duration, and mood."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "genre": {"type": "string", "enum": ["classical", "jazz", "electronic", "rock"], "description": "The genre of music to generate."},
                "duration_seconds": {"type": "integer", "minimum": 30, "maximum": 300, "description": "The desired duration of the music in seconds."},
                "mood": {"type": "string", "enum": ["upbeat", "calm", "energetic", "melancholy"], "description": "The desired mood of the music."}
            },
            "required": ["genre", "duration_seconds", "mood"]
        }

    def execute(self, genre: str, duration_seconds: int, mood: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Generates a textual representation of a musical piece based on genre, duration, and mood.
        """
        if duration_seconds < 30 or duration_seconds > 300:
            raise ValueError("Duration must be between 30 and 300 seconds.")

        composition = {
            "genre": genre.title(),
            "duration_seconds": duration_seconds,
            "mood": mood.title(),
            "tempo_bpm": 0,
            "key": "",
            "instrumentation": [],
            "sections": []
        }

        # Adjust based on mood
        if mood == "upbeat":
            composition["tempo_bpm"] = random.randint(120, 180)  # nosec B311
            composition["key"] = random.choice(["C Major", "G Major", "D Major"])  # nosec B311
        elif mood == "calm":
            composition["tempo_bpm"] = random.randint(60, 90)  # nosec B311
            composition["key"] = random.choice(["C Major", "G Major", "A Minor", "E Minor"])  # nosec B311
        elif mood == "energetic":
            composition["tempo_bpm"] = random.randint(140, 200)  # nosec B311
            composition["key"] = random.choice(["A Minor", "E Minor", "C Major"])  # nosec B311
        elif mood == "melancholy":
            composition["tempo_bpm"] = random.randint(50, 80)  # nosec B311
            composition["key"] = random.choice(["A Minor", "E Minor", "D Minor"])  # nosec B311

        # Genre-specific details
        if genre == "classical":
            composition["instrumentation"] = random.sample(["Piano", "Violin", "Cello", "Flute"], k=random.randint(1, 3))  # nosec B311
            composition["sections"] = [
                {"name": "Introduction", "description": f"A {mood} opening, setting the tone."},
                {"name": "Main Theme", "description": f"A {mood} melody, developing with variations."},
                {"name": "Bridge", "description": "Contrasting section, building tension or providing relief."},
                {"name": "Coda", "description": f"A {mood} conclusion, resolving the piece."}
            ]
        elif genre == "jazz":
            composition["instrumentation"] = random.sample(["Saxophone", "Trumpet", "Piano", "Double Bass", "Drums"], k=random.randint(2, 4))  # nosec B311
            composition["sections"] = [
                {"name": "Head", "description": f"The main {mood} melody, often played in unison."},
                {"name": "Improvisation", "description": f"An extended {mood} solo over the chord changes."},
                {"name": "Trading Fours", "description": "Agents exchange short, {mood} solos."},
                {"name": "Outro", "description": f"A {mood} fade-out or final chord."}
            ]
        elif genre == "electronic":
            composition["instrumentation"] = ["Synthesizer (Lead)", "Synthesizer (Pad)", "Drum Machine", "Bass Synth"]
            composition["sections"] = [
                {"name": "Intro (Build-up)", "description": f"A {mood} atmospheric build-up with evolving synths."},
                {"name": "Drop", "description": f"The main {mood} section with a driving beat and prominent lead."},
                {"name": "Breakdown", "description": f"A {mood} melodic interlude, often with filtered sounds."},
                {"name": "Outro", "description": f"A {mood} deconstruction of the main theme."}
            ]
        elif genre == "rock":
            composition["instrumentation"] = ["Electric Guitar (Lead)", "Electric Guitar (Rhythm)", "Bass Guitar", "Drums", "Vocals"]
            composition["sections"] = [
                {"name": "Intro (Riff)", "description": f"A {mood} guitar riff that sets the energy."},
                {"name": "Verse", "description": f"Vocal melody over a {mood} rhythm section."},
                {"name": "Chorus", "description": f"An {mood}, memorable hook with full instrumentation."},
                {"name": "Guitar Solo", "description": f"A {mood} and expressive guitar solo."},
                {"name": "Outro", "description": f"A {mood} repetition of the main riff or a powerful final chord."}
            ]
        else:
            raise ValueError(f"Unsupported genre: {genre}")

        return {
            "status": "success",
            "composed_piece": composition,
            "disclaimer": "This is a simulated musical composition. No actual audio is generated."
        }

if __name__ == '__main__':
    print("Demonstrating MusicGeneratorSimulatorTool functionality...")
    
    generator_tool = MusicGeneratorSimulatorTool()
    
    try:
        # 1. Generate an upbeat electronic track
        print("\n--- Generating an Upbeat Electronic track (150s) ---")
        result1 = generator_tool.execute(genre="electronic", duration_seconds=150, mood="upbeat")
        print(json.dumps(result1, indent=2))

        # 2. Generate a calm classical piece
        print("\n--- Generating a Calm Classical piece (200s) ---")
        result2 = generator_tool.execute(genre="classical", duration_seconds=200, mood="calm")
        print(json.dumps(result2, indent=2))
        
        # 3. Generate an energetic rock song
        print("\n--- Generating an Energetic Rock song (180s) ---")
        result3 = generator_tool.execute(genre="rock", duration_seconds=180, mood="energetic")
        print(json.dumps(result3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")