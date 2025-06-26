from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_database: str = "blog_auth"
    mongodb_collection: str = "users"
    mongodb_username: str = "admin"
    mongodb_password: str = "password"
    
    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings() 