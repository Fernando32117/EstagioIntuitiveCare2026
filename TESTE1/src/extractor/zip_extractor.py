from config import get_settings
import logging
import zipfile
from pathlib import Path
from typing import List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


settings = get_settings()


class ZipExtractor:
    def extract(self, zip_files: List[Path]) -> List[Path]:
        extracted_files: List[Path] = []

        for zip_path in zip_files:
            target_dir = settings.teste1_extracted_dir / zip_path.stem
            target_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(target_dir)

            for file in target_dir.rglob("*"):
                if file.is_file():
                    extracted_files.append(file)

        return extracted_files
