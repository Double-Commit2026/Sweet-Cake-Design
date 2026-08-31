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
    # python-dotenv é opcional em produção, onde as variáveis já vêm
    # definidas pelo ambiente de hospedagem.
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # Caminho do arquivo do banco SQLite.
    # (os.getenv só usa o default quando a variável está AUSENTE; se ela
    # existir mas vier vazia — como pode acontecer num .env.example copiado
    # sem preencher — tratamos como "não configurada" também.)
    DATABASE_PATH = os.getenv("DATABASE_PATH") or str(BASE_DIR / "database" / "sweetcake.db")

    # Número oficial de WhatsApp da Sweet Cake (formato: 5591985396256).
    # Usado apenas para montar o link "https://wa.me/<numero>" no front-end.
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER") or ""

    # Origem do front-end autorizada a consumir a API (CORS).
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN") or "*"

    # development | production
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV != "production"

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-troque-em-producao")


settings = Settings()
