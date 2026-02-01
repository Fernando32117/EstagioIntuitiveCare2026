"""
Enriquecedor de dados com informações cadastrais da ANS.

Trade-off implementado: Join em memória com pandas (em vez de streaming/chunked)
- Prós: Simples, rápido para datasets médios, suporte nativo do pandas
- Contras: Pode usar muita memória com datasets muito grandes

Justificativa: Os dados da ANS (~400k registros) cabem confortavelmente em memória
de máquinas modernas (< 100MB). A simplicidade do código vale a pena. Se os dados
crescerem significativamente (>10M registros), seria legal migrar para outro processamento.
"""

import logging
import pandas as pd
import requests
from pathlib import Path
import re
from utils.enrichment import EnrichmentStats, CadastroColumnMapping

logger = logging.getLogger(__name__)


class DataEnricher:
    def __init__(self, cadastro_dir: Path, ans_url: str):
        self.cadastro_dir = cadastro_dir
        self.ans_url = ans_url
        self.cadastro_df = None
        self.enrichment_stats: EnrichmentStats = {
            'total_records': 0,
            'matched': 0,
            'not_matched': 0,
            'multiple_matches': 0
        }

    def load_cadastro(self) -> bool:
        cadastro_file = self.cadastro_dir / "Relatorio_cadop.csv"

        if not cadastro_file.exists():
            if not self._download_cadastro(cadastro_file):
                return False

        try:
            for sep in [';', ',', '\t']:
                for encoding in ['latin1', 'utf-8', 'iso-8859-1']:
                    try:
                        self.cadastro_df = pd.read_csv(
                            cadastro_file,
                            sep=sep,
                            encoding=encoding,
                            dtype=str
                        )
                        if len(self.cadastro_df.columns) > 3:
                            return True
                    except:
                        continue

            logger.error("Não foi possível ler o arquivo cadastral")
            return False

        except Exception as e:
            logger.error(f"Erro ao carregar cadastro: {e}")
            return False

    def _download_cadastro(self, output_path: Path) -> bool:
        try:
            response = requests.get(self.ans_url, timeout=30)
            response.raise_for_status()

            matches = re.findall(
                r'href="([^"]*Relatorio_cadop[^"]*\.csv)"', response.text, re.IGNORECASE)

            if not matches:
                logger.error(
                    "Arquivo Relatorio_cadop.csv não encontrado no servidor da ANS")
                return False

            file_url = self.ans_url + \
                matches[0] if not matches[0].startswith('http') else matches[0]

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with requests.get(file_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            return True

        except Exception as e:
            logger.error(f"Erro ao baixar cadastro: {e}")
            return False

    def enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriquece o DataFrame com dados cadastrais (RegistroANS, Modalidade, UF).

        Estratégia de Join:
        - LEFT JOIN: Mantém todos os registros do consolidado
        - Registros sem match terão valores nulos nas colunas enriquecidas
        - Múltiplos matches: mantém o primeiro (pode haver duplicatas no cadastro)

        Returns:
            DataFrame enriquecido com colunas: RegistroANS, Modalidade, UF
        """
        if self.cadastro_df is None:
            logger.error(
                "Cadastro não carregado. Execute load_cadastro() primeiro.")
            return df

        self.enrichment_stats['total_records'] = len(df)

        cadastro_cols = self.cadastro_df.columns.str.upper().str.strip()
        self.cadastro_df.columns = cadastro_cols

        col_mapping = self._identify_cadastro_columns()

        if not col_mapping:
            logger.error(
                "Não foi possível identificar as colunas no cadastro da ANS")
            return df

        razao_col = None
        for col in self.cadastro_df.columns:
            if 'RAZAO' in col or 'NOME_FANTASIA' in col or 'RAZÃO' in col:
                razao_col = col
                break

        cols_to_join = [
            col_mapping['registro_ans'],
            col_mapping.get('cnpj', col_mapping['registro_ans']),
            col_mapping['modalidade'],
            col_mapping['uf']
        ]
        if razao_col:
            cols_to_join.append(razao_col)

        cadastro_for_join = self.cadastro_df[cols_to_join].copy()

        df['CNPJ_JOIN'] = df['CNPJ'].astype(str).str.strip()
        # Usa REGISTRO_OPERADORA para fazer o join (não CNPJ)
        cadastro_for_join['CNPJ_JOIN'] = cadastro_for_join[col_mapping['registro_ans']].astype(
            str).str.strip()

        duplicates = cadastro_for_join[cadastro_for_join.duplicated(
            'CNPJ_JOIN', keep='first')]
        if len(duplicates) > 0:
            self.enrichment_stats['multiple_matches'] = len(duplicates)
            cadastro_for_join = cadastro_for_join.drop_duplicates(
                'CNPJ_JOIN', keep='first')

        df_enriched = df.merge(
            cadastro_for_join,
            on='CNPJ_JOIN',
            how='left',
            suffixes=('', '_CADASTRO')
        )

        df_enriched['RegistroANS'] = df_enriched[col_mapping['registro_ans']]
        df_enriched['Modalidade'] = df_enriched[col_mapping['modalidade']]
        df_enriched['UF'] = df_enriched[col_mapping['uf']]

        razao_col = None
        for col in cadastro_for_join.columns:
            if 'RAZAO' in col or 'NOME' in col:
                razao_col = col
                break

        if razao_col and razao_col in df_enriched.columns:
            mask_empty = (df_enriched['RazaoSocial'].isna()) | (
                df_enriched['RazaoSocial'] == '') | (df_enriched['RazaoSocial'] == 'NÃO INFORMADO')
            df_enriched['RazaoSocial'] = df_enriched['RazaoSocial'].astype(str)
            df_enriched.loc[mask_empty, 'RazaoSocial'] = df_enriched.loc[mask_empty, razao_col].fillna(
                'NÃO INFORMADO')

        cols_to_drop = ['CNPJ_JOIN']
        for orig_col in [col_mapping['registro_ans'], col_mapping['modalidade'], col_mapping['uf']]:
            if orig_col not in ['RegistroANS', 'Modalidade', 'UF']:
                cols_to_drop.append(orig_col)
        if col_mapping.get('cnpj'):
            cols_to_drop.append(col_mapping['cnpj'])
        if razao_col:
            cols_to_drop.append(razao_col)
        df_enriched = df_enriched.drop(columns=cols_to_drop, errors='ignore')
        self._print_enrichment_report()

        return df_enriched

    def _identify_cadastro_columns(self) -> CadastroColumnMapping:
        mapping: CadastroColumnMapping = {}

        for col in self.cadastro_df.columns:
            col_clean = col.upper().strip()

            if 'REGISTRO_OPERADORA' in col_clean:
                mapping['registro_ans'] = col
            elif 'REGISTRO_ANS' in col_clean and 'DATA' not in col_clean and 'registro_ans' not in mapping:
                mapping['registro_ans'] = col
            elif 'REG_ANS' in col_clean and 'registro_ans' not in mapping:
                mapping['registro_ans'] = col
            elif 'CNPJ' in col_clean or 'CGC' in col_clean:
                mapping['cnpj'] = col
            elif 'MODALIDADE' in col_clean or 'MODALIDAD' in col_clean:
                mapping['modalidade'] = col
            elif col_clean == 'UF' or 'SIGLA_UF' in col_clean or 'UF_' in col_clean:
                mapping['uf'] = col

        return mapping

    def _print_enrichment_report(self):
        pass
