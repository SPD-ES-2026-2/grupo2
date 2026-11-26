"""
Definição da conexão SQLite e das entidades relacionais (SQLAlchemy).
Esquema físico conforme planejamento:
- participante (id_participante, nome, documento)
- produto (id_produto, nome_produto, gtin, unidade)
- nota_fiscal (id_nota, data_emissao, valor_total, id_vendedor, id_comprador)
- item_nota (id_nota, id_produto, quantidade, valor_unitario, valor_total)
"""

from pathlib import Path
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "database" / "db_relacional"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Participante(Base):
    __tablename__ = "participante"

    id_participante = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255), nullable=False)
    documento = Column(String(30), nullable=False)


class Produto(Base):
    __tablename__ = "produto"

    id_produto = Column(Integer, primary_key=True, autoincrement=True)
    nome_produto = Column(String(100))
    gtin = Column(String(20))
    unidade = Column(String(20), nullable=False)


class NotaFiscal(Base):
    __tablename__ = "nota_fiscal"

    id_nota = Column(Integer, primary_key=True, autoincrement=True)
    data_emissao = Column(Date, nullable=False)
    valor_total = Column(Float, nullable=False)
    id_vendedor = Column(Integer, ForeignKey("participante.id_participante"), nullable=False)
    id_comprador = Column(Integer, ForeignKey("participante.id_participante"), nullable=False)

    vendedor = relationship("Participante", foreign_keys=[id_vendedor])
    comprador = relationship("Participante", foreign_keys=[id_comprador])
    itens = relationship("ItemNota", back_populates="nota", cascade="all, delete-orphan")


class ItemNota(Base):
    __tablename__ = "item_nota"

    id_nota = Column(Integer, ForeignKey("nota_fiscal.id_nota"), primary_key=True)
    id_produto = Column(Integer, ForeignKey("produto.id_produto"), primary_key=True)
    quantidade = Column(String(50), nullable=False)
    valor_unitario = Column(String(50), nullable=False)
    valor_total = Column(Float, nullable=False)

    nota = relationship("NotaFiscal", back_populates="itens")
    produto = relationship("Produto")
