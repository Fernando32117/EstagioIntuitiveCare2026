"""
Agregador de dados com análises estatísticas.

Trade-off implementado: Ordenação in-memory com pandas (em vez de ordenação externa)
- Prós: Simples, rápido, totalmente integrado com pandas, funciona bem até ~10M registros
- Contras: Pode usar muita memória com datasets gigantescos

Justificativa: Para os dados da ANS (~400k registros após agregação), a ordenação
in-memory é mais que suficiente. Pandas implementa quicksort/mergesort eficientes.
Só seria necessário ordenação externa (sort em disco) para datasets > 100M registros
ou com memória RAM muito limitada (< 4GB).
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path

from utils.aggregation import (
    AggregationStats,
    VariabilityLevel,
    HIGH_VARIABILITY_THRESHOLD
)

logger = logging.getLogger(__name__)


class DataAggregator:
    def __init__(self) -> None:
        self.aggregation_stats: AggregationStats = {
            'original_records': 0,
            'aggregated_groups': 0,
            'trimestres_por_grupo': {}
        }

    def aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega dados por RazaoSocial e UF, calculando:
        - Total de despesas
        - Média de despesas por trimestre
        - Desvio padrão das despesas

        Returns:
            DataFrame agregado e ordenado por valor total (decrescente)
        """
        self.aggregation_stats['original_records'] = len(df)

        if 'UF' not in df.columns:
            logger.error("ERRO: Coluna 'UF' não encontrada no DataFrame.")
            logger.error(
                "O enriquecimento pode não ter funcionado corretamente.")
            logger.error(f"Colunas disponíveis: {df.columns.tolist()}")
            raise KeyError(
                "Coluna 'UF' não encontrada. Verifique se o enriquecimento foi bem-sucedido.")

        df_clean = df.dropna(subset=['RazaoSocial', 'UF'])
        df_clean = df_clean[(df_clean['RazaoSocial'] != '')
                            & (df_clean['UF'] != '')]

        grouped = df_clean.groupby(['RazaoSocial', 'UF'], as_index=False).agg({
            'ValorDespesas': [
                ('TotalDespesas', 'sum'),
                ('MediaDespesasTrimestre', 'mean'),
                ('DesvioPadraoDespesas', 'std'),
                ('NumeroRegistros', 'count')
            ]
        })

        grouped.columns = ['_'.join(col).strip('_') if col[1] else col[0]
                           for col in grouped.columns.values]

        grouped = grouped.rename(columns={
            'ValorDespesas_TotalDespesas': 'TotalDespesas',
            'ValorDespesas_MediaDespesasTrimestre': 'MediaDespesasTrimestre',
            'ValorDespesas_DesvioPadraoDespesas': 'DesvioPadraoDespesas',
            'ValorDespesas_NumeroRegistros': 'NumeroRegistros'
        })

        grouped['DesvioPadraoDespesas'] = grouped['DesvioPadraoDespesas'].fillna(
            0)

        trimestres_por_grupo = df_clean.groupby(['RazaoSocial', 'UF'])[
            'Trimestre'].nunique().reset_index()
        trimestres_por_grupo = trimestres_por_grupo.rename(
            columns={'Trimestre': 'NumeroTrimestres'})

        grouped = grouped.merge(trimestres_por_grupo, on=[
                                'RazaoSocial', 'UF'], how='left')

        grouped['CoeficienteVariacao'] = (
            grouped['DesvioPadraoDespesas'] / grouped['MediaDespesasTrimestre']
        ).replace([np.inf, -np.inf], 0).fillna(0)

        self.aggregation_stats['aggregated_groups'] = len(grouped)

        grouped_sorted = grouped.sort_values(
            'TotalDespesas', ascending=False).reset_index(drop=True)

        self._print_aggregation_report(grouped_sorted)
        self._print_top_operadoras(grouped_sorted)
        self._print_variability_analysis(grouped_sorted)

        return grouped_sorted

    def _print_aggregation_report(self, df: pd.DataFrame):
        pass

    def _print_top_operadoras(self, df: pd.DataFrame):
        pass

    def _print_variability_analysis(self, df: pd.DataFrame):
        pass

    def export(self, df: pd.DataFrame, output_file) -> None:
        output_file.parent.mkdir(parents=True, exist_ok=True)

        final_columns = [
            'RazaoSocial',
            'UF',
            'TotalDespesas',
            'MediaDespesasTrimestre',
            'DesvioPadraoDespesas'
        ]

        df_export = df[final_columns].copy()

        df_export.to_csv(
            output_file,
            index=False,
            sep=',',
            encoding='utf-8',
            float_format='%.2f'
        )
