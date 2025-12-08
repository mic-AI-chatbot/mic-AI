import logging
import random
import json
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simple knowledge base for quiz questions
QUIZ_DATA = {
    "history": [
        {"question": "Who was the first President of the United States?", "options": ["Abraham Lincoln", "George Washington", "Thomas Jefferson", "John Adams"], "correct_answer": "George Washington"},
        {"question": "In what year did World War II end?", "options": ["1942", "1945", "1950", "1939"], "correct_answer": "1945"},
        {"question": "Which ancient civilization built the pyramids?", "options": ["Roman", "Greek", "Egyptian", "Mayan"], "correct_answer": "Egyptian"},
        {"question": "Who discovered America in 1492?", "options": ["Vasco da Gama", "Ferdinand Magellan", "Christopher Columbus", "James Cook"], "correct_answer": "Christopher Columbus"},
        {"question": "What was the primary cause of the Cold War?", "options": ["Economic competition", "Ideological conflict", "Territorial disputes", "Religious differences"], "correct_answer": "Ideological conflict"}
    ],
    "science": [
        {"question": "What is the chemical symbol for Oxygen?", "options": ["O2", "Ox", "O", "Oz"], "correct_answer": "O"},
        {"question": "What planet is known as the Red Planet?", "options": ["Earth", "Jupiter", "Mars", "Venus"], "correct_answer": "Mars"},
        {"question": "What is the powerhouse of the cell?", "options": ["Nucleus", "Mitochondria", "Ribosome", "Cytoplasm"], "correct_answer": "Mitochondria"},
        {"question": "What force keeps planets in orbit around the sun?", "options": ["Magnetism", "Friction", "Gravity", "Centrifugal force"], "correct_answer": "Gravity"},
        {"question": "What is the hardest natural substance on Earth?", "options": ["Gold", "Iron", "Diamond", "Quartz"], "correct_answer": "Diamond"}
    ],
    "geography": [
        {"question": "What is the capital of Canada?", "options": ["Toronto", "Vancouver", "Ottawa", "Montreal"], "correct_answer": "Ottawa"},
        {"question": "Which river is the longest in the world?", "options": ["Amazon", "Mississippi", "Nile", "Yangtze"], "correct_answer": "Nile"},
        {"question": "What is the largest ocean on Earth?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "correct_answer": "Pacific"},
        {"question": "Which country is known as the Land of the Rising Sun?", "options": ["China", "South Korea", "Japan", "Thailand"], "correct_answer": "Japan"},
        {"question": "What is the highest mountain in Africa?", "options": ["Mount Kenya", "Mount Kilimanjaro", "Mount Elgon", "Mount Stanley"], "correct_answer": "Mount Kilimanjaro"}
    ]
}

class QuizGeneratorTool(BaseTool):
    """
    A tool that generates quizzes based on a specified topic and number of questions,
    providing multiple-choice questions with correct answers.
    """
    def __init__(self, tool_name: str = "QuizGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates quizzes based on topic and number of questions, providing multiple-choice questions with correct answers."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "enum": ["history", "science", "geography"], "description": "The topic of the quiz."},
                "num_questions": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5, "description": "The number of questions to generate."}
            },
            "required": ["topic"]
        }

    def execute(self, topic: str, num_questions: int = 5, **kwargs: Any) -> List[Dict[str, Any]]:
        """
        Generates a quiz with multiple-choice questions based on the specified topic.
        """
        if topic not in QUIZ_DATA:
            raise ValueError(f"Unsupported topic: {topic}. Choose from {list(QUIZ_DATA.keys())}.")
        if num_questions < 1 or num_questions > 10:
            raise ValueError("Number of questions must be between 1 and 10.")

        available_questions = QUIZ_DATA[topic]
        
        if num_questions > len(available_questions):
            logger.warning(f"Requested {num_questions} questions, but only {len(available_questions)} available for topic '{topic}'. Generating all available questions.")
            num_questions = len(available_questions)

        selected_questions = random.sample(available_questions, num_questions)  # nosec B311
        
        # Format questions for output
        quiz_questions = []
        for i, q_data in enumerate(selected_questions):
            quiz_questions.append({
                "question_number": i + 1,
                "question_text": q_data["question"],
                "options": q_data["options"],
                "correct_answer": q_data["correct_answer"]
            })
        
        return quiz_questions

if __name__ == '__main__':
    print("Demonstrating QuizGeneratorTool functionality...")
    
    quiz_generator = QuizGeneratorTool()
    
    try:
        # 1. Generate a science quiz with 3 questions
        print("\n--- Generating a Science Quiz (3 questions) ---")
        science_quiz = quiz_generator.execute(topic="science", num_questions=3)
        print(json.dumps(science_quiz, indent=2))

        # 2. Generate a history quiz with 5 questions
        print("\n--- Generating a History Quiz (5 questions) ---")
        history_quiz = quiz_generator.execute(topic="history", num_questions=5)
        print(json.dumps(history_quiz, indent=2))
        
        # 3. Generate a geography quiz with 2 questions
        print("\n--- Generating a Geography Quiz (2 questions) ---")
        geography_quiz = quiz_generator.execute(topic="geography", num_questions=2)
        print(json.dumps(geography_quiz, indent=2))

        # 4. Attempt to generate too many questions
        print("\n--- Attempting to generate 15 questions for History (should cap at 5) ---")
        large_history_quiz = quiz_generator.execute(topic="history", num_questions=15)
        print(json.dumps(large_history_quiz, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")