from sqlalchemy import Column, String, Date
from sqlalchemy.orm import relationship
from database import Base


class Operadora(Base):
    __tablename__ = "operadoras"

    registro_ans = Column(String(6), primary_key=True)
    cnpj = Column(String(14), nullable=True)
    razao_social = Column(String(255), nullable=False)
    modalidade = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    data_cadastro = Column(Date, nullable=True)

    despesas = relationship("DespesaConsolidada", back_populates="operadora")
