"""
Camada de acesso ao banco de dados.

Utiliza PostgreSQL através do Psycopg 3.
O banco utilizado em produção será o PostgreSQL hospedado no Supabase.
"""

from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from config.settings import settings


def get_connection():
    """
    Abre uma conexão com o PostgreSQL.

    As linhas retornadas pelas consultas serão dicionários,
    permitindo acessar os campos como:

        row["nome"]
    """

    if not settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não foi configurada. "
            "Configure a variável de ambiente com a URL do PostgreSQL."
        )

    return psycopg.connect(
        settings.DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=10,
        prepare_threshold=None
    )


@contextmanager
def get_db():
    """
    Context manager responsável por:

    - abrir conexão
    - realizar commit
    - realizar rollback em caso de erro
    - fechar conexão
    """

    conn = get_connection()

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()