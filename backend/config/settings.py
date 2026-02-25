import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    assets_root: str = "assets_root"
    duplicate_threshold: float = 0.90
    similar_threshold: float = 0.75
    api_host: str = "127.0.0.1"
    api_port: int = 17831

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
