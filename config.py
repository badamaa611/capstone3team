import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "capstone-secret-2025")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///capstone.db"  # локал дээр SQLite
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    # When true, the app will not attempt to write results to Google Sheets.
    MOCK_GOOGLE_SHEETS = os.getenv("MOCK_GOOGLE_SHEETS", "false").lower() in ("1", "true", "yes")