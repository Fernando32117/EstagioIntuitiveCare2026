import logging
import pandas as pd
from typing import List, Dict

logger = logging.getLogger(__name__)


class DataCleaner:
    def __init__(self):
        self.inconsistencies_log: List[Dict] = []

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica todas as regras de limpeza.

        Estratégias implementadas:
        1. Remove valores negativos (podem ser erros de contabilização)
        2. Mantém valores zero (representam ausência de despesa no período)
        3. Remove duplicatas exatas
        4. Loga CNPJs com razões sociais inconsistentes

        Args:
            df: DataFrame a ser limpo

        Returns:
            DataFrame limpo
        """
        df_clean = df.copy()
        original_count = len(df_clean)
        df_clean = self._remove_negative_values(df_clean)
        df_clean = self._remove_exact_duplicates(df_clean)
        self._detect_razao_social_inconsistencies(df_clean)
        df_clean = self._standardize_quarters(df_clean)

        cleaned_count = len(df_clean)
        removed = original_count - cleaned_count

        if removed > 0:
            logger.info(f"  └─ {removed} registros removidos durante limpeza")

        return df_clean

    def _remove_negative_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove registros com valores negativos.

        Trade-off: Remover vs Marcar
        - Escolha: Remover
        - Justificativa: Valores negativos geralmente indicam erros de dados
        - Zeros são mantidos (podem representar períodos sem despesa)
        """
        if 'ValorDespesas' not in df.columns:
            return df

        negative_mask = df['ValorDespesas'] < 0
        negative_count = negative_mask.sum()

        if negative_count > 0:
            logger.info(
                f"  └─ Removidos {negative_count} registros com valores negativos")
            self.inconsistencies_log.append({
                'tipo': 'valores_negativos',
                'quantidade': negative_count,
                'acao': 'removidos'
            })

        zero_count = (df['ValorDespesas'] == 0).sum()
        if zero_count > 0:
            logger.info(f"  └─ Mantidos {zero_count} registros com valor zero")
            self.inconsistencies_log.append({
                'tipo': 'valores_zero',
                'quantidade': zero_count,
                'acao': 'mantidos'
            })

        return df[~negative_mask]

    def _remove_exact_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        duplicates_count = df.duplicated().sum()

        if duplicates_count > 0:
            logger.info(f"  └─ Removidas {duplicates_count} linhas duplicadas")
            self.inconsistencies_log.append({
                'tipo': 'duplicatas_exatas',
                'quantidade': duplicates_count,
                'acao': 'removidas'
            })

        return df.drop_duplicates()

    def _detect_razao_social_inconsistencies(self, df: pd.DataFrame):
        """
        Detecta CNPJs com múltiplas razões sociais.

        Trade-off: Remover vs Logar
        - Escolha: Logar (não remover)
        - Justificativa: Pode ser mudança legítima de razão social
        """
        if 'CNPJ' not in df.columns or 'RazaoSocial' not in df.columns:
            return

        cnpj_razao = df.groupby('CNPJ')['RazaoSocial'].nunique()
        inconsistent_cnpjs = cnpj_razao[cnpj_razao > 1]

        if len(inconsistent_cnpjs) > 0:
            logger.warning(
                f"  └─ {len(inconsistent_cnpjs)} CNPJs com múltiplas razões sociais "
                "(mantidos para análise posterior)"
            )
            self.inconsistencies_log.append({
                'tipo': 'razao_social_inconsistente',
                'quantidade': len(inconsistent_cnpjs),
                'acao': 'mantidos_com_aviso',
                'detalhes': inconsistent_cnpjs.head(5).to_dict()
            })

    def _standardize_quarters(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'Trimestre' not in df.columns:
            return df

        df['Trimestre'] = pd.to_numeric(df['Trimestre'], errors='coerce')

        invalid_mask = (df['Trimestre'] < 1) | (df['Trimestre'] > 4)
        invalid_count = invalid_mask.sum()

        if invalid_count > 0:
            logger.warning(
                f"  └─ {invalid_count} registros com trimestre inválido removidos")
            self.inconsistencies_log.append({
                'tipo': 'trimestre_invalido',
                'quantidade': invalid_count,
                'acao': 'removidos'
            })

        return df[~invalid_mask]

    def get_cleaning_report(self) -> Dict:
        return {
            'total_inconsistencies': len(self.inconsistencies_log),
            'details': self.inconsistencies_log
        }
