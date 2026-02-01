from typing import TypedDict, Optional


class EnrichmentStats(TypedDict):
    total_records: int
    matched: int
    not_matched: int
    multiple_matches: int


class CadastroColumnMapping(TypedDict, total=False):
    registro_ans: str
    cnpj: str
    razao_social: Optional[str]
    modalidade: str
    uf: str


class EnrichedRecord(TypedDict):
    CNPJ: str
    RazaoSocial: str
    Trimestre: int
    Ano: int
    ValorDespesas: float
    RegistroANS: str
    Modalidade: str
    UF: str
    VALIDO: bool
    MOTIVO_INVALIDACAO: str
