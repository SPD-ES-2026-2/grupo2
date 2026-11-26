"""
Camada de persistência relacional (CRUD).
- Integrante 3: Implementa inicialmente usando SQL puro (sqlite3) para o Desktop MVC.
- Integrante 4: Refatora para utilizar os modelos ORM do SQLAlchemy (models.py).
"""

import sqlite3
from src.persistencia.models import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --- PARTICIPANTE ---
def create_participante(nome: str, documento: str) -> int:
    raise NotImplementedError("Integrante 3/4: implementar inserção de participante.")


def read_participantes(limit: int = 100) -> list[dict]:
    raise NotImplementedError("Integrante 3/4: implementar leitura de participantes.")


def update_participante(id_participante: int, nome: str, documento: str) -> bool:
    raise NotImplementedError("Integrante 3/4: implementar atualização de participante.")


def delete_participante(id_participante: int) -> bool:
    raise NotImplementedError("Integrante 3/4: implementar remoção de participante.")


# --- PRODUTO ---
def create_produto(nome_produto: str, gtin: str, unidade: str) -> int:
    raise NotImplementedError("Integrante 3/4: implementar inserção de produto.")


def read_produtos(limit: int = 100) -> list[dict]:
    raise NotImplementedError("Integrante 3/4: implementar leitura de produtos.")


def update_produto(id_produto: int, nome_produto: str, gtin: str, unidade: str) -> bool:
    raise NotImplementedError("Integrante 3/4: implementar atualização de produto.")


def delete_produto(id_produto: int) -> bool:
    raise NotImplementedError("Integrante 3/4: implementar remoção de produto.")


# --- NOTA FISCAL E ITENS ---
def create_nota_fiscal(data_emissao: str, valor_total: float, id_vendedor: int, id_comprador: int, itens: list[dict]) -> int:
    raise NotImplementedError("Integrante 3/4: implementar inserção de nota fiscal e itens.")


def read_notas_fiscais(limit: int = 100) -> list[dict]:
    raise NotImplementedError("Integrante 3/4: implementar leitura de notas fiscais.")


def update_nota_fiscal(id_nota: int, data_emissao: str, valor_total: float) -> bool:
    raise NotImplementedError("Integrante 3/4: implementar atualização de nota fiscal.")


def delete_nota_fiscal(id_nota: int) -> bool:
    raise NotImplementedError("Integrante 3/4: implementar remoção de nota fiscal.")
