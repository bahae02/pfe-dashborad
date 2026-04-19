import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE", 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = {"xlsx", "xls", "csv"}
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

def get_config():
    """Get config based on environment"""
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
