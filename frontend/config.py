from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    auth_url: str = "http://auth:8000"
    medias_url: str = "http://medias:8000"
    posts_url: str = "http://posts:8000"
    ads_url: str = "http://ads:8000"
    events_url: str = "http://events:8000"
    polls_url: str = "http://polls:8000"
    metrics_url: str = "http://metrics:8000"
    secret_key: str = "frontend-secret"
    
    class Config:
        env_file = ".env"

settings = Settings() 