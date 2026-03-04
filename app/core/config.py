"""
Configuration file.

This loads environment variables from .env
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """
    Settings class holds all environment variables.
    """

    APP_NAME: str = os.getenv("APP_NAME")
    ENV: str = os.getenv("ENV")

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    AWS_ACCESS_KEY: str = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY: str = os.getenv("AWS_SECRET_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION")
    AWS_BUCKET: str = os.getenv("AWS_BUCKET")

    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 10485760))


settings = Settings()