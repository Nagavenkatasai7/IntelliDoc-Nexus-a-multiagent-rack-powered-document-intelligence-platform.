from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "IntelliDoc Nexus"
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    version: str = "0.1.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    access_token_expire_minutes: int = 60

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://intellidoc:intellidoc@db:5432/intellidoc",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql://intellidoc:intellidoc@db:5432/intellidoc",
        alias="DATABASE_URL_SYNC",
    )

    # Redis
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # Claude / Anthropic
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    claude_model: str = "claude-sonnet-4-20250514"

    # Pinecone
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_index_name: str = Field(
        default="intellidoc-index", alias="PINECONE_INDEX_NAME"
    )
    pinecone_environment: str = Field(default="us-east-1", alias="PINECONE_ENVIRONMENT")

    # AWS S3
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    s3_bucket_name: str = Field(
        default="intellidoc-documents", alias="S3_BUCKET_NAME"
    )

    # Document Processing
    max_upload_size_mb: int = 100
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Celery
    celery_broker_url: str = Field(default="redis://redis:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(
        default="redis://redis:6379/2", alias="CELERY_RESULT_BACKEND"
    )

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
