from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MinIO Configuration
    minio_host: str = "localhost"
    minio_port: int = 9000
    minio_bucket: str = "blog-medias"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings() 