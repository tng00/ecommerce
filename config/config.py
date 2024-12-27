from yookassa import Configuration, Payment, Refund
import uuid

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY")
    YOOKASSA_ACCOUNT_ID: str = os.getenv("YOOKASSA_ACCOUNT_ID")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY")
    CHECKS_DIR: str = os.getenv("CHECKS_DIR")

    # Проверяем, чтобы все ключевые переменные были загружены
    @staticmethod
    def validate():
        required_keys = [
            "DATABASE_URL",
            "SESSION_SECRET_KEY",
            "YOOKASSA_ACCOUNT_ID",
            "YOOKASSA_SECRET_KEY",
            "CHECKS_DIR",
        ]
        for key in required_keys:
            if not os.getenv(key):
                raise EnvironmentError(f"Missing required environment variable: {key}")

# Инициализируем настройки
settings = Settings()
settings.validate()
