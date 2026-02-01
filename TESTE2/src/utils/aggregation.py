from typing import TypedDict
from enum import Enum


class VariabilityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AggregationStats(TypedDict):
    original_records: int
    aggregated_groups: int
    trimestres_por_grupo: dict[str, int]


class AggregatedGroup(TypedDict):
    RazaoSocial: str
    UF: str
    TotalDespesas: float
    MediaDespesasTrimestre: float
    DesvioPadraoDespesas: float
    NumeroRegistros: int
    NumeroTrimestres: int
    CoeficienteVariacao: float


HIGH_VARIABILITY_THRESHOLD = 0.5
COMPRESSION_THRESHOLD = 100
