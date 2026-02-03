from sqlalchemy import Column, String, Integer, Numeric, SmallInteger, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from database import Base


class DespesaConsolidada(Base):
    __tablename__ = "despesas_consolidadas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registro_ans = Column(String(6), ForeignKey(
        "operadoras.registro_ans"), nullable=False)
    razao_social = Column(String(255), nullable=True)
    trimestre = Column(SmallInteger, nullable=False)
    ano = Column(SmallInteger, nullable=False)
    valor_despesas = Column(Numeric(15, 2), nullable=False)
    data_importacao = Column(TIMESTAMP, nullable=True)

    operadora = relationship("Operadora", back_populates="despesas")
