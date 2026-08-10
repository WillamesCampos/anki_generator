"""
Configuração do Banco de Dados MongoDB

Centraliza as configurações de conexão com o MongoDB usado para persistir
decks, cards e estatísticas de estudo (ver `<persistencia>` em PROMPT_REFINADO.md).
As variáveis de ambiente são carregadas pelo Django (`core/settings/base.py`) via
`python-dotenv`, não aqui — este módulo só lê do `os.environ`.
"""

import os
from typing import Optional
from dataclasses import dataclass

from apps.decks.infrastructure.exceptions import MongoConfigError


@dataclass
class MongoDBConfig:
    """
    Configuração para conexão com MongoDB.
    """

    host: str = "localhost"
    port: int = 27017
    username: Optional[str] = None
    password: Optional[str] = None
    database: str = "anki_generator"
    auth_source: str = "admin"

    max_pool_size: int = 100
    min_pool_size: int = 10
    max_idle_time_ms: int = 30000
    connect_timeout_ms: int = 20000
    server_selection_timeout_ms: int = 5000

    ssl: bool = False
    ssl_cert_reqs: str = "CERT_REQUIRED"
    ssl_ca_certs: Optional[str] = None

    @classmethod
    def from_env(cls) -> "MongoDBConfig":
        """
        Cria configuração a partir de variáveis de ambiente.
        """
        return cls(
            host=os.getenv("MONGODB_HOST", "localhost"),
            port=int(os.getenv("MONGODB_PORT", "27017")),
            username=os.getenv("MONGODB_USERNAME") or None,
            password=os.getenv("MONGODB_PASSWORD") or None,
            database=os.getenv("MONGODB_DATABASE", "anki_generator"),
            auth_source=os.getenv("MONGODB_AUTH_SOURCE", "admin"),
            max_pool_size=int(os.getenv("MONGODB_MAX_POOL_SIZE", "100")),
            min_pool_size=int(os.getenv("MONGODB_MIN_POOL_SIZE", "10")),
            max_idle_time_ms=int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "30000")),
            connect_timeout_ms=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "20000")),
            server_selection_timeout_ms=int(
                os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
            ),
            ssl=os.getenv("MONGODB_SSL", "false").lower() == "true",
            ssl_cert_reqs=os.getenv("MONGODB_SSL_CERT_REQS", "CERT_REQUIRED"),
            ssl_ca_certs=os.getenv("MONGODB_SSL_CA_CERTS"),
        )

    def get_connection_string(self) -> str:
        if self.username and self.password:
            return (
                f"mongodb://{self.username}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}?authSource={self.auth_source}"
            )
        return f"mongodb://{self.host}:{self.port}/{self.database}"

    def get_connection_params(self) -> dict:
        params = {
            "host": self.host,
            "port": self.port,
            "maxPoolSize": self.max_pool_size,
            "minPoolSize": self.min_pool_size,
            "maxIdleTimeMS": self.max_idle_time_ms,
            "connectTimeoutMS": self.connect_timeout_ms,
            "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
        }

        if self.username and self.password:
            params.update(
                {
                    "username": self.username,
                    "password": self.password,
                    "authSource": self.auth_source,
                }
            )

        if self.ssl:
            params.update({"ssl": self.ssl, "ssl_cert_reqs": self.ssl_cert_reqs})
            if self.ssl_ca_certs:
                params["ssl_ca_certs"] = self.ssl_ca_certs

        return params

    def validate(self) -> None:
        if not self.host:
            raise MongoConfigError("MongoDB host cannot be empty")
        if not (1 <= self.port <= 65535):
            raise MongoConfigError("MongoDB port must be between 1 and 65535")
        if not self.database:
            raise MongoConfigError("MongoDB database name cannot be empty")
        if self.max_pool_size < 1:
            raise MongoConfigError("Max pool size must be at least 1")
        if self.min_pool_size < 0:
            raise MongoConfigError("Min pool size cannot be negative")
        if self.min_pool_size > self.max_pool_size:
            raise MongoConfigError("Min pool size cannot be greater than max pool size")

    def __str__(self) -> str:
        return f"MongoDBConfig(host={self.host}, port={self.port}, database={self.database}, ssl={self.ssl})"


_config: Optional[MongoDBConfig] = None


def get_mongodb_config() -> MongoDBConfig:
    global _config
    if _config is None:
        _config = MongoDBConfig.from_env()
        _config.validate()
    return _config


def set_mongodb_config(config: MongoDBConfig) -> None:
    global _config
    config.validate()
    _config = config
