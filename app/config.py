import os
from datetime import timedelta

from pydantic import AnyUrl, BaseSettings, Field, validator


class Settings(BaseSettings):
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DATABASE_URL: AnyUrl = Field(..., env="DATABASE_URL")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = {"development", "production", "testing"}
        if v not in allowed:
            raise ValueError(f"Invalid ENVIRONMENT '{v}'. Allowed values are {allowed}.")
        return v

    @validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    def validate_expire_minutes(cls, v):
        if v <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer.")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    if not hasattr(get_settings, "_instance"):
        get_settings._instance = Settings()
    return get_settings._instance


settings = get_settings()


def database_url() -> str:
    url = settings.DATABASE_URL
    return str(url)


def token_expiration_delta() -> timedelta:
    minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    return timedelta(minutes=minutes)