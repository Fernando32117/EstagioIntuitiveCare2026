from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal

from database import get_db
from services.despesa_service import DespesaService
from schemas import (
    DespesaAgregadaResponse,
    CrescimentoResponse,
    DespesaPorUFResponse,
    OperadoraAcimaDaMediaResponse
)


router = APIRouter(prefix="/despesas", tags=["despesas"])


@router.get("/agregadas", response_model=List[DespesaAgregadaResponse])
def listar_despesas_agregadas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    uf: Optional[str] = Query(
        None, max_length=2, description="Filtrar por UF"),
    min_despesas: Optional[Decimal] = Query(
        None, ge=0, description="Valor mínimo de despesas"),
    db: Session = Depends(get_db)
):
    return DespesaService.listar_agregadas(db, skip, limit, uf, min_despesas)


@router.get("/top-ufs", response_model=List[DespesaPorUFResponse])
def top_ufs_por_despesas(
    limit: int = Query(5, ge=1, le=50, description="Número de UFs"),
    db: Session = Depends(get_db)
):
    return DespesaService.top_ufs_por_despesas(db, limit)


@router.get("/crescimento", response_model=List[CrescimentoResponse])
def top_crescimento_operadoras(
    limit: int = Query(5, ge=1, le=50, description="Número de operadoras"),
    db: Session = Depends(get_db)
):
    return DespesaService.top_crescimento_operadoras(db, limit)


@router.get("/acima-media", response_model=List[OperadoraAcimaDaMediaResponse])
def operadoras_acima_da_media(
    min_trimestres: int = Query(
        2, ge=1, le=4, description="Mínimo de trimestres acima da média"),
    limit: int = Query(10, ge=1, le=100, description="Número de operadoras"),
    db: Session = Depends(get_db)
):
    return DespesaService.operadoras_acima_da_media(db, min_trimestres, limit)
