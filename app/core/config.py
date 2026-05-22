# app/core/config.py
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI General Chatbot"

    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    @classmethod
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    SECRET_KEY: str = "********"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300

    # MongoDB Atlas Connection URI
    MONGODB_URI: str = "mongodb://localhost:27017/chatbot_db"

    # Google AI Studio
    GEMINI_API_KEY: str = "********"

    # Qdrant Cloud
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = "********"

    # LangSmith Tracing
    LANGCHAIN_TRACING_V2: bool = 'true'
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: str = "********"
    LANGSMITH_PROJECT: str = "pr-only-surround-27"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
