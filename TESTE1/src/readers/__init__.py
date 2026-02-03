import logging
from pathlib import Path
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


class FileReader:
    SUPPORTED_SEPARATORS = [";", ",", "\t", "|"]
    SUPPORTED_ENCODINGS = ["latin1", "utf-8", "cp1252"]

    def read(self, path: Path) -> Optional[pd.DataFrame]:
        extension = path.suffix.lower()

        if extension in [".csv", ".txt"]:
            return self._read_text_file(path)
        elif extension == ".xlsx":
            return self._read_excel_file(path)
        else:
            logger.warning(f"Formato não suportado: {extension}")
            return None

    def _read_text_file(self, path: Path) -> Optional[pd.DataFrame]:
        for sep in self.SUPPORTED_SEPARATORS:
            for encoding in self.SUPPORTED_ENCODINGS:
                try:
                    df = pd.read_csv(
                        path,
                        sep=sep,
                        encoding=encoding,
                        dtype=str,
                        on_bad_lines='skip'
                    )

                    if len(df.columns) > 1:
                        logger.debug(
                            f"  └─ Detectado separador: '{sep}', encoding: {encoding}")
                        return df

                except Exception:
                    continue

        logger.error(f"Não foi possível ler o arquivo: {path}")
        return None

    def _read_excel_file(self, path: Path) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_excel(path, dtype=str)
            logger.debug(f"  └─ Arquivo Excel lido com sucesso")
            return df
        except Exception as e:
            logger.error(f"Erro ao ler Excel: {e}")
            return None

    def find_files(self, directory: Path, extensions: list[str] = None) -> list[Path]:
        if extensions is None:
            extensions = ['.csv', '.txt', '.xlsx']

        files = []
        for ext in extensions:
            files.extend(directory.rglob(f"*{ext}"))

        return sorted(files)
