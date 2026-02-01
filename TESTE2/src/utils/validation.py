from typing import TypedDict, Literal
from enum import Enum


class InvalidReason(str, Enum):
    CNPJ_FORMATO_INVALIDO = "CNPJ_FORMATO_INVALIDO"
    IDENTIFICADOR_FORMATO_INVALIDO = "IDENTIFICADOR_FORMATO_INVALIDO"
    CNPJ_DIGITO_VERIFICADOR_INVALIDO = "CNPJ_DIGITO_VERIFICADOR_INVALIDO"
    VALOR_NEGATIVO = "VALOR_NEGATIVO"
    RAZAO_SOCIAL_VAZIA = "RAZAO_SOCIAL_VAZIA"


class ValidationReport(TypedDict):
    total_records: int
    cnpj_invalid: int
    cnpj_format_error: int
    cnpj_digit_error: int
    valor_negative: int
    razao_empty: int


class ValidationResult(TypedDict):
    is_valid: bool
    reasons: list[str]


IdentifierType = Literal["REG_ANS", "CNPJ", "INVALID"]
REG_ANS_LENGTH = 6
CNPJ_LENGTH = 14
