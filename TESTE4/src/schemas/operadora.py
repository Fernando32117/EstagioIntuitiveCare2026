from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class OperadoraBase(BaseModel):
    registro_ans: str = Field(..., max_length=6,
                              description="Registro ANS da operadora")
    cnpj: Optional[str] = Field(
        None, max_length=14, description="CNPJ da operadora")
    razao_social: str = Field(..., max_length=255,
                              description="Razão social da operadora")
    modalidade: Optional[str] = Field(
        None, max_length=100, description="Modalidade da operadora")
    uf: Optional[str] = Field(
        None, max_length=2, description="UF da operadora")

    class Config:
        from_attributes = True


class OperadoraResponse(OperadoraBase):
    data_cadastro: Optional[date] = Field(None, description="Data de cadastro")
