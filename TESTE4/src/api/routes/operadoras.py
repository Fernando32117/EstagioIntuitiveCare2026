from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from typing import List

from database import get_db
from services.operadora_service import OperadoraService
from services.despesa_service import DespesaService


router = APIRouter(prefix="/operadoras", tags=["operadoras"])


class PaginatedResponse(BaseModel):
    data: List[dict]
    total: int
    page: int
    limit: int
    total_pages: int


@router.get("")
def listar_operadoras(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    search: Optional[str] = Query(
        None, description="Buscar por razão social, CNPJ ou registro ANS"),
    db: Session = Depends(get_db)
):
    return OperadoraService.listar_paginado(db, page, limit, search)


@router.get("/{cnpj}")
def buscar_operadora(
    cnpj: str,
    db: Session = Depends(get_db)
):
    operadora = OperadoraService.buscar_por_cnpj_ou_registro(db, cnpj)

    if not operadora:
        raise HTTPException(
            status_code=404,
            detail=f"Operadora com CNPJ/Registro ANS {cnpj} não encontrada"
        )

    return operadora


@router.get("/{cnpj}/despesas")
def listar_despesas_operadora(
    cnpj: str,
    db: Session = Depends(get_db)
):
    resultado = DespesaService.buscar_historico_operadora(db, cnpj)

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"Operadora com CNPJ/Registro ANS {cnpj} não encontrada"
        )

    return resultado
