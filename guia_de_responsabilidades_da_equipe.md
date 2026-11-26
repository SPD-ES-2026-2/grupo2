# Guia de Execução e Responsabilidades da Equipe

Este documento define o escopo técnico, os arquivos de responsabilidade exclusiva, a ordem de dependências e as regras de negócio de cada integrante no projeto **Auditoria de Notas Fiscais**.

> **Regra de Ouro de Versionamento (Git):** Cada integrante deve atuar **exclusivamente** nos arquivos designados à sua função para evitar conflitos de *merge*. Crie uma branch própria a partir da `main` (ex.: `feat/integrante-3-desktop`) e abra um *Pull Request* ao finalizar.

---

## 1. Visão Geral da Arquitetura e Ordem de Execução

Para que ninguém fique bloqueado, o desenvolvimento ocorre em **3 ondas**:

* **Onda 1 (Base e Infraestrutura):** Integrante 1 (Banco SQLite) $\rightarrow$ Integrante 2 (Container Elasticsearch + Carga inicial).
* **Onda 2 (Desenvolvimento Paralelo):** Integrante 3 (SQL puro + Desktop MVC), Integrante 5 (Queries ES + API REST), Integrante 7 (Middleware Integrador) e Integrante 8 (Busca Auditoria + RapidFuzz).
* **Onda 3 (Refatoração ORM/ODM e Validação):** Integrante 4 (Migração de `orm.py` e `odm.py` para SQLAlchemy e `elasticsearch-dsl`) e Integrante 6 (Testes Unitários com `pytest`).

---

## 2. Detalhamento por Integrante

### Integrante 1 — Banco de Dados Relacional (Concluído)
* **Arquivos:** `database/db_relacional` e `database/scripts/*`
* **Responsabilidades:**
  * Criar e popular o banco SQLite chamado exatamente **`db_relacional`** (sem extensão) antes do início das demais tarefas.
  * Garantir a estrutura física das 4 tabelas (`participante`, `produto`, `nota_fiscal`, `item_nota`) e a injeção controlada de inconsistências nas colunas suscetíveis a erro (`participante.nome`, `participante.documento`, `produto.nome_produto` e `produto.gtin`).

---

### Integrante 2 — Infraestrutura Docker e Carga Inicial no Elasticsearch
* **Arquivos:** `infra/docker-compose.yml` e `src/integracao/integrador.py`
* **Responsabilidades:**
  1. **Subir o Elasticsearch:** Configurar e executar o `infra/docker-compose.yml` para disponibilizar o Elasticsearch na rede local (`http://localhost:9200`).
  2. **Carga Inicial:** Assim que o `db_relacional` estiver disponível em `database/`, executar `src/integracao/integrador.py` para realizar a primeira indexação dos dados no Elasticsearch, utilizando as classes/funções de `src/persistencia/odm.py`.
  3. **Documentar o Mapping:** Garantir que a estrutura de mapeamento (`NotaFiscalDoc`, `ParticipanteDoc` e `ItemNotaDoc` definidos em `src/persistencia/odm.py`) esteja explicitamente documentada no `README.md` para consulta dos demais integrantes.
* **Comandos de referência:**
  ```bash
  docker compose -f infra/docker-compose.yml up -d
  python -m src.integracao.integrador
  ```

---

### Integrante 3 — Interface Desktop MVC e Camada CRUD Relacional (SQL Puro)
* **Arquivos:** `src/persistencia/orm.py` e `src/aplicacao/desktop_mvc.py`
* **Responsabilidades:**
  1. **Camada de Persistência (`src/persistencia/orm.py`):** Implementar as funções `create`, `read`, `update` e `delete` para `Participante`, `Produto`, `NotaFiscal` e `ItemNota`.
     * **Restrição obrigatória:** Nesta etapa, **não utilize ORM (SQLAlchemy)**. Escreva cada consulta em **SQL puro** usando `sqlite3` (a conversão para ORM será feita posteriormente pelo Integrante 4).
  2. **Interface Desktop (`src/aplicacao/desktop_mvc.py`):** Construir uma aplicação desktop (Tkinter ou PyQt) seguindo rigorosamente o padrão arquitetural **MVC (Model-View-Controller)** que consuma exclusivamente as funções de `src/persistencia/orm.py` para realizar o CRUD no `db_relacional`.

