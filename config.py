import os
import re
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote_plus


def carregar_env():
    # Carrega variáveis locais.
    env_path = Path(__file__).with_name(".env")

    if not env_path.exists():
        return

    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()

        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)
        valor = valor.strip().strip('"').strip("'")
        os.environ.setdefault(chave.strip(), valor)


carregar_env()


class Config:
    # Centraliza as configurações de conexão, sessão e segurança.
    SECRET_KEY = os.getenv("SECRET_KEY", "chave-dev")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ecommerce_db")
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    INACTIVITY_TIMEOUT_SECONDS = 900

    # Valida o nome do banco.
    if not re.fullmatch(r"[A-Za-z0-9_]+", MYSQL_DATABASE):
        raise ValueError("MYSQL_DATABASE deve conter apenas letras, números e underscore.")

    _USER = quote_plus(MYSQL_USER)
    _PASSWORD = quote_plus(MYSQL_PASSWORD)

    MYSQL_SERVER_URL = (
        f"mysql+mysqlconnector://{_USER}:{_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/"
        "?charset=utf8mb4"
    )

    DATABASE_URL = (
        f"mysql+mysqlconnector://{_USER}:{_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/"
        f"{MYSQL_DATABASE}?charset=utf8mb4"
    )
