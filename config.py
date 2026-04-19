"""
Конфигурация бота. Переменные загружаются из .env (файл в .cursorignore).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "bot.db"))).resolve()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
CLINIC_PHONE = os.getenv("CLINIC_PHONE", "+79001234567").strip()
SITE_URL = os.getenv("SITE_URL", "https://ulybka-plus.example.com").strip()

# Демо-режим: разрешить переключение ролей по /patient и /owner. Для продакшена выставить False.
DEMO_SWITCH_ENABLED = os.getenv("DEMO_SWITCH_ENABLED", "true").strip().lower() in ("1", "true", "yes")
