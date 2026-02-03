import logging
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


class AccountFilter:
    TARGET_ACCOUNT_CODES = ['411', '41']
    DESCRIPTION_KEYWORDS = [
        'EVENTO', 'SINISTRO', 'DESPESA COM EVENTO',
        'ASSISTENCIA', 'ASSISTÊNCIA', 'INTERNACAO', 'INTERNAÇÃO',
        'CONSULTA', 'EXAME', 'TERAPIA', 'PROCEDIMENTO'
    ]

    def __init__(self, target_account: str = "411"):
        self.target_account = target_account
        self.TARGET_ACCOUNT_CODES = [target_account, target_account[:2]]

    def filter(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        df = df.copy()
        df.columns = df.columns.str.upper().str.strip()

        col_mapping = self._identify_columns(df)

        if not col_mapping:
            logger.warning(
                "Não foi possível identificar as colunas necessárias para filtro")
            return pd.DataFrame()

        filter_mask = pd.Series([False] * len(df))

        if 'conta' in col_mapping:
            conta_col = col_mapping['conta']
            for code in self.TARGET_ACCOUNT_CODES:
                filter_mask |= df[conta_col].astype(
                    str).str.startswith(code, na=False)

        if 'descricao' in col_mapping:
            desc_col = col_mapping['descricao']
            description_upper = df[desc_col].astype(str).str.upper()

            for keyword in self.DESCRIPTION_KEYWORDS:
                filter_mask |= description_upper.str.contains(
                    keyword, na=False, regex=False
                )

        filtered_df = df[filter_mask].copy()

        if not filtered_df.empty:
            logger.debug(
                f"  └─ Filtrados {len(filtered_df)} de {len(df)} registros")

        return filtered_df

    def _identify_columns(self, df: pd.DataFrame) -> dict:
        mapping = {}

        for col in df.columns:
            col_clean = col.upper().strip()

            if any(k in col_clean for k in ['CONTA', 'CD_CONTA', 'CODIGO_CONTA', 'CÓDIGO_CONTA']):
                if 'conta' not in mapping:
                    mapping['conta'] = col

            elif any(k in col_clean for k in ['DESCRI', 'DESC_CONTA', 'DESCRIÇÃO', 'DESCRICAO']):
                if 'descricao' not in mapping:
                    mapping['descricao'] = col

        return mapping
