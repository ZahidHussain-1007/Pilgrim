from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

ROOT_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

class RagSettings(BaseSettings):
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama3-8b-8192")
    qdrant_url: str = Field(default="")
    qdrant_api_key: str = Field(default="")
    redis_url: str = Field(default="")

    model_config = SettingsConfigDict(env_file=str(ROOT_ENV_PATH), extra="ignore")

settings = RagSettings()
