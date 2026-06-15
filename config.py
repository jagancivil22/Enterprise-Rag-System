from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    secret_key: str = "your-secret-key"
    openai_api_key: str = ""
    use_local_llm: bool = True
    chroma_persist_dir: str = "./chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model_name: str = "google/flan-t5-small"
    chunk_size: int = 500
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()