from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    APP_NAME: str = 'HRMS Backend API'
    APP_VERSION: str = '1.0.0'
    DEBUG: bool = True
    PORT: int = 8000

    DATABASE_URL: str = 'postgresql+psycopg2://postgres:postgres@localhost:5432/hrms'

    #JWT secret key, should be replaced with a secure value in production
    JWT_SECRET_KEY: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = 'http://localhost:3000,http://127.0.0.1:3000'

    OFFICE_START_HOUR: int = 10
    OFFICE_START_MINUTE: int = 0
    LATE_AFTER_HOUR: int = 10
    LATE_AFTER_MINUTE: int = 15
    FULL_DAY_HOURS: float = 8.0
    HALF_DAY_MIN_HOURS: float = 4.0
    OVERTIME_MAX_HOURS_PER_DAY: float = 6.0

    LATE_DEDUCTION_PER_MARK: float = 250.0
    LEAVE_DEDUCTION_PER_DAY: float = 500.0
    OVERTIME_HOURLY_RATE_MULTIPLIER: float = 1.5

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]


settings = Settings()
