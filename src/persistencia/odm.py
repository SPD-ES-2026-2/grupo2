"""
Camada de persistência orientada a documentos (Elasticsearch).
- Integrante 5: Cria as funções CRUD (create, read, update, delete) para a API REST.
- Integrante 4: Garante o uso da biblioteca ODM (elasticsearch-dsl) com Document e InnerDoc.
"""

from elasticsearch_dsl import Date, Document, Float, InnerDoc, Keyword, Nested, Text, connections

ES_HOST = "http://localhost:9200"
INDEX_NAME = "notas_fiscais_auditoria"


def conectar_elastic(host: str = ES_HOST) -> None:
    connections.create_connection(hosts=[host])


class ParticipanteDoc(InnerDoc):
    id_participante = Keyword()
    nome = Text(fields={"raw": Keyword()})
    documento = Keyword()
    tipo_pessoa = Keyword()  # 'PF' ou 'PJ' deduzido pelo tamanho do documento


class ItemNotaDoc(InnerDoc):
    id_produto = Keyword()
    nome_produto = Text(fields={"raw": Keyword()})
    gtin = Keyword()
    unidade = Keyword()
    quantidade = Float()
    valor_unitario = Float()
    valor_total = Float()


class NotaFiscalDoc(Document):
    id_nota = Keyword()
    data_emissao = Date()
    valor_total = Float()
    vendedor = Nested(ParticipanteDoc)
    comprador = Nested(ParticipanteDoc)
    itens = Nested(ItemNotaDoc)

    class Index:
        name = INDEX_NAME


def create_nota_doc(dados: dict) -> str:
    raise NotImplementedError("Integrante 4/5: implementar criação de documento no Elasticsearch.")


def read_notas_doc(filtros: dict | None = None, limit: int = 100) -> list[dict]:
    raise NotImplementedError("Integrante 4/5: implementar consulta de documentos no Elasticsearch.")


def update_nota_doc(id_nota: str, campos: dict) -> bool:
    raise NotImplementedError("Integrante 4/5: implementar atualização de documento no Elasticsearch.")


def delete_nota_doc(id_nota: str) -> bool:
    raise NotImplementedError("Integrante 4/5: implementar remoção de documento no Elasticsearch.")
