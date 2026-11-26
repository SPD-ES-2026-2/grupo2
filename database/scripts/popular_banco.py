import json
import os
import random
import re
import sqlite3
import unicodedata
from datetime import date, timedelta

# ==============================================================================
# CONFIGURAÇÕES GERAIS
# ==============================================================================
ARQUIVO_JSON = "resultado_distintos_limpo.json"
NOME_BANCO = "db_relacional"  # Nome exato exigido pelo planejamento_2.pdf
QTD_NOTAS_FISCAIS = 15000     # Gera ~45.000 itens de nota coerentes
SEED = 42

random.seed(SEED)


# ==============================================================================
# 1. GERADORES DE DOCUMENTOS E CÓDIGOS MATEMATICAMENTE VÁLIDOS
# ==============================================================================
def gerar_cpf_valido() -> str:
    n = [random.randint(0, 9) for _ in range(9)]
    if len(set(n)) == 1:
        n[-1] = (n[-1] + 1) % 10
    d1 = (sum(x * y for x, y in zip(n, range(10, 1, -1))) * 10) % 11
    d1 = 0 if d1 == 10 else d1
    n.append(d1)
    d2 = (sum(x * y for x, y in zip(n, range(11, 1, -1))) * 10) % 11
    d2 = 0 if d2 == 10 else d2
    n.append(d2)
    s = "".join(map(str, n))
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"


def gerar_cnpj_valido() -> str:
    n = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    r1 = sum(x * y for x, y in zip(n, pesos1)) % 11
    d1 = 0 if r1 < 2 else 11 - r1
    n.append(d1)
    r2 = sum(x * y for x, y in zip(n, pesos2)) % 11
    d2 = 0 if r2 < 2 else 11 - r2
    n.append(d2)
    s = "".join(map(str, n))
    return f"{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}"


def gerar_gtin_valido(tamanho: int = 13) -> str:
    """Gera GTIN válido de 8, 12, 13 ou 14 dígitos com dígito verificador GS1."""
    assert tamanho in (8, 12, 13, 14)
    corpo = [random.randint(1 if i == 0 else 0, 9) for i in range(tamanho - 1)]
    soma = 0
    for idx, digito in enumerate(reversed(corpo)):
        soma += digito * (3 if idx % 2 == 0 else 1)
    dv = (10 - (soma % 10)) % 10
    return "".join(map(str, corpo)) + str(dv)


# ==============================================================================
# 2. INJEÇÃO DE ERROS CONTROLADA (CONFORME REGRAS DO PLANEJAMENTO)
# ==============================================================================
def remover_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def aplicar_ruido_texto(texto: str, probabilidade: float = 0.40) -> str:
    """Injeta erros comuns de digitação/padronização em nomes."""
    if random.random() > probabilidade or len(texto) < 5:
        return texto

    t = texto
    tipo_erro = random.choice([
        "abreviar",
        "sem_acento",
        "espacos_extras",
        "pontuacao",
        "typo_teclado",
        "caixa_mista",
    ])

    if tipo_erro == "abreviar":
        subs = [
            (r"\bPREFEITURA MUNICIPAL\b", "PREF. MUN."),
            (r"\bPREFEITURA\b", "PREF"),
            (r"\bSECRETARIA\b", "SEC."),
            (r"\bMUNICIPIO\b", "MUN."),
            (r"\bLIMITADA\b", "LTDA"),
            (r"\bLTDA\b", "LTDA."),
            (r"\bCOMERCIO\b", "COM."),
            (r"\bSERVICOS\b", "SERV."),
            (r"\bDISTRIBUIDORA\b", "DIST."),
            (r"\bENGENHARIA\b", "ENG."),
            (r"\bHOSPITAL\b", "HOSP."),
            (r"\bLABORATORIO\b", "LAB."),
            (r"\bINFORMATICA\b", "INFO."),
            (r"\bTECNOLOGIA\b", "TEC."),
            (r"\bMEDICAMENTOS\b", "MEDIC."),
        ]
        for padrao, rep in subs:
            novo = re.sub(padrao, rep, t, flags=re.IGNORECASE)
            if novo != t:
                t = novo
                break
    elif tipo_erro == "sem_acento":
        t = remover_acentos(t)
    elif tipo_erro == "espacos_extras":
        partes = t.split(" ")
        if len(partes) > 1:
            idx = random.randint(0, len(partes) - 2)
            partes[idx] += " "
            t = " ".join(partes)
        t = f" {t} "
    elif tipo_erro == "pontuacao":
        t = re.sub(r"[.\-/]", " ", t)
    elif tipo_erro == "typo_teclado":
        pos = random.randint(1, len(t) - 2)
        if t[pos].isalpha() and t[pos + 1].isalpha():
            lista = list(t)
            lista[pos], lista[pos + 1] = lista[pos + 1], lista[pos]
            t = "".join(lista)
    elif tipo_erro == "caixa_mista":
        t = t.lower() if random.random() < 0.5 else t.title()

    return t[:250]


