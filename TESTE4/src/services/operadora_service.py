from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, Dict, List
from models import Operadora


class OperadoraService:

    @staticmethod
    def listar_paginado(
        db: Session,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Dict:
        query = db.query(Operadora)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Operadora.razao_social.ilike(search_pattern),
                    Operadora.cnpj.ilike(search_pattern),
                    Operadora.registro_ans.ilike(search_pattern)
                )
            )

        total = query.count()

        skip = (page - 1) * limit
        operadoras = query.offset(skip).limit(limit).all()

        operadoras_dict = [
            {
                "registro_ans": op.registro_ans,
                "cnpj": op.cnpj,
                "razao_social": op.razao_social,
                "modalidade": op.modalidade,
                "uf": op.uf,
                "data_cadastro": op.data_cadastro.isoformat() if op.data_cadastro else None
            }
            for op in operadoras
        ]

        return {
            "data": operadoras_dict,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }

    @staticmethod
    def buscar_por_cnpj_ou_registro(db: Session, identificador: str) -> Optional[Dict]:
        operadora = db.query(Operadora).filter(
            or_(
                Operadora.cnpj == identificador,
                Operadora.registro_ans == identificador
            )
        ).first()

        if not operadora:
            return None

        return {
            "registro_ans": operadora.registro_ans,
            "cnpj": operadora.cnpj,
            "razao_social": operadora.razao_social,
            "modalidade": operadora.modalidade,
            "uf": operadora.uf,
            "data_cadastro": operadora.data_cadastro.isoformat() if operadora.data_cadastro else None
        }
