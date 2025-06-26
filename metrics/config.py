from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_database: str = "blog_metrics"
    mongodb_username: str = "admin"
    mongodb_password: str = "password"
    # Collections for each microservice
    users_collection: str = "users"
    posts_collection: str = "posts"
    ads_collection: str = "ads"
    events_collection: str = "events"
    polls_collection: str = "polls"
    # Databases for each microservice
    users_db: str = "blog_auth"
    posts_db: str = "blog_posts"
    ads_db: str = "blog_ads"
    events_db: str = "blog_events"
    polls_db: str = "blog_polls"
    
    class Config:
        env_file = ".env"

settings = Settings() 