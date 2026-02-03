from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.estatistica_service import EstatisticaService


router = APIRouter(prefix="/estatisticas", tags=["estatísticas"])


@router.get("")
def obter_estatisticas(db: Session = Depends(get_db)):
    return EstatisticaService.obter_estatisticas(db)