def aplicar_ruido_documento(doc: str, probabilidade: float = 0.18) -> str:
    """Injeta falhas de formatação e digitação (baixa/média incidência) no CPF/CNPJ."""
    if random.random() > probabilidade:
        return doc

    apenas_digitos = re.sub(r"\D", "", doc)
    tipo_erro = random.choice([
        "sem_mascara",
        "prefixo_sujo",
        "pontuacao_errada",
        "espacos_no_meio",
        "zeros_esquerda_removidos",
        "faltar_caractere",
        "adicionar_caractere",
    ])

    if tipo_erro == "sem_mascara":
        return apenas_digitos
    elif tipo_erro == "prefixo_sujo":
        rotulo = "CNPJ: " if len(apenas_digitos) == 14 else "CPF: "
        return rotulo + (doc if random.random() < 0.5 else apenas_digitos)
    elif tipo_erro == "pontuacao_errada":
        return doc.replace(".", "-").replace("/", ".")
    elif tipo_erro == "espacos_no_meio":
        return doc.replace(".", " ").replace("-", " ").replace("/", " ")
    elif tipo_erro == "zeros_esquerda_removidos":
        return apenas_digitos.lstrip("0") or apenas_digitos
    elif tipo_erro == "faltar_caractere":
        # Remove 1 caractere aleatório (pode ser pontuação ou dígito)
        if len(doc) > 5:
            idx = random.randint(0, len(doc) - 1)
            return doc[:idx] + doc[idx + 1:]
    elif tipo_erro == "adicionar_caractere":
        # Insere 1 caractere extra (dígito duplicado, espaço ou pontuação solta)
        idx = random.randint(0, len(doc))
        char_extra = random.choice([str(random.randint(0, 9)), " ", ".", "-"])
        return (doc[:idx] + char_extra + doc[idx:])[:30]

    return doc


def aplicar_ruido_gtin(gtin: str, probabilidade: float = 0.06) -> str:
    """Baixa incidência de erros (~6%) no GTIN conforme especificado."""
    if random.random() > probabilidade:
        return gtin

    tipo = random.choice(["digito_invalido", "tamanho_errado", "com_espaco"])
    if tipo == "digito_invalido":
        ultimo = (int(gtin[-1]) + 3) % 10
        return gtin[:-1] + str(ultimo)
    elif tipo == "tamanho_errado":
        return gtin[:-2]
    else:
        return f"{gtin[:4]} {gtin[4:]}"


# ==============================================================================
# 3. CLASSIFICAÇÃO SEMÂNTICA DOS PARTICIPANTES DO JSON
# ==============================================================================
KW_ORGAO_PUBLICO = (
    "SECRETARIA", "FUNDO", "PREFEITURA", "MUNICIPIO", "TRIBUNAL",
    "MINISTERIO", "CAMARA", "ASSEMBLEIA", "GOVERNO", "ESTADO DE",
    "INSTITUTO", "FUNDACAO", "AGENCIA", "SUPERINTENDENCIA", "AUTARQUIA",
    "DEFENSORIA", "PROCURADORIA", "CONSELHO", "CORPO DE BOMBEIROS", "POLICIA"
)

