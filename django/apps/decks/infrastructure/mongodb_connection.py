"""
Gerenciador de Conexão MongoDB

Este módulo gerencia a conexão síncrona com MongoDB usando pymongo.
Implementa o padrão Singleton para garantir uma única instância de conexão
em toda a aplicação.

Características:
- Conexão síncrona com pymongo
- Singleton pattern
- Pool de conexões otimizado
- Reconexão automática
- Health check
"""

import threading
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from apps.decks.infrastructure.exceptions import (
    MongoConfigError,
    MongoNotConnectedError,
)
from apps.decks.infrastructure.mongodb_config import get_mongodb_config, MongoDBConfig
from apps.decks.infrastructure.schemas import IndexDefinitions


class MongoDBConnectionManager:
    """
    Gerenciador de conexão MongoDB usando pymongo (síncrono).

    Implementa o padrão Singleton para garantir uma única instância
    de conexão em toda a aplicação.
    """

    _instance: Optional["MongoDBConnectionManager"] = None
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    _config: Optional[MongoDBConfig] = None
    _connect_lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "MongoDBConnectionManager":
        """
        Implementa o padrão Singleton.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Inicializa o gerenciador de conexão.
        """
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._config = get_mongodb_config()

    def connect(self, config: Optional[MongoDBConfig] = None) -> None:
        """
        Estabelece conexão com MongoDB.

        Args:
            config: Configuração personalizada (opcional)

        Raises:
            ConnectionFailure: Se não conseguir conectar
            ServerSelectionTimeoutError: Se timeout na seleção do servidor
        """
        if config:
            self._config = config

        if self._config is None:
            raise MongoConfigError("MongoDB configuration is required")

        try:
            if self._client is not None:
                self._client.close()

            # Cria cliente MongoDB com configurações otimizadas
            connection_params = self._config.get_connection_params()
            self._client = MongoClient(
                host=connection_params.pop("host"),
                port=connection_params.pop("port"),
                **connection_params,
            )

            # Obtém referência do banco
            self._database = self._client[self._config.database]

            # Testa a conexão
            self._test_connection()

            print(
                f"✅ MongoDB conectado: {self._config.host}:{self._config.port}/{self._config.database}"
            )

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ Erro ao conectar MongoDB: {e}")
            raise

    def disconnect(self) -> None:
        """
        Fecha a conexão com MongoDB.
        """
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            print("🔌 MongoDB desconectado")

    def _test_connection(self) -> None:
        """
        Testa a conexão com MongoDB.

        Raises:
            ConnectionFailure: Se a conexão falhar
        """
        try:
            # Ping no servidor para testar conexão
            self._client.admin.command("ping")
        except Exception as e:
            raise ConnectionFailure(f"Failed to ping MongoDB server: {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        Verifica a saúde da conexão MongoDB.

        Returns:
            Dicionário com informações de saúde
        """
        if not self.is_connected():
            return {"status": "disconnected", "error": "Not connected to MongoDB"}

        try:
            # Ping no servidor
            ping_result = self._client.admin.command("ping")

            # Informações do servidor
            server_info = self._client.server_info()

            # Estatísticas do banco
            db_stats = self._database.command("dbStats")

            return {
                "status": "connected",
                "ping": ping_result,
                "server_version": server_info.get("version"),
                "database_name": self._config.database,
                "collections_count": db_stats.get("collections", 0),
                "data_size": db_stats.get("dataSize", 0),
                "storage_size": db_stats.get("storageSize", 0),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def is_connected(self) -> bool:
        """
        Verifica se está conectado ao MongoDB.
        """
        return self._client is not None and self._database is not None

    @property
    def client(self) -> MongoClient:
        """
        Retorna o cliente MongoDB.

        Returns:
            Cliente MongoClient

        Raises:
            MongoNotConnectedError: Se não estiver conectado
        """
        if not self.is_connected():
            raise MongoNotConnectedError("MongoDB not connected. Call connect() first.")
        return self._client

    @property
    def database(self) -> Database:
        """
        Retorna o banco de dados MongoDB.

        Returns:
            Banco Database

        Raises:
            MongoNotConnectedError: Se não estiver conectado
        """
        if not self.is_connected():
            raise MongoNotConnectedError("MongoDB not connected. Call connect() first.")
        return self._database

    @property
    def config(self) -> MongoDBConfig:
        """
        Retorna a configuração MongoDB.

        Returns:
            Configuração MongoDB
        """
        return self._config

    def get_collection(self, collection_name: str):
        """
        Retorna uma collection do MongoDB.

        Args:
            collection_name: Nome da collection

        Returns:
            Collection MongoDB
        """
        return self.database[collection_name]

    def create_indexes(self) -> None:
        """
        Cria índices otimizados para o sistema, a partir da fonte única de
        verdade em `IndexDefinitions` (schemas.py) — evita duas listas de
        índices divergentes (ver `<regra_obrigatoria>` sobre índices em
        PROMPT_REFINADO.md).
        """
        if not self.is_connected():
            raise MongoNotConnectedError("MongoDB not connected. Call connect() first.")

        for collection_name, index_defs in IndexDefinitions.get_all_indexes().items():
            collection = self.get_collection(collection_name)
            for index_def in index_defs:
                if isinstance(index_def, tuple) and isinstance(index_def[0], str):
                    field_name, direction = index_def
                    collection.create_index([(field_name, direction)])
                else:
                    keys, options = index_def
                    collection.create_index(keys, **options)

        print("✅ Índices MongoDB criados com sucesso")

    def drop_collection(self, collection_name: str) -> None:
        """
        Remove uma collection (apenas para desenvolvimento/testes).

        Args:
            collection_name: Nome da collection
        """
        if not self.is_connected():
            raise MongoNotConnectedError("MongoDB not connected. Call connect() first.")

        self.database.drop_collection(collection_name)
        print(f"🗑️ Collection '{collection_name}' removida")

    def get_database_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o banco de dados.

        Returns:
            Dicionário com informações do banco
        """
        if not self.is_connected():
            raise MongoNotConnectedError("MongoDB not connected. Call connect() first.")

        db_stats = self._database.command("dbStats")

        # Lista collections
        collections = self._database.list_collection_names()

        return {
            "database_name": self._config.database,
            "collections": collections,
            "collections_count": db_stats.get("collections", 0),
            "data_size_bytes": db_stats.get("dataSize", 0),
            "storage_size_bytes": db_stats.get("storageSize", 0),
            "indexes_count": db_stats.get("indexes", 0),
            "objects_count": db_stats.get("objects", 0),
        }


# Instância global do gerenciador
mongodb_manager = MongoDBConnectionManager()


def get_mongodb_manager() -> MongoDBConnectionManager:
    """
    Retorna a instância global do gerenciador MongoDB.

    Returns:
        Gerenciador MongoDB
    """
    return mongodb_manager


def ensure_mongodb_connection() -> MongoDBConnectionManager:
    """
    Garante que a conexão MongoDB está estabelecida.

    Protegida por um lock comum (`threading.Lock`) para que requisições
    concorrentes chegando antes de qualquer conexão existir não disparem
    múltiplos `connect()` simultâneos — só a primeira efetivamente conecta,
    as demais reaproveitam o client já criado.

    Returns:
        Gerenciador MongoDB conectado

    Raises:
        ConnectionFailure: Se não conseguir conectar
    """
    manager = get_mongodb_manager()

    with manager._connect_lock:
        if not manager.is_connected():
            manager.connect()

    return manager
