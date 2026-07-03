from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./quizapp.db"
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: str = "http://localhost:5173"
    CORS_ORIGIN_REGEX: str = r"https://.*\.(vercel\.app|onrender\.com)$"
    CORS_ALLOW_CREDENTIALS: bool = True
    ADMIN_EMAIL: str = "admin@macquiz.com"
    ADMIN_PASSWORD: str = "admin123"
    AI_ENABLED: bool = True
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    @field_validator("*", mode="before")
    @classmethod
    def strip_string_values(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value
    
    @property
    def cors_origins_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if self.CORS_ALLOW_CREDENTIALS and "*" in origins:
            # Browsers block '*' with credentials; also unsafe.
            # Force the safer behavior while keeping the app running.
            print("⚠️  CORS_ORIGINS contains '*' while credentials are enabled; disabling credentials")
            self.CORS_ALLOW_CREDENTIALS = False
        return origins
    
    class Config:
        env_file = ".env"

settings = Settings()