KW_SETORES = {
    "SAUDE": ("HOSPITAL", "CLINICA", "LABORATORIO", "MEDICAMENTO", "FARMAC", "DROGARIA", "ODONTO", "MEDICO", "SAUDE", "CIRURG"),
    "OBRAS": ("CONSTRUTORA", "ENGENHARIA", "PAVIMENTACAO", "TERRAPLENAGEM", "OBRAS", "CONSTRUCAO", "CIMENTO", "ASFALTO", "ARQUITETURA"),
    "TI": ("INFORMATICA", "TECNOLOGIA", "SISTEMAS", "TELECOM", "SOFTWARE", "DADOS", "COMPUTADOR", "ELETRONIC", "REDES"),
    "COMBUSTIVEL": ("POSTO", "COMBUSTIVEL", "COMBUSTIVEIS", "PETROLEO", "AUTO POSTO", "DERIVADOS", "LUBRIFICANTE", "GAS"),
    "ALIMENTOS": ("SUPERMERCADO", "ALIMENTO", "PANIFICADORA", "ACOUGUE", "HORTIFRUTI", "BEBIDAS", "RESTAURANTE", "REFEICOES", "MERCEARIA"),
    "PAPELARIA": ("PAPELARIA", "GRAFICA", "LIVRARIA", "ESCRITORIO", "IMPRESSOS", "EMBALAGENS"),
}

KW_PESSOA_JURIDICA = (
    "LTDA", "S/A", "S.A", "ME", "EPP", "EIRELI", "COMERCIO", "SERVICOS",
    "INDUSTRIA", "DISTRIBUIDORA", "TRANSPORTES", "COOPERATIVA", "ASSOCIACAO",
    "EMPRESA", "COMERCIAL", "AGROPECUARIA", "HOTEL", "LOCADORA", "CONSULTORIA"
)


def classificar_participante(nome: str) -> tuple[str, str]:
    """Retorna (papel_preferencial, setor)."""
    upper = remover_acentos(nome.upper())

    if any(k in upper for k in KW_ORGAO_PUBLICO):
        return ("ORGAO_PUBLICO", "PUBLICO")

    for setor, palavras in KW_SETORES.items():
        if any(k in upper for k in palavras):
            return ("FORNECEDOR_PJ", setor)

    if any(k in upper for k in KW_PESSOA_JURIDICA):
        return ("FORNECEDOR_PJ", "GERAL")

    return ("PESSOA_FISICA", "GERAL")


