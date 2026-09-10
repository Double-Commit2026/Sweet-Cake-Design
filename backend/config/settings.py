"""
Configurações centrais da aplicação.

Todo valor sensível ou específico de ambiente (número de WhatsApp, caminho
do banco, origem liberada para o front-end) vem de variáveis de ambiente,
nunca fica hardcoded no código-fonte. Ver .env.example para a lista
completa de variáveis esperadas.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Settings:
    #URL de conexão com o PostgreSQL/SupaBase
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Número oficial de WhatsApp da Sweet Cake.
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER") or ""

    # Origem do front-end autorizada a consumir a API (CORS).
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN")

    # development | production
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV != "production"

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-troque-em-producao")


settings = Settings()
