"""
Integrante 8: Interface de busca do auditor.
- Ponto A: Busca por termo (nome, documento, nome_produto, gtin) no Elastic + rapidfuzz (_weighted_scorer) + filtro opcional de data (x a y).
- Ponto B: Seleção dos itens filtrados, exibição de resumo (participantes, soma total, range de datas) e download dos documentos.
"""
