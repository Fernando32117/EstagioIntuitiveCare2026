from validators.data_validator import DataValidator
from enrichers.data_enricher import DataEnricher
from aggregators.data_aggregator import DataAggregator
from config import get_settings, consts
import pandas as pd
import logging
import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=consts.DEFAULT_LOG_FORMAT
)


def create_directories():
    for directory in [settings.teste2_input_path, settings.teste2_cadastro_path, settings.teste2_output_path]:
        directory.mkdir(parents=True, exist_ok=True)


def copy_teste1_output():
    teste1_output = Path(__file__).parent.parent.parent / \
        "TESTE1" / "output" / consts.CONSOLIDADO_FILENAME
    input_file = settings.teste2_input_file

    if input_file.exists():
        return True

    if teste1_output.exists():
        import shutil
        shutil.copy(teste1_output, input_file)
        return True
    else:
        logging.error("ERRO: Arquivo consolidado_despesas.csv não encontrado!")
        logging.error(
            f"Execute o TESTE 1 primeiro ou copie para: {input_file}")
        return False


def main():
    logging.info("TESTE 2 - TRANSFORMAÇÃO E VALIDAÇÃO DE DADOS")

    try:
        create_directories()

        if not copy_teste1_output():
            return

        input_file = settings.teste2_input_file
        df = pd.read_csv(input_file)

        logging.info("2.1 VALIDAÇÃO DE DADOS")
        validator = DataValidator()
        df_validated = validator.validate(df)
        df_valid = validator.get_valid_records(df_validated)

        logging.info("2.2 ENRIQUECIMENTO COM DADOS CADASTRAIS")
        enricher = DataEnricher(
            settings.teste2_cadastro_path, settings.ans_cadastro_url)

        if not enricher.load_cadastro():
            logging.error("Falha ao carregar cadastro")
            df_enriched = df_valid
        else:
            df_enriched = enricher.enrich(df_valid)

        logging.info("2.3 AGREGAÇÃO E ANÁLISE ESTATÍSTICA")
        aggregator = DataAggregator()
        df_aggregated = aggregator.aggregate(df_enriched)

        output_file = settings.teste2_aggregated_file
        aggregator.export(df_aggregated, output_file)

        zip_path = settings.teste2_output_path / consts.FINAL_ZIP_NAME
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(output_file, arcname=output_file.name)

        logging.info("TESTE 2 FINALIZADO COM SUCESSO")

    except Exception as e:
        logging.exception("Erro durante a execução do TESTE 2")
        raise


if __name__ == "__main__":
    main()