# ==============================================================================
# 4. CATÁLOGO BASE DE PRODUTOS POR SETOR (UNIDADE SEM ERROS)
# ==============================================================================
CATALOGO_PRODUTOS = {
    "SAUDE": [
        ("Dipirona Sódica 500mg Caixa c/ 30 Comprimidos", "CX", (8.50, 22.00)),
        ("Amoxicilina 500mg Cápsulas Caixa c/ 21", "CX", (15.00, 38.00)),
        ("Luva Cirúrgica Estéril Tamanho 7.5 Caixa c/ 50 Pares", "CX", (45.00, 95.00)),
        ("Seringa Descartável 10ml sem Agulha Pacote c/ 100", "PCT", (28.00, 62.00)),
        ("Soro Fisiológico 0,9% Frasco 500ml", "UN", (4.20, 9.80)),
        ("Máscara Cirúrgica Tripla Camada Caixa c/ 50", "CX", (12.00, 29.00)),
        ("Álcool Etílico 70% Hospitalar Galão 5 Litros", "UN", (24.00, 48.00)),
        ("Cateter Intravenoso 22G Caixa c/ 100 Unidades", "CX", (85.00, 160.00)),
    ],
    "OBRAS": [
        ("Cimento Portland CP II-E-32 Saco 50kg", "UN", (32.00, 46.00)),
        ("Brita Graduada Simples para Pavimentação", "M3", (95.00, 145.00)),
        ("Areia Média Lavada para Construção", "M3", (85.00, 130.00)),
        ("Concreto Betuminoso Usinado a Quente (CBUQ)", "TON", (480.00, 720.00)),
        ("Vergalhão Aço CA-50 10mm Barra 12m", "UN", (42.00, 68.00)),
        ("Tubo PVC Esgoto 100mm Barra 6 Metros", "UN", (55.00, 89.00)),
        ("Tinta Acrílica Fosca Branco Neve Lata 18L", "UN", (190.00, 340.00)),
        ("Piso Intertravado de Concreto 8cm", "M2", (48.00, 78.00)),
    ],
    "TI": [
        ("Notebook Corporativo Core i5 16GB RAM SSD 512GB", "UN", (3400.00, 5200.00)),
        ("Monitor LED 24 Polegadas Full HD HDMI", "UN", (680.00, 1150.00)),
        ("Switch Gerenciável Gigabit 24 Portas Rack", "UN", (1400.00, 2900.00)),
        ("Cabo de Rede UTP Cat6 Caixa 305 Metros", "CX", (450.00, 790.00)),
        ("Nobreak Senoidal 1500VA Bivolt", "UN", (890.00, 1650.00)),
        ("HD SSD NVMe 1TB Leitura 3500MB/s", "UN", (380.00, 640.00)),
        ("Impressora Multifuncional Laser Monocromática", "UN", (1500.00, 2800.00)),
        ("Licença Anual Suíte de Escritório Corporativa", "UN", (420.00, 890.00)),
    ],
    "COMBUSTIVEL": [
        ("Gasolina Comum Automotiva", "L", (5.49, 6.39)),
        ("Óleo Diesel S10", "L", (5.69, 6.59)),
        ("Etanol Hidratado Combustível", "L", (3.69, 4.49)),
        ("Óleo Lubrificante Sintético 5W30 Frasco 1L", "UN", (34.00, 58.00)),
        ("Agente Redutor Líquido Automotivo ARLA 32 Balde 20L", "UN", (75.00, 125.00)),
    ],
    "ALIMENTOS": [
        ("Arroz Branco Tipo 1 Pacote 5kg", "PCT", (22.00, 32.00)),
        ("Feijão Carioca Tipo 1 Pacote 1kg", "PCT", (6.50, 10.50)),
        ("Óleo de Soja Refinado Pet 900ml", "UN", (5.80, 8.90)),
        ("Café Torrado e Moído Tradicional Pacote 500g", "PCT", (14.00, 24.00)),
        ("Açúcar Cristal Especial Pacote 5kg", "PCT", (16.00, 23.00)),
        ("Leite Integral UHT Caixa 1 Litro", "UN", (4.30, 6.20)),
        ("Carne Bovina Patinho Resfriada", "KG", (32.00, 46.00)),
    ],
    "PAPELARIA": [
        ("Papel Sulfite A4 75g Caixa c/ 10 Resmas (5000 Folhas)", "CX", (240.00, 320.00)),
        ("Caneta Esferográfica Azul Caixa c/ 50 Unidades", "CX", (32.00, 54.00)),
        ("Pasta Suspensa Kraft Plastificada Caixa c/ 50", "CX", (68.00, 110.00)),
        ("Toner Compatível Preto Alto Rendimento", "UN", (65.00, 145.00)),
        ("Envelope Pardo A4 240x340mm Caixa c/ 250", "CX", (75.00, 125.00)),
    ],
    "GERAL": [
        ("Ar Condicionado Split Inverter 12000 BTUs", "UN", (1850.00, 2750.00)),
        ("Cadeira Giratória Ergonômica Escritório NR17", "UN", (580.00, 1150.00)),
        ("Água Mineral sem Gás Galão 20 Litros", "UN", (11.00, 18.00)),
        ("Detergente Neutro Concentrado Galão 5 Litros", "UN", (18.00, 34.00)),
        ("Pneu Radial 175/70 R14 Passeio", "UN", (310.00, 460.00)),
        ("Extintor de Incêndio ABC 6kg com Suporte", "UN", (115.00, 185.00)),
    ],
}


