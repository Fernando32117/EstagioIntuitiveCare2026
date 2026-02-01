import zipfile
from pathlib import Path


def zip_csv(csv_path: Path, zip_path: Path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_path, arcname=csv_path.name)
