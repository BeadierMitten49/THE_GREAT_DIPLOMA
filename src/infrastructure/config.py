from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str

    # Auth
    secret_key: str
    algorithm: str = "HS256"

    # Telegram
    telegram_bot_token: str = ""


settings = Settings()
