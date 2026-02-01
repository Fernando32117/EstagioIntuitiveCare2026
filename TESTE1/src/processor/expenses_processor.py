import logging
from pathlib import Path
import pandas as pd
import re
from typing import Tuple

from readers import FileReader
from filters import AccountFilter
from cleaners import DataCleaner

logger = logging.getLogger(__name__)


class ExpensesProcessor:
    def __init__(self, extracted_dir: Path, output_file: Path, target_account: str = "411"):
        self.extracted_dir = extracted_dir
        self.output_file = output_file

        self.reader = FileReader()
        self.filter = AccountFilter(target_account=target_account)
        self.cleaner = DataCleaner()

    def run(self):
        data_files = self.reader.find_files(self.extracted_dir)

        if not data_files:
            return

        all_expenses = []

        for data_file in data_files:
            try:
                df = self.reader.read(data_file)
                if df is None:
                    continue

                expenses_df = self.filter.filter(df)

                if expenses_df.empty:
                    continue

                trimestre, ano = self._extract_trimester_and_year(
                    data_file.parent.name)
                normalized_df = self._extract_fields(
                    expenses_df, trimestre, ano)

                if not normalized_df.empty:
                    all_expenses.append(normalized_df)

            except Exception as e:
                logger.error(f"Erro ao processar {data_file.name}: {e}")
                continue

        if not all_expenses:
            return

        consolidated = pd.concat(all_expenses, ignore_index=True)

        logger.info("TRATAMENTO DE INCONSISTÊNCIAS")
        cleaned = self.cleaner.clean(consolidated)

        final_df = self._normalize_to_final_format(cleaned)

        self._export(final_df)
        self._log_cleaning_report()

    def _extract_fields(self, df: pd.DataFrame, trimestre: int, ano: int) -> pd.DataFrame:
        result = pd.DataFrame()
        col_mapping = self._identify_columns(df)

        if 'reg_ans' in col_mapping:
            result['REG_ANS'] = df[col_mapping['reg_ans']].astype(
                str).str.strip()
        elif 'cnpj' in col_mapping:
            result['REG_ANS'] = df[col_mapping['cnpj']].astype(str).str.strip()
        else:
            result['REG_ANS'] = ''

        if 'razao_social' in col_mapping:
            result['RazaoSocial'] = df[col_mapping['razao_social']].astype(
                str).str.strip()
        else:
            result['RazaoSocial'] = ''

        result['Trimestre'] = trimestre
        result['Ano'] = ano

        if 'valor' in col_mapping:
            valor_col = col_mapping['valor']
            result['ValorDespesas'] = (
                df[valor_col]
                .astype(str)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.replace(r'[^0-9.\-]', '', regex=True)
            )
            result['ValorDespesas'] = pd.to_numeric(
                result['ValorDespesas'], errors='coerce')
        else:
            result['ValorDespesas'] = 0.0

        return result.dropna(subset=['ValorDespesas'])

    def _identify_columns(self, df: pd.DataFrame) -> dict:
        mapping = {}

        for col in df.columns:
            col_clean = col.upper().strip()

            if any(k in col_clean for k in ['REG_ANS', 'REGISTRO_ANS', 'REG ANS']):
                mapping['reg_ans'] = col
            elif any(k in col_clean for k in ['CNPJ', 'CGC']):
                mapping['cnpj'] = col
            elif any(k in col_clean for k in ['RAZAO', 'RAZÃO', 'NOME', 'OPERADORA']):
                mapping['razao_social'] = col
            elif any(k in col_clean for k in ['VL_SALDO_FINAL', 'VALOR', 'SALDO']):
                mapping['valor'] = col

        return mapping

    def _extract_trimester_and_year(self, folder_name: str) -> Tuple[int, int]:
        match = re.search(r'(\d)T(\d{4})', folder_name)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0

    def _normalize_to_final_format(self, df: pd.DataFrame) -> pd.DataFrame:

        df['CNPJ'] = df['REG_ANS'] if 'REG_ANS' in df.columns else ''
        df = df[df['CNPJ'].notna() & (df['CNPJ'] != '')]
        df['RazaoSocial'] = df['RazaoSocial'].fillna('NÃO INFORMADO')

        final_columns = ['CNPJ', 'RazaoSocial',
                         'Trimestre', 'Ano', 'ValorDespesas']
        return df[final_columns].copy()

    def _export(self, df: pd.DataFrame):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(
            self.output_file,
            index=False,
            sep=',',
            encoding='utf-8',
            float_format='%.2f'
        )

    def _log_cleaning_report(self):
        report = self.cleaner.get_cleaning_report()

        if report['total_inconsistencies'] > 0:
            logger.info("RESUMO DE INCONSISTÊNCIAS")

            for item in report['details']:
                logger.info(
                    f"  • {item['tipo']}: {item['quantidade']} - {item['acao']}")
