from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    db_echo: bool = False

    db_url: str = Field(
        default="postgresql+asyncpg://youruser:yourpassword@db:5432/main_db",
        validation_alias="DB_URL"
    )


settings = Settings()