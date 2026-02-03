from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class DespesaConsolidadaBase(BaseModel):
    registro_ans: str = Field(..., max_length=6)
    razao_social: Optional[str] = Field(None, max_length=255)
    trimestre: int = Field(..., ge=1, le=4, description="Trimestre (1-4)")
    ano: int = Field(..., ge=2000, le=2100, description="Ano")
    valor_despesas: Decimal = Field(..., ge=0,
                                    description="Valor das despesas")

    class Config:
        from_attributes = True


class DespesaConsolidadaResponse(DespesaConsolidadaBase):
    id: int


class DespesaConsolidadaWithOperadora(DespesaConsolidadaResponse):
    modalidade: Optional[str] = None
    uf_operadora: Optional[str] = None


class DespesaAgregadaBase(BaseModel):
    razao_social: str = Field(..., max_length=255)
    uf: str = Field(..., max_length=2)
    total_despesas: Decimal = Field(..., ge=0)
    media_despesas_trimestre: Decimal = Field(..., ge=0)
    desvio_padrao_despesas: Decimal = Field(..., ge=0)

    class Config:
        from_attributes = True


class DespesaAgregadaResponse(DespesaAgregadaBase):
    id: int


class CrescimentoResponse(BaseModel):
    registro_ans: str
    razao_social: str
    uf: Optional[str]
    modalidade: Optional[str]
    trimestre_inicial: int
    ano_inicial: int
    valor_inicial: Decimal
    trimestre_final: int
    ano_final: int
    valor_final: Decimal
    crescimento_percentual: Decimal
    variacao_absoluta: Decimal


class DespesaPorUFResponse(BaseModel):
    uf: str
    num_operadoras: int
    total_despesas: Decimal
    media_por_operadora: Decimal
    percentual_nacional: Decimal


class OperadoraAcimaDaMediaResponse(BaseModel):
    registro_ans: str
    razao_social: str
    uf: Optional[str]
    trimestres_acima_media: int
    total_trimestres: int
    media_despesas: Decimal
    percentual_acima: Decimal
