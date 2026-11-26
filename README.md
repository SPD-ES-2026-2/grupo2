# Auditoria de Notas Fiscais — Software para Persistência de Dados

Sistema híbrido de persistência (SQLite + Elasticsearch) para auditoria e busca por similaridade em notas fiscais com dados não padronizados.

## Estrutura do Projeto

- `database/`: Banco SQLite (`db_relacional`) e scripts auxiliares de carga (`limpar_json.py`, `popular_banco.py`, `verificar_duplicatas.py`).
- `infra/`: Arquivos de infraestrutura (`docker-compose.yml`) para subir o Elasticsearch.
- `src/persistencia/`: Camadas de acesso a dados (`models.py`, `orm.py`, `odm.py`).
- `src/integracao/`: Middleware de normalização e carga SQLite -> Elasticsearch (`integrador.py`).
- `src/aplicacao/`: Interfaces de usuário e API (`desktop_mvc.py`, `api_rest.py`, `busca_auditoria.py`).
- `tests/`: Testes unitários automatizados com `pytest` (`test_persistencia.py`).

## Divisão por Integrante

| Arquivo | Responsável | Papel |
| :--- | :--- | :--- |
| `database/db_relacional` | Deivison Oliveira da Silva | Criação e carga inicial do banco SQLite |
| `infra/docker-compose.yml` + `src/integracao/integrador.py` | Integrante 2 | Subir Elasticsearch e carga inicial |
| `src/persistencia/orm.py` + `src/aplicacao/desktop_mvc.py` | Integrante 3 | CRUD relacional e interface Desktop MVC |
| `src/persistencia/orm.py` + `src/persistencia/odm.py` | Integrante 4 | Migração de SQL/queries para SQLAlchemy e elasticsearch-dsl |
| `src/persistencia/odm.py` + `src/aplicacao/api_rest.py` | Integrante 5 | CRUD documental e API REST JSON |
| `tests/test_persistencia.py` | Integrante 6 | Testes unitários de conformidade da persistência |
| `src/integracao/integrador.py` | Integrante 7 | Normalização (CPF/CNPJ, GTIN, textos) sem duplicatas |
| `src/aplicacao/busca_auditoria.py` | Integrante 8 | Busca com Elasticsearch + `rapidfuzz` + filtro de data e exportação |
