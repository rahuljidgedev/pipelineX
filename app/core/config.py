import os
from dotenv import load_dotenv
from pathlib import Path

# Get the absolute path to the project root (one level up from app/core/)
env_path = Path(__file__).parent.parent.parent

# Specifically check for files to avoid collision with .env directory
dotenv_file = env_path / ".env"
dotenv_local = env_path / ".env.local"

if dotenv_file.is_file():
    load_dotenv(dotenv_file)

if dotenv_local.is_file():
    load_dotenv(dotenv_local)

class Settings:
    # Use .strip() to handle any accidental spaces
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY").strip() if os.getenv("OPENAI_API_KEY") else None

settings = Settings()