---

### Integrante 4 — Migração para ORM (SQLAlchemy) e ODM (`elasticsearch-dsl`)
* **Arquivos:** `src/persistencia/orm.py` e `src/persistencia/odm.py`
* **Dependência:** Atua após os Integrantes 3 e 5 implementarem as operações CRUD iniciais com SQL e queries em *hardcode*.
* **Responsabilidades:**
  1. **Refatoração Relacional (`src/persistencia/orm.py`):** Substituir todos os comandos SQL puros (`sqlite3`) pelas operações equivalentes usando o **ORM SQLAlchemy** (`SessionLocal` e as classes `Participante`, `Produto`, `NotaFiscal`, `ItemNota` já mapeadas em `src/persistencia/models.py`).
  2. **Refatoração Documental (`src/persistencia/odm.py`):** Substituir todas as queries brutas do Elasticsearch pelas operações equivalentes usando o **ODM `elasticsearch-dsl`** (`NotaFiscalDoc`, `Search`, `.save()`, `.update()`, `.delete()`).
  3. **Contrato de Interface:** Manter exatamente os mesmos nomes de funções, parâmetros e tipos de retorno em `orm.py` e `odm.py` para não quebrar a interface Desktop (Integrante 3), a API REST (Integrante 5) nem os testes (Integrante 6).

---

### Integrante 5 — Backend API REST JSON e Camada CRUD Documental
* **Arquivos:** `src/persistencia/odm.py` e `src/aplicacao/api_rest.py`
* **Responsabilidades:**
  1. **Camada de Persistência Documental (`src/persistencia/odm.py`):** Implementar as funções CRUD (`create_nota_doc`, `read_notas_doc`, `update_nota_doc`, `delete_nota_doc`) escrevendo inicialmente as queries de busca, inserção, atualização e remoção no Elasticsearch (que serão posteriormente convertidas para ODM pelo Integrante 4).
  2. **API REST JSON (`src/aplicacao/api_rest.py`):** Criar uma API HTTP (ex.: FastAPI) acessível na rede local que exponha endpoints REST (`POST`, `GET`, `PUT`, `DELETE`) para manipulação das notas fiscais no Elasticsearch, utilizando **obrigatoriamente** as funções de `src/persistencia/odm.py`.

---

### Integrante 6 — Testes Unitários das Camadas de Persistência
* **Arquivo:** `tests/test_persistencia.py`
* **Responsabilidades:**
  1. Escrever uma suíte de testes unitários automatizados utilizando **`pytest`** para comprovar que `src/persistencia/orm.py` e `src/persistencia/odm.py` respeitam a modelagem e as restrições do banco.
  2. Como os contratos das funções (`create`, `read`, `update`, `delete`) já estão definidos em `orm.py` e `odm.py`, os testes podem ser escritos imediatamente e executados tanto sobre a versão SQL/Query pura quanto após a refatoração ORM/ODM do Integrante 4.
  3. **Cenários mínimos obrigatórios:**
     * Ciclo completo (`create` $\rightarrow$ `read` $\rightarrow$ `update` $\rightarrow$ `delete`) para entidades relacionais e documentos.
     * Validação de chaves estrangeiras (`id_vendedor`, `id_comprador` e chave composta `(id_nota, id_produto)` em `item_nota`).
     * Conformidade de tipos e obrigatoriedade de campos (`NOT NULL`).
* **Comando de execução:**
  ```bash
  pytest
  ```

---

