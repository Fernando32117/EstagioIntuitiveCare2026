from utils.zip_utils import zip_csv
from processor.expenses_processor import ExpensesProcessor
from extractor.zip_extractor import ZipExtractor
from downloader.ans_downloader import ANSDownloader
from config import get_settings, consts
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=consts.DEFAULT_LOG_FORMAT
)


def create_directories():
    for directory in [
        settings.teste1_raw_dir,
        settings.teste1_extracted_dir,
        settings.teste1_output_path
    ]:
        directory.mkdir(parents=True, exist_ok=True)


def main():
    logging.info("TESTE 1 - INTEGRAÇÃO COM API ANS")

    try:
        create_directories()

        downloader = ANSDownloader()
        zip_files = downloader.download_latest_trimesters()

        extractor = ZipExtractor()
        extractor.extract(zip_files)

        processor = ExpensesProcessor(
            extracted_dir=settings.teste1_extracted_dir,
            output_file=settings.teste1_consolidated_file
        )
        processor.run()

        output_zip_path = settings.teste1_output_path / "consolidado_despesas.zip"
        zip_csv(settings.teste1_consolidated_file, output_zip_path)

        logging.info("TESTE 1 FINALIZADO COM SUCESSO")

    except Exception:
        logging.exception("Erro durante a execução do pipeline")
        raise


if __name__ == "__main__":
    main()