# ==============================================================================
# 5. CRIAÇÃO DO BANCO E POPULAÇÃO DOS DADOS
# ==============================================================================
def criar_tabelas(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.executescript(
        """
        PRAGMA foreign_keys = ON;

        DROP TABLE IF EXISTS item_nota;
        DROP TABLE IF EXISTS nota_fiscal;
        DROP TABLE IF EXISTS produto;
        DROP TABLE IF EXISTS participante;

        CREATE TABLE participante (
            id_participante INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VARCHAR(255) NOT NULL,
            documento VARCHAR(30) NOT NULL
        );

        CREATE TABLE produto (
            id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_produto VARCHAR(100),
            gtin VARCHAR(20),
            unidade VARCHAR(20) NOT NULL
        );

        CREATE TABLE nota_fiscal (
            id_nota INTEGER PRIMARY KEY AUTOINCREMENT,
            data_emissao DATE NOT NULL,
            valor_total FLOAT NOT NULL,
            id_vendedor INT NOT NULL,
            id_comprador INT NOT NULL,
            FOREIGN KEY (id_vendedor) REFERENCES participante (id_participante),
            FOREIGN KEY (id_comprador) REFERENCES participante (id_participante)
        );

        CREATE TABLE item_nota (
            id_nota INT NOT NULL,
            id_produto INT NOT NULL,
            quantidade VARCHAR(50) NOT NULL,
            valor_unitario VARCHAR(50) NOT NULL,
            valor_total FLOAT NOT NULL,
            PRIMARY KEY (id_nota, id_produto),
            FOREIGN KEY (id_nota) REFERENCES nota_fiscal (id_nota),
            FOREIGN KEY (id_produto) REFERENCES produto (id_produto)
        );
        """
    )
    conn.commit()


def popular_banco() -> None:
    if not os.path.exists(ARQUIVO_JSON):
        raise FileNotFoundError(
            f"Arquivo '{ARQUIVO_JSON}' não encontrado no diretório atual: {os.getcwd()}"
        )

    with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
        dados_json = json.load(f)

    nomes_distintos = dados_json.get("valores_distintos", [])
    print(f"Registros carregados de {ARQUIVO_JSON}: {len(nomes_distintos)}")

    conn = sqlite3.connect(NOME_BANCO)
    criar_tabelas(conn)
    cursor = conn.cursor()

    # --------------------------------------------------------------------------
    # A) POPULAR PARTICIPANTES (30.393 originais + ~2.500 variações com ruído)
    # --------------------------------------------------------------------------
    registros_participantes = []
    metadados_participantes = []  # (id_participante, papel, setor)

    for idx, nome_original in enumerate(nomes_distintos, start=1):
        papel, setor = classificar_participante(nome_original)
        doc_base = (
            gerar_cpf_valido()
            if papel == "PESSOA_FISICA"
            else gerar_cnpj_valido()
        )
        nome_final = aplicar_ruido_texto(nome_original, probabilidade=0.35)
        doc_final = aplicar_ruido_documento(doc_base, probabilidade=0.40)

        registros_participantes.append((nome_final, doc_final))
        metadados_participantes.append((idx, papel, setor, nome_original, doc_base))

    # Gera duplicatas/variações sujas de ~2.500 entidades reais para testar fuzzy matching
    amostra_duplicatas = random.sample(metadados_participantes, k=min(2500, len(metadados_participantes)))
    proximo_id = len(registros_participantes) + 1
    for _, papel, setor, nome_orig, doc_base in amostra_duplicatas:
        nome_variado = aplicar_ruido_texto(nome_orig, probabilidade=0.95)
        doc_variado = aplicar_ruido_documento(doc_base, probabilidade=0.90)
        registros_participantes.append((nome_variado, doc_variado))
        metadados_participantes.append((proximo_id, papel, setor, nome_orig, doc_base))
        proximo_id += 1

    cursor.executemany(
        "INSERT INTO participante (nome, documento) VALUES (?, ?)",
        registros_participantes,
    )
    print(f"Participantes inseridos: {len(registros_participantes)}")

    # --------------------------------------------------------------------------
    # B) POPULAR PRODUTOS (Catálogo base + variações de cadastro com ruído)
    # --------------------------------------------------------------------------
    registros_produtos = []
    produtos_por_setor: dict[str, list[tuple[int, tuple[float, float]]]] = {
        setor: [] for setor in CATALOGO_PRODUTOS
    }

    id_prod_atual = 1
    for setor, lista_itens in CATALOGO_PRODUTOS.items():
        for nome_base, unidade, faixa_preco in lista_itens:
            gtin_base = gerar_gtin_valido(random.choice([8, 12, 13, 14]))
            # Versão principal + 4 variações de digitação por produto
            for versao in range(5):
                nome_prod = (
                    nome_base
                    if versao == 0
                    else aplicar_ruido_texto(nome_base, probabilidade=0.90)
                )[:100]
                gtin_prod = aplicar_ruido_gtin(gtin_base, probabilidade=0.06)
                registros_produtos.append((nome_prod, gtin_prod, unidade))
                produtos_por_setor[setor].append((id_prod_atual, faixa_preco))
                id_prod_atual += 1

    cursor.executemany(
        "INSERT INTO produto (nome_produto, gtin, unidade) VALUES (?, ?, ?)",
        registros_produtos,
    )
    print(f"Produtos inseridos: {len(registros_produtos)}")

    # --------------------------------------------------------------------------
    # C) POPULAR NOTAS FISCAIS E ITENS DE NOTA (COERÊNCIA SEMÂNTICA E MATEMÁTICA)
    # --------------------------------------------------------------------------
    compradores = [m for m in metadados_participantes if m[1] in ("ORGAO_PUBLICO", "FORNECEDOR_PJ")]
    vendedores = [m for m in metadados_participantes if m[1] in ("FORNECEDOR_PJ", "PESSOA_FISICA")]

    data_inicio = date(2023, 1, 1)
    dias_intervalo = (date(2026, 11, 25) - data_inicio).days

    registros_notas = []
    registros_itens = []

    for id_nota in range(1, QTD_NOTAS_FISCAIS + 1):
        vendedor = random.choice(vendedores)
        comprador = random.choice(compradores)
        while comprador[0] == vendedor[0]:
            comprador = random.choice(compradores)

        id_vendedor = vendedor[0]
        setor_vendedor = vendedor[2]
        id_comprador = comprador[0]

        data_emissao = (data_inicio + timedelta(days=random.randint(0, dias_intervalo))).isoformat()

        # Escolhe produtos compatíveis com o setor do vendedor sem duplicar IDs
        pool_produtos = list(produtos_por_setor.get(setor_vendedor, []))
        if setor_vendedor != "GERAL" and (not pool_produtos or random.random() < 0.30):
            pool_produtos.extend(produtos_por_setor["GERAL"])

        qtd_itens_nota = random.randint(1, min(6, len(pool_produtos)))
        produtos_escolhidos = random.sample(pool_produtos, k=qtd_itens_nota)

        total_nota = 0.0
        for id_produto, (preco_min, preco_max) in produtos_escolhidos:
            qtd_num = random.randint(1, 50)
            valor_unit_num = round(random.uniform(preco_min, preco_max), 2)
            valor_item_total = round(qtd_num * valor_unit_num, 2)
            total_nota = round(total_nota + valor_item_total, 2)

            # quantidade e valor_unitario são VARCHAR(50) SEM ERROS; valor_total é FLOAT SEM ERROS
            registros_itens.append((
                id_nota,
                id_produto,
                str(qtd_num),
                f"{valor_unit_num:.2f}",
                valor_item_total,
            ))

        registros_notas.append((
            data_emissao,
            total_nota,
            id_vendedor,
            id_comprador,
        ))

    cursor.executemany(
        """
        INSERT INTO nota_fiscal (data_emissao, valor_total, id_vendedor, id_comprador)
        VALUES (?, ?, ?, ?)
        """,
        registros_notas,
    )
    cursor.executemany(
        """
        INSERT INTO item_nota (id_nota, id_produto, quantidade, valor_unitario, valor_total)
        VALUES (?, ?, ?, ?, ?)
        """,
        registros_itens,
    )

    conn.commit()
    conn.close()
    print(f"Notas fiscais inseridas: {len(registros_notas)}")
    print(f"Itens de nota inseridos: {len(registros_itens)}")
    print(f"Banco SQLite '{NOME_BANCO}' criado e populado com sucesso!")


if __name__ == "__main__":
    popular_banco()