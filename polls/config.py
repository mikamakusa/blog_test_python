from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_database: str = "blog_polls"
    mongodb_collection: str = "polls"
    mongodb_username: str = "admin"
    mongodb_password: str = "password"
    
    class Config:
        env_file = ".env"

settings = Settings() 