import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8001

    # Teto de cards por exportação (Sprint 11, D9): cada card é uma chamada de
    # rede sequencial ao gTTS. Reforça a validação do Django (defesa em profundidade).
    max_cards_per_export: int = 100
    audio_output_dir: str = "/data/anki_audio"

    # JWT de serviço (Sprint 5, `autenticacao-service-to-service-jwt`) —
    # autentica chamadas Django -> document-generator. `service_jwt_keys` é
    # o MESMO mapa `{kid: secret}` configurado no lado Django
    # (`SERVICE_JWT_KEYS`) — a verificação aqui é sempre local (nenhuma
    # chamada de volta pro Django), aceitando qualquer `kid` presente neste
    # mapa, não só o mais recente (permite rotação sem downtime: ver D4 em
    # openspec/changes/sprint-5-fundacoes-transversais/design.md).
    service_jwt_keys_raw: str = Field(default="{}", alias="SERVICE_JWT_KEYS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_prefix="",
    )

    @property
    def service_jwt_keys(self) -> dict[str, str]:
        return json.loads(self.service_jwt_keys_raw)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