### Integrante 7 — Middleware Integrador e Saneamento de Dados
* **Arquivo:** `src/integracao/integrador.py`
* **Responsabilidades:**
  1. Completar o pipeline de sincronização bidirecional/incremental entre o banco relacional (`db_relacional`) e o Elasticsearch.
  2. **Normalização obrigatória dos dados sujos:**
     * **Documentos (`documento`):** Remover máscaras/prefixos (`CNPJ:`, `CPF:`, pontos, traços, barras), preencher zeros à esquerda e deduzir o tipo de pessoa (`11` dígitos = `PF`; `14` dígitos = `PJ`).
     * **Produtos (`gtin`):** Validar tamanho (`8`, `12`, `13` ou `14` dígitos) e limpar espaços/caracteres inválidos.
     * **Textos (`nome` e `nome_produto`):** Padronizar caixa, espaços extras e acentuação.
     * **Numéricos e Datas:** Converter `quantidade` e `valor_unitario` (armazenados como `VARCHAR` no SQLite) para `float` e padronizar `data_emissao`.
  3. **Prevenção de duplicatas:** Utilizar o `id_nota` como identificador único (`_id`) no Elasticsearch para que reexecuções do integrador atualizem o documento existente em vez de duplicá-lo.

---

### Integrante 8 — Interface de Busca do Auditor (`RapidFuzz` + Filtros + Exportação)
* **Arquivo:** `src/aplicacao/busca_auditoria.py`
* **Objetivo:** Responder às perguntas-chave da auditoria: **"Quem"** (vendedor/comprador), **"Quanto"** (valor total) e **"Quando"** (data da transação).
* **Responsabilidades:**
  * **Etapa A — Busca por Similaridade e Filtro Temporal:**
    1. Fornecer um campo de entrada onde o auditor digita um termo de busca.
    2. Consultar os documentos no Elasticsearch via cláusula `match` e aplicar `from rapidfuzz import process` utilizando **`_weighted_scorer`** para ranquear e retornar apenas os termos mais semelhantes.
    3. **Colunas de busca configuráveis:** A busca deve ocorrer exclusivamente nas colunas de texto curto: `nome` (`participante`), `documento` (`participante`), `nome_produto` (`produto`) e `gtin` (`produto`). Mantenha essa lista de campos em uma constante no topo do arquivo para fácil adição/remoção.
    4. **Filtro de data opcional:** Permitir informar um intervalo entre data inicial $x$ e data final $y$. Caso $x = y$, filtrar apenas os documentos daquela data exata.
  * **Etapa B — Refinamento, Resumo e Download:**
    1. Exibir na tela os termos/itens recuperados na Etapa A para que o auditor possa **desmarcar/remover** aqueles que não lhe interessam.
    2. Ao clicar em **Avançar**, buscar no Elasticsearch todos os documentos compatíveis com os itens mantidos (respeitando o filtro de data $x..y$, caso tenha sido preenchido).
    3. Exibir na interface uma **string de resumo** contendo:
       * Lista dos **participantes** presentes nos documentos retornados;
       * **Valor total gasto** (soma dos valores dos documentos recuperados);
       * **Intervalo (range) de datas** em que os documentos ocorreram.
    4. Disponibilizar um botão para **download** dos documentos filtrados (ex.: formato `.json` ou `.csv`).

---

## 3. Referência Rápida do Esquema Relacional (`db_relacional`)

| Tabela | Colunas | Observações de Qualidade |
| :--- | :--- | :--- |
| **`participante`** | `id_participante` (PK), `nome` (VARCHAR 255), `documento` (VARCHAR 30) | Alta incidência de erros em `nome`; baixa/média em `documento`. |
| **`produto`** | `id_produto` (PK), `nome_produto` (VARCHAR 100), `gtin` (VARCHAR 20), `unidade` (VARCHAR 20) | Alta incidência de erros em `nome_produto`; baixa em `gtin` (8, 12, 13 ou 14 dígitos); `unidade` sem erros. |
| **`nota_fiscal`** | `id_nota` (PK), `data_emissao` (DATE), `valor_total` (FLOAT), `id_vendedor` (FK), `id_comprador` (FK) | Todos os campos sem erros. `id_vendedor` e `id_comprador` referenciam `participante`. |
| **`item_nota`** | `id_nota` (PK/FK), `id_produto` (PK/FK), `quantidade` (VARCHAR 50), `valor_unitario` (VARCHAR 50), `valor_total` (FLOAT) | Todos os campos sem erros. Resolve a relação N:N entre `nota_fiscal` e `produto`. |