from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "FocusFlow Brain"
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    port: int = int(os.getenv("PORT", 8000))
    host: str = os.getenv("HOST", "0.0.0.0")

    class Config:
        env_file = ".env"

settings = Settings()
