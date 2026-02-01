import logging
from pathlib import Path
from typing import List, Any


class ExpensesNormalizer:
    def normalize_and_export(self, data: List[Any], output_path: Path) -> None:
        output_path.touch(exist_ok=True)
