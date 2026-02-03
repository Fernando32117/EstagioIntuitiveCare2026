from sqlalchemy import Column, String, Integer, Numeric, TIMESTAMP
from database import Base


class DespesaAgregada(Base):
    __tablename__ = "despesas_agregadas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    razao_social = Column(String(255), nullable=False)
    uf = Column(String(2), nullable=False)
    total_despesas = Column(Numeric(15, 2), nullable=False)
    media_despesas_trimestre = Column(Numeric(15, 2), nullable=False)
    desvio_padrao_despesas = Column(Numeric(15, 2), nullable=False)
    data_importacao = Column(TIMESTAMP, nullable=True)
