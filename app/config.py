import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    SECRET_KEY = os.environ.get("FORMVERSE_SECRET_KEY", "dev-secret-change-me")
    DATABASE_PATH = os.environ.get("FORMVERSE_DB_PATH", os.path.join(BASE_DIR, "formverse.db"))
    JWT_EXPIRY_HOURS = 24 * 7  # 7 days
    RESET_TOKEN_EXPIRY_MINUTES = 30
    CORS_ORIGINS = os.environ.get("FORMVERSE_CORS_ORIGINS", "*")
