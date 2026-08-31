"""
Camada de acesso ao banco de dados.

Usa SQLite por simplicidade (ideal para o volume de dados de um catálogo
de confeitaria). Se o negócio crescer e precisar de Postgres/MySQL, só
esta função `get_connection` (e a string de conexão) precisam mudar —
o resto da aplicação não sabe qual banco está por trás.
"""
import sqlite3
from contextlib import contextmanager

from config.settings import settings


def get_connection():
    """Abre uma conexão com o banco, com linhas acessíveis por nome de coluna."""
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    """Context manager para uso em rotas: garante commit/rollback e fechamento."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('delivery', 'encomenda')),
    descricao TEXT,
    ordem INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id INTEGER NOT NULL REFERENCES categories(id),
    nome TEXT NOT NULL,
    descricao TEXT,
    tipo_preco TEXT NOT NULL CHECK (tipo_preco IN ('fixo', 'configuravel')),
    preco_base INTEGER,              -- em centavos; usado quando tipo_preco = 'fixo'
    preco_promocional INTEGER,       -- em centavos; opcional, para itens "de/por"
    imagem_url TEXT,
    disponivel INTEGER NOT NULL DEFAULT 1,
    destaque INTEGER NOT NULL DEFAULT 0,
    ordem INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS product_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    nome TEXT NOT NULL,              -- ex: "20cm - 3 camadas / 2 recheios"
    preco_base INTEGER NOT NULL,     -- em centavos
    serve_pessoas INTEGER,
    disponivel INTEGER NOT NULL DEFAULT 1,
    ordem INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS option_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id),
    nome TEXT NOT NULL,              -- ex: "Massa", "Recheio", "Decoração"
    obrigatorio INTEGER NOT NULL DEFAULT 1,
    ordem INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    option_group_id INTEGER NOT NULL REFERENCES option_groups(id),
    nome TEXT NOT NULL,
    preco_adicional INTEGER NOT NULL DEFAULT 0,  -- em centavos
    requer_orcamento INTEGER NOT NULL DEFAULT 0,
    disponivel INTEGER NOT NULL DEFAULT 1,
    ordem INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS store_info (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
"""


def init_db():
    """Cria as tabelas caso ainda não existam. Não apaga dados existentes."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
