from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # AWS Configuration
    aws_access_key_id: str = Field(..., alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(..., alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("us-east-1", alias="AWS_REGION")
    aws_bucket_name: str = Field(..., alias="AWS_BUCKET_NAME")

    # Database Configuration
    database_url: str = Field(
        "postgresql+psycopg2://postgres:postgres@localhost/tech_rag",
        alias="DATABASE_URL"
    )

    # Security Configuration
    secret_key: str = Field(..., alias="SECRET_KEY")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Application Configuration
    api_prefix: str = Field("/api/v1", alias="API_PREFIX")
    debug: bool = Field(False, alias="DEBUG")

    # OpenAI Configuration
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    # Pinecone Configuration
    pinecone_api_key: str = Field(..., alias="PINECONE_API_KEY")
    pinecone_environment: str = Field(..., alias="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(..., alias="PINECONE_INDEX_NAME")

    # LangChain Configuration
    langchain_tracing_v2: bool = Field(False, alias="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str = Field(..., alias="LANGCHAIN_ENDPOINT")
    langchain_api_key: str = Field(..., alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(..., alias="LANGCHAIN_PROJECT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
