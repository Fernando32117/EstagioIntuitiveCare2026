from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict
from decimal import Decimal
from datetime import datetime
import time

from models import Operadora, DespesaConsolidada


class EstatisticaService:
    _cache = {"data": None, "timestamp": None}
    CACHE_TTL_SECONDS = 300

    @classmethod
    def obter_estatisticas(cls, db: Session, force_refresh: bool = False) -> Dict:
        if not force_refresh and cls._cache["data"] is not None:
            if cls._cache["timestamp"]:
                age = time.time() - cls._cache["timestamp"]
                if age < cls.CACHE_TTL_SECONDS:
                    return cls._cache["data"]

        resultado = cls._calcular_estatisticas(db)

        cls._cache["data"] = resultado
        cls._cache["timestamp"] = time.time()

        return resultado

    @staticmethod
    def _calcular_estatisticas(db: Session) -> Dict:

        total_despesas = db.query(
            func.sum(DespesaConsolidada.valor_despesas)
        ).scalar() or Decimal(0)

        media_despesas = db.query(
            func.avg(DespesaConsolidada.valor_despesas)
        ).scalar() or Decimal(0)

        total_operadoras = db.query(
            func.count(Operadora.registro_ans)
        ).scalar() or 0

        top_operadoras = db.query(
            Operadora.registro_ans,
            Operadora.cnpj,
            Operadora.razao_social,
            Operadora.uf,
            Operadora.modalidade,
            func.sum(DespesaConsolidada.valor_despesas).label('total')
        ).join(
            DespesaConsolidada,
            Operadora.registro_ans == DespesaConsolidada.registro_ans
        ).group_by(
            Operadora.registro_ans,
            Operadora.cnpj,
            Operadora.razao_social,
            Operadora.uf,
            Operadora.modalidade
        ).order_by(
            desc('total')
        ).limit(5).all()

        despesas_por_uf = db.query(
            Operadora.uf,
            func.sum(DespesaConsolidada.valor_despesas).label('total'),
            func.count(func.distinct(DespesaConsolidada.registro_ans)).label(
                'num_operadoras')
        ).join(
            DespesaConsolidada,
            Operadora.registro_ans == DespesaConsolidada.registro_ans
        ).filter(
            Operadora.uf.isnot(None)
        ).group_by(
            Operadora.uf
        ).order_by(
            desc('total')
        ).all()

        return {
            "total_despesas": float(total_despesas),
            "media_despesas": float(media_despesas),
            "total_operadoras": total_operadoras,
            "total_registros": db.query(func.count(DespesaConsolidada.id)).scalar(),
            "top_5_operadoras": [
                {
                    "registro_ans": op.registro_ans,
                    "cnpj": op.cnpj,
                    "razao_social": op.razao_social,
                    "uf": op.uf,
                    "modalidade": op.modalidade,
                    "total_despesas": float(op.total)
                }
                for op in top_operadoras
            ],
            "despesas_por_uf": [
                {
                    "uf": row.uf,
                    "total_despesas": float(row.total),
                    "num_operadoras": row.num_operadoras,
                    "percentual": float(row.total / total_despesas * 100) if total_despesas > 0 else 0
                }
                for row in despesas_por_uf
            ],
            "cache_info": {
                "cached_at": datetime.now().isoformat(),
                "ttl_seconds": EstatisticaService.CACHE_TTL_SECONDS
            }
        }
