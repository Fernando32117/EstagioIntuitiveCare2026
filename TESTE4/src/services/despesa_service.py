from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case, and_, or_
from typing import Optional, Dict, List
from decimal import Decimal
from models import Operadora, DespesaConsolidada, DespesaAgregada


class DespesaService:
    @staticmethod
    def buscar_historico_operadora(db: Session, identificador: str) -> Optional[Dict]:
        operadora = db.query(Operadora).filter(
            or_(
                Operadora.cnpj == identificador,
                Operadora.registro_ans == identificador
            )
        ).first()

        if not operadora:
            return None

        despesas = db.query(DespesaConsolidada).filter(
            DespesaConsolidada.registro_ans == operadora.registro_ans
        ).order_by(
            DespesaConsolidada.ano.desc(),
            DespesaConsolidada.trimestre.desc()
        ).all()

        return {
            "operadora": {
                "registro_ans": operadora.registro_ans,
                "cnpj": operadora.cnpj,
                "razao_social": operadora.razao_social,
                "uf": operadora.uf
            },
            "despesas": [
                {
                    "trimestre": d.trimestre,
                    "ano": d.ano,
                    "valor_despesas": float(d.valor_despesas),
                    "data_importacao": d.data_importacao.isoformat() if d.data_importacao else None
                }
                for d in despesas
            ],
            "total_despesas": sum(float(d.valor_despesas) for d in despesas),
            "num_trimestres": len(despesas)
        }

    @staticmethod
    def listar_agregadas(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        uf: Optional[str] = None,
        min_despesas: Optional[Decimal] = None
    ) -> List[DespesaAgregada]:
        query = db.query(DespesaAgregada).order_by(
            desc(DespesaAgregada.total_despesas)
        )

        if uf:
            query = query.filter(DespesaAgregada.uf == uf.upper())

        if min_despesas:
            query = query.filter(
                DespesaAgregada.total_despesas >= min_despesas)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def top_ufs_por_despesas(db: Session, limit: int = 5) -> List[Dict]:
        total_nacional = db.query(
            func.sum(DespesaConsolidada.valor_despesas)
        ).scalar() or Decimal(0)

        despesas_por_uf = db.query(
            Operadora.uf,
            func.count(func.distinct(DespesaConsolidada.registro_ans)).label(
                'num_operadoras'),
            func.sum(DespesaConsolidada.valor_despesas).label(
                'total_despesas'),
            (func.sum(DespesaConsolidada.valor_despesas) /
             func.count(func.distinct(DespesaConsolidada.registro_ans))).label('media_por_operadora')
        ).join(
            DespesaConsolidada,
            Operadora.registro_ans == DespesaConsolidada.registro_ans
        ).filter(
            Operadora.uf.isnot(None)
        ).group_by(
            Operadora.uf
        ).order_by(
            desc('total_despesas')
        ).limit(limit).all()

        resultado = []
        for uf, num_ops, total, media in despesas_por_uf:
            percentual = (total / total_nacional *
                          100) if total_nacional > 0 else Decimal(0)
            resultado.append({
                "uf": uf,
                "num_operadoras": num_ops,
                "total_despesas": total,
                "media_por_operadora": media,
                "percentual_nacional": round(percentual, 2)
            })

        return resultado

    @staticmethod
    def top_crescimento_operadoras(db: Session, limit: int = 5) -> List[Dict]:
        primeiro = db.query(
            DespesaConsolidada.registro_ans,
            DespesaConsolidada.ano,
            DespesaConsolidada.trimestre,
            DespesaConsolidada.valor_despesas,
            func.row_number().over(
                partition_by=DespesaConsolidada.registro_ans,
                order_by=[DespesaConsolidada.ano, DespesaConsolidada.trimestre]
            ).label('rn')
        ).subquery()

        ultimo = db.query(
            DespesaConsolidada.registro_ans,
            DespesaConsolidada.ano,
            DespesaConsolidada.trimestre,
            DespesaConsolidada.valor_despesas,
            func.row_number().over(
                partition_by=DespesaConsolidada.registro_ans,
                order_by=[desc(DespesaConsolidada.ano),
                          desc(DespesaConsolidada.trimestre)]
            ).label('rn')
        ).subquery()

        crescimentos = db.query(
            Operadora.registro_ans,
            Operadora.razao_social,
            Operadora.uf,
            Operadora.modalidade,
            primeiro.c.trimestre.label('trimestre_inicial'),
            primeiro.c.ano.label('ano_inicial'),
            primeiro.c.valor_despesas.label('valor_inicial'),
            ultimo.c.trimestre.label('trimestre_final'),
            ultimo.c.ano.label('ano_final'),
            ultimo.c.valor_despesas.label('valor_final'),
            (
                (ultimo.c.valor_despesas - primeiro.c.valor_despesas) /
                func.nullif(primeiro.c.valor_despesas, 0) * 100
            ).label('crescimento_percentual'),
            (ultimo.c.valor_despesas -
             primeiro.c.valor_despesas).label('variacao_absoluta')
        ).join(
            primeiro,
            and_(
                Operadora.registro_ans == primeiro.c.registro_ans,
                primeiro.c.rn == 1
            )
        ).join(
            ultimo,
            and_(
                Operadora.registro_ans == ultimo.c.registro_ans,
                ultimo.c.rn == 1
            )
        ).filter(
            ultimo.c.valor_despesas > primeiro.c.valor_despesas
        ).order_by(
            desc('crescimento_percentual')
        ).limit(limit).all()

        resultado = []
        for row in crescimentos:
            resultado.append({
                "registro_ans": row.registro_ans,
                "razao_social": row.razao_social,
                "uf": row.uf,
                "modalidade": row.modalidade,
                "trimestre_inicial": row.trimestre_inicial,
                "ano_inicial": row.ano_inicial,
                "valor_inicial": row.valor_inicial,
                "trimestre_final": row.trimestre_final,
                "ano_final": row.ano_final,
                "valor_final": row.valor_final,
                "crescimento_percentual": round(row.crescimento_percentual or Decimal(0), 2),
                "variacao_absoluta": row.variacao_absoluta
            })

        return resultado

    @staticmethod
    def operadoras_acima_da_media(
        db: Session,
        min_trimestres: int = 2,
        limit: int = 10
    ) -> List[Dict]:
        media_por_trimestre = db.query(
            DespesaConsolidada.ano,
            DespesaConsolidada.trimestre,
            func.avg(DespesaConsolidada.valor_despesas).label('media_geral')
        ).group_by(
            DespesaConsolidada.ano,
            DespesaConsolidada.trimestre
        ).subquery()

        comparacao = db.query(
            DespesaConsolidada.registro_ans,
            Operadora.razao_social,
            Operadora.uf,
            func.sum(
                case(
                    (DespesaConsolidada.valor_despesas >
                     media_por_trimestre.c.media_geral, 1),
                    else_=0
                )
            ).label('trimestres_acima_media'),
            func.count().label('total_trimestres'),
            func.avg(DespesaConsolidada.valor_despesas).label('media_despesas')
        ).join(
            Operadora,
            DespesaConsolidada.registro_ans == Operadora.registro_ans
        ).join(
            media_por_trimestre,
            and_(
                DespesaConsolidada.ano == media_por_trimestre.c.ano,
                DespesaConsolidada.trimestre == media_por_trimestre.c.trimestre
            )
        ).group_by(
            DespesaConsolidada.registro_ans,
            Operadora.razao_social,
            Operadora.uf
        ).having(
            func.sum(
                case(
                    (DespesaConsolidada.valor_despesas >
                     media_por_trimestre.c.media_geral, 1),
                    else_=0
                )
            ) >= min_trimestres
        ).order_by(
            desc('trimestres_acima_media'),
            desc('media_despesas')
        ).limit(limit).all()

        resultado = []
        for row in comparacao:
            percentual = (row.trimestres_acima_media / row.total_trimestres *
                          100) if row.total_trimestres > 0 else Decimal(0)
            resultado.append({
                "registro_ans": row.registro_ans,
                "razao_social": row.razao_social,
                "uf": row.uf,
                "trimestres_acima_media": row.trimestres_acima_media,
                "total_trimestres": row.total_trimestres,
                "media_despesas": round(row.media_despesas, 2),
                "percentual_acima": round(percentual, 2)
            })

        return resultado
