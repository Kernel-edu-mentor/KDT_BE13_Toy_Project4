from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Upstage API
    UPSTAGE_API_KEY: str

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # File Storage
    UPLOAD_DIR: str = "./uploads"

    # Cache
    CACHE_SIZE: int = 100

    class Config:
        env_file = ".env"

settings = Settings()
