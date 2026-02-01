from config import get_settings, consts
import logging
import re
from pathlib import Path
from typing import List, Tuple
import sys

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


settings = get_settings()


class ANSDownloader:
    def __init__(self):
        self.base_url = settings.ans_base_url
        self.output_dir = settings.teste1_raw_dir

    def download_latest_trimesters(self) -> List[Path]:
        zip_infos = self._discover_all_zips()
        latest_zips = zip_infos[:len(consts.TRIMESTRES_TO_PROCESS)]

        downloaded_files: List[Path] = []

        for filename, year_url in latest_zips:
            downloaded_files.append(
                self._download_file(year_url, filename)
            )

        return downloaded_files

    def _discover_all_zips(self) -> List[Tuple[str, str]]:
        response = requests.get(self.base_url, timeout=30)
        response.raise_for_status()

        years = re.findall(r'href="(\d{4})/"', response.text)
        years = sorted(set(years), reverse=True)

        zip_entries: List[Tuple[str, str, int, int]] = []

        for year in years:
            year_url = f"{self.base_url}/{year}/"

            year_response = requests.get(year_url, timeout=30)
            year_response.raise_for_status()

            zip_files = re.findall(r'href="([^"]+\.zip)"', year_response.text)

            for zip_name in zip_files:
                match = re.match(r'([1-4])T(\d{4})\.zip', zip_name)
                if not match:
                    continue

                quarter = int(match.group(1))
                year_num = int(match.group(2))

                zip_entries.append(
                    (zip_name, year_url, year_num, quarter)
                )

        zip_entries.sort(
            key=lambda x: (x[2], x[3]),
            reverse=True
        )

        return [(z[0], z[1]) for z in zip_entries]

    def _download_file(self, base_url: str, filename: str) -> Path:
        file_url = f"{base_url}{filename}"
        output_path = self.output_dir / filename

        if output_path.exists():
            return output_path

        with requests.get(file_url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(output_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)

        return output_path
