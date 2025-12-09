import os

# --- Database Settings ---
DB_TYPE = os.environ.get("DB_TYPE", "postgres") # "sqlite" or "postgres"
DB_NAME = os.environ.get("DB_NAME", "mic_db")
DB_USER = os.environ.get("DB_USER", "mic_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "mic_password")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")


# --- API Keys and Paths ---
# These should be set as environment variables in your production environment.
# The application will fail to start if these are not set.

try:
    # For gemini, google search, etc.
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    GOOGLE_CSE_ID = os.environ["GOOGLE_CSE_ID"]
    # For bing search
    BING_API_KEY = os.environ.get("BING_API_KEY")
    # For currency conversion in payments
    EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY") # Get from https://www.exchangerate-api.com/
    # For signing JWTs
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
except KeyError as e:
    raise RuntimeError(f"Missing required environment variable: {e}. Please set this in your .env file or system environment.") from e

# --- JWT Settings ---
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Path to the local GGUF model file
# This can be optional if you don't intend to use a local Llama model.
LLAMA_MODEL_PATH = os.environ.get("LLAMA_MODEL_PATH") 

# --- Subscription Tiers and Limits ---
# It's safe to define these directly in the code.
SUBSCRIPTION_TIERS = {
    "Free": {
        "description": "Basic access to mic features.",
        "price_usd": 0,
        "web_search_limit": 5,
        "llm_query_limit": 10,
        "file_processing_limit": -1,
        "allowed_tools": [
            "web_search",
            "joke_generator",
            "math_problem_solver",
            "summarize",
            "translate",
            "unit_converter",
        ]
    },
    "Premium": {
        "description": "Enhanced access with higher limits.",
        "price_usd": 10,
        "web_search_limit": 50,
        "llm_query_limit": 100,
        "file_processing_limit": 10,
        "allowed_tools": [
            "web_search",
            "joke_generator",
            "math_problem_solver",
            "summarize",
            "translate",
            "unit_converter",
            "generate_code",
            "explain_code",
            "refactor_code",
            "generate_unit_test",
            "generate_image",
            "analyze_image",
            "data_analysis",
            "generate_chart",
            "storyboard_generator",
            "logo_designer",
            "interactive_tutorial_generator",
            "language_tutor",
            "game_master",
            "personal_health_monitor",
            "virtual_interior_designer",
            "ai_art_collaborator",
            "emotionally_resonant_music_composer",
        ]
    },
    "Gold": {
        "description": "Unlimited access to all mic features.",
        "price_usd": 25,
        "web_search_limit": -1,
        "llm_query_limit": -1,
        "file_processing_limit": -1,
        "allowed_tools": ["*"] # All tools
    }
}

DEFAULT_SUBSCRIPTION_TIER = "Free"
