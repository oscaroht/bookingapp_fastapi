from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import os

load_dotenv()


class Settings(BaseSettings):
    JWT_ENCRYPTION_ALGORITHM: str = os.getenv('JWT_ENCRYPTION_ALGORITHM')
    JWT_TOKEN_EXPIRY_MINUTES: int = int(os.getenv('JWT_TOKEN_EXPIRY_MINUTES'))  # returns str so cast to int
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    DB_USER: str = os.getenv('DB_USER'),
    DB_PASSWORD: str = os.getenv('DB_PASSWORD'),
    DB_HOST: str = os.getenv('DB_HOST'),
    DB_PORT: str = os.getenv('DB_PORT'),
    DB_NAME: str = os.getenv('DB_NAME'),


settings = Settings()
