from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gmail
    gmail_address: str = ""
    gmail_app_password: str = ""

    # IMAP/SMTP
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587

    # App
    poll_interval_seconds: int = 300
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    database_url: str = "sqlite:///./translator.db"
    secret_key: str = "change-me-in-production"

    # Gemini
    gemini_api_key: str = ""

    # Whitelist senders
    allowed_senders: str = "content@clawshorns.com,meinguyen133@gmail.com"

    # Google OAuth
    google_client_id: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
