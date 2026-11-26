"""
Middleware integrador: lê os dados brutos do SQLite (db_relacional), normaliza os campos
não padronizados e indexa no Elasticsearch sem gerar duplicatas.
- Integrante 2: Carga inicial após subir o container Docker.
- Integrante 7: Regras completas de saneamento e prevenção de duplicidade (id_nota como _id).
"""

import re
import sqlite3
from src.persistencia.models import DB_PATH
from src.persistencia.odm import NotaFiscalDoc, conectar_elastic


def limpar_documento(doc: str) -> tuple[str, str]:
    """Remove máscaras/prefixos e retorna (documento_limpo, tipo_pessoa)."""
    digitos = re.sub(r"\D", "", doc or "")
    if len(digitos) <= 11:
        return digitos.zfill(11), "PF"
    return digitos.zfill(14), "PJ"


def sincronizar_relacional_para_elastic() -> None:
    conectar_elastic()
    NotaFiscalDoc.init()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # TODO (Integrante 2 e 7):
    # 1. Consultar nota_fiscal fazendo JOIN com participante (vendedor/comprador) e item_nota + produto.
    # 2. Normalizar nome, documento, gtin, quantidade e valor_unitario.
    # 3. Salvar usando meta={'id': id_nota} no NotaFiscalDoc para evitar duplicatas ao reexecutar.
    conn.close()


if __name__ == "__main__":
    sincronizar_relacional_para_elastic()
