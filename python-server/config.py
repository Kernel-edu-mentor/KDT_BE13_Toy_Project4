from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent / ".env")
    )

    # Upstage API
    UPSTAGE_API_KEY: str

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # File Storage
    UPLOAD_DIR: str = "./uploads"

    # Cache
    CACHE_SIZE: int = 100

    # LangSmith
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "edumentor"


settings = Settings()
