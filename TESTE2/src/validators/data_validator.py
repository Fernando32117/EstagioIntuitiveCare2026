"""
Validador de dados com múltiplas estratégias de validação.

Trade-off implementado: MARCAR registros inválidos e manter (em vez de remover)
- Prós: Preserva todos os dados para análise posterior, permite rastreabilidade
- Contras: Requer tratamento cuidadoso em análises para não contaminar resultados

Justificativa: Em processos de validação de dados públicos, é importante manter
transparência sobre quais registros têm problemas. Remover silenciosamente pode
ocultar problemas sistemáticos nos dados originais da ANS.
"""

import logging
import pandas as pd
import re
from typing import Tuple

from utils.validation import (
    ValidationReport,
    InvalidReason,
    IdentifierType,
    REG_ANS_LENGTH,
    CNPJ_LENGTH
)

logger = logging.getLogger(__name__)


class DataValidator:
    def __init__(self) -> None:
        self.validation_report: ValidationReport = {
            'total_records': 0,
            'cnpj_invalid': 0,
            'cnpj_format_error': 0,
            'cnpj_digit_error': 0,
            'valor_negative': 0,
            'razao_empty': 0
        }

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        self.validation_report['total_records'] = len(df)

        df = df.copy()
        df['VALIDO'] = True
        df['MOTIVO_INVALIDACAO'] = ''

        df = self._validate_cnpj(df)
        df = self._validate_valores(df)
        df = self._validate_razao_social(df)

        self._print_validation_report(df)

        return df

    def _validate_cnpj(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida CNPJ/REG_ANS.

        Aceita tanto CNPJ (14 dígitos) quanto REG_ANS (6 dígitos) da ANS.
        Estratégia: MARCAR como inválido apenas se não for nem CNPJ nem REG_ANS válido.
        """
        for idx, row in df.iterrows():
            identificador = str(row['CNPJ']).strip()
            id_numbers = re.sub(r'[^0-9]', '', identificador)
            id_type = self._identify_type(id_numbers)

            if id_type == "REG_ANS":
                continue
            elif id_type == "CNPJ":
                if not self._validate_cnpj_digits(id_numbers):
                    df.at[idx, 'VALIDO'] = False
                    df.at[idx,
                          'MOTIVO_INVALIDACAO'] += f'{InvalidReason.CNPJ_DIGITO_VERIFICADOR_INVALIDO.value}; '
                    self.validation_report['cnpj_digit_error'] += 1
            else:
                df.at[idx, 'VALIDO'] = False
                df.at[idx,
                      'MOTIVO_INVALIDACAO'] += f'{InvalidReason.IDENTIFICADOR_FORMATO_INVALIDO.value}; '
                self.validation_report['cnpj_format_error'] += 1

        return df

    def _identify_type(self, id_numbers: str) -> IdentifierType:
        if len(id_numbers) == REG_ANS_LENGTH:
            return "REG_ANS"
        elif len(id_numbers) == CNPJ_LENGTH:
            return "CNPJ"
        else:
            return "INVALID"

    def _validate_cnpj_digits(self, cnpj: str) -> bool:
        if len(cnpj) != 14:
            return False

        if len(set(cnpj)) == 1:
            return False

        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
        digit1 = 0 if sum1 % 11 < 2 else 11 - (sum1 % 11)

        if int(cnpj[12]) != digit1:
            return False

        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
        digit2 = 0 if sum2 % 11 < 2 else 11 - (sum2 % 11)

        return int(cnpj[13]) == digit2

    def _validate_valores(self, df: pd.DataFrame) -> pd.DataFrame:
        negative_mask = df['ValorDespesas'] < 0
        negative_count = negative_mask.sum()

        if negative_count > 0:
            df.loc[negative_mask, 'VALIDO'] = False
            df.loc[negative_mask, 'MOTIVO_INVALIDACAO'] += 'VALOR_NEGATIVO; '
            self.validation_report['valor_negative'] = negative_count

        return df

    def _validate_razao_social(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valida se a Razão Social não está vazia.

        NOTA: No TESTE 1, a Razão Social vem vazia dos arquivos da ANS.
        Será preenchida no enriquecimento (TESTE 2.2).
        Por isso, não invalidamos registros sem Razão Social.
        """
        empty_mask = (df['RazaoSocial'].isna()) | (
            df['RazaoSocial'] == '') | (df['RazaoSocial'] == 'NÃO INFORMADO')
        empty_count = empty_mask.sum()

        if empty_count > 0:
            self.validation_report['razao_empty'] = empty_count

        return df

    def _print_validation_report(self, df: pd.DataFrame):
        pass

    def get_valid_records(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df['VALIDO']].copy()

    def get_invalid_records(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[~df['VALIDO']].copy()
