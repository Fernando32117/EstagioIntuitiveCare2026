from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

from . import consts


class Settings(BaseSettings):
    ans_base_url: str = Field(
        default="https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis",
        description="URL base para download de demonstrações contábeis"
    )
    ans_cadastro_url: str = Field(
        default="https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_saude",
        description="URL base para download de cadastro de operadoras"
    )
    log_level: str = Field(
        default="INFO",
        description="Nível de logging (DEBUG, INFO, WARNING, ERROR)"
    )

    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent

    # TESTE 1
    @property
    def teste1_raw_dir(self) -> Path:
        return self.project_root / consts.TESTE1_DATA_DIR / "raw"

    @property
    def teste1_extracted_dir(self) -> Path:
        return self.project_root / consts.TESTE1_DATA_DIR / "extracted"

    @property
    def teste1_output_path(self) -> Path:
        return self.project_root / consts.TESTE1_OUTPUT_DIR

    @property
    def teste1_consolidated_file(self) -> Path:
        return self.teste1_output_path / consts.CONSOLIDADO_FILENAME

    # TESTE 2
    @property
    def teste2_input_path(self) -> Path:
        return self.project_root / consts.TESTE2_INPUT_DIR

    @property
    def teste2_cadastro_path(self) -> Path:
        return self.project_root / consts.TESTE2_CADASTRO_DIR

    @property
    def teste2_output_path(self) -> Path:
        return self.project_root / consts.TESTE2_OUTPUT_DIR

    @property
    def teste2_input_file(self) -> Path:
        return self.teste2_input_path / consts.CONSOLIDADO_FILENAME

    @property
    def teste2_aggregated_file(self) -> Path:
        return self.teste2_output_path / consts.AGREGADO_FILENAME

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
