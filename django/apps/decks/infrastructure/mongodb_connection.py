"""
Gerenciador de Conexão MongoDB

Este módulo gerencia a conexão assíncrona com MongoDB usando Motor.
Implementa o padrão Singleton para garantir uma única instância de conexão
em toda a aplicação.

Características:
- Conexão assíncrona com Motor
- Singleton pattern
- Pool de conexões otimizado
- Reconexão automática
- Health check
"""

import asyncio
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from apps.decks.infrastructure.mongodb_config import get_mongodb_config, MongoDBConfig


class MongoDBConnectionManager:
    """
    Gerenciador de conexão MongoDB usando Motor (async).
    
    Implementa o padrão Singleton para garantir uma única instância
    de conexão em toda a aplicação.
    """
    
    _instance: Optional['MongoDBConnectionManager'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    _config: Optional[MongoDBConfig] = None
    
    def __new__(cls) -> 'MongoDBConnectionManager':
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
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config = get_mongodb_config()
    
    async def connect(self, config: Optional[MongoDBConfig] = None) -> None:
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
            raise ValueError("MongoDB configuration is required")
        
        try:
            # Cria cliente MongoDB com configurações otimizadas
            connection_params = self._config.get_connection_params()
            self._client = AsyncIOMotorClient(
                host=connection_params.pop("host"),
                port=connection_params.pop("port"),
                **connection_params
            )
            
            # Obtém referência do banco
            self._database = self._client[self._config.database]
            
            # Testa a conexão
            await self._test_connection()
            
            print(f"✅ MongoDB conectado: {self._config.host}:{self._config.port}/{self._config.database}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ Erro ao conectar MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """
        Fecha a conexão com MongoDB.
        """
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            print("🔌 MongoDB desconectado")
    
    async def _test_connection(self) -> None:
        """
        Testa a conexão com MongoDB.
        
        Raises:
            ConnectionFailure: Se a conexão falhar
        """
        try:
            # Ping no servidor para testar conexão
            await self._client.admin.command('ping')
        except Exception as e:
            raise ConnectionFailure(f"Failed to ping MongoDB server: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica a saúde da conexão MongoDB.
        
        Returns:
            Dicionário com informações de saúde
        """
        if not self.is_connected():
            return {
                "status": "disconnected",
                "error": "Not connected to MongoDB"
            }
        
        try:
            # Ping no servidor
            ping_result = await self._client.admin.command('ping')
            
            # Informações do servidor
            server_info = await self._client.server_info()
            
            # Estatísticas do banco
            db_stats = await self._database.command('dbStats')
            
            return {
                "status": "connected",
                "ping": ping_result,
                "server_version": server_info.get("version"),
                "database_name": self._config.database,
                "collections_count": db_stats.get("collections", 0),
                "data_size": db_stats.get("dataSize", 0),
                "storage_size": db_stats.get("storageSize", 0)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def is_connected(self) -> bool:
        """
        Verifica se está conectado ao MongoDB.
        
        Returns:
            True se conectado, False caso contrário
        """
        return self._client is not None and self._database is not None
    
    @property
    def client(self) -> AsyncIOMotorClient:
        """
        Retorna o cliente MongoDB.
        
        Returns:
            Cliente AsyncIOMotorClient
            
        Raises:
            RuntimeError: Se não estiver conectado
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self._client
    
    @property
    def database(self) -> AsyncIOMotorDatabase:
        """
        Retorna o banco de dados MongoDB.
        
        Returns:
            Banco AsyncIOMotorDatabase
            
        Raises:
            RuntimeError: Se não estiver conectado
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self._database
    
    @property
    def config(self) -> MongoDBConfig:
        """
        Retorna a configuração MongoDB.
        
        Returns:
            Configuração MongoDB
        """
        return self._config
    
    async def get_collection(self, collection_name: str):
        """
        Retorna uma collection do MongoDB.
        
        Args:
            collection_name: Nome da collection
            
        Returns:
            Collection MongoDB
        """
        return self.database[collection_name]
    
    async def create_indexes(self) -> None:
        """
        Cria índices otimizados para o sistema.
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        
        # Índices para collection cards
        cards_collection = await self.get_collection("cards")
        await cards_collection.create_index("deck_id")
        await cards_collection.create_index("word.normalized")
        await cards_collection.create_index("created_at")
        await cards_collection.create_index([("deck_id", 1), ("word.normalized", 1)], unique=True)
        
        # Índices para collection decks
        decks_collection = await self.get_collection("decks")
        await decks_collection.create_index("title")
        await decks_collection.create_index("created_at")
        await decks_collection.create_index("updated_at")
        
        # Índices para collection generation_sessions
        sessions_collection = await self.get_collection("generation_sessions")
        await sessions_collection.create_index("deck_id")
        await sessions_collection.create_index("status")
        await sessions_collection.create_index("created_at")
        await sessions_collection.create_index("completed_at")
        
        print("✅ Índices MongoDB criados com sucesso")
    
    async def drop_collection(self, collection_name: str) -> None:
        """
        Remove uma collection (apenas para desenvolvimento/testes).
        
        Args:
            collection_name: Nome da collection
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        
        await self.database.drop_collection(collection_name)
        print(f"🗑️ Collection '{collection_name}' removida")
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o banco de dados.
        
        Returns:
            Dicionário com informações do banco
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        
        db_stats = await self._database.command('dbStats')
        
        # Lista collections
        collections = await self._database.list_collection_names()
        
        return {
            "database_name": self._config.database,
            "collections": collections,
            "collections_count": db_stats.get("collections", 0),
            "data_size_bytes": db_stats.get("dataSize", 0),
            "storage_size_bytes": db_stats.get("storageSize", 0),
            "indexes_count": db_stats.get("indexes", 0),
            "objects_count": db_stats.get("objects", 0)
        }


# Instância global do gerenciador
mongodb_manager = MongoDBConnectionManager()


async def get_mongodb_manager() -> MongoDBConnectionManager:
    """
    Retorna a instância global do gerenciador MongoDB.
    
    Returns:
        Gerenciador MongoDB
    """
    return mongodb_manager


async def ensure_mongodb_connection() -> MongoDBConnectionManager:
    """
    Garante que a conexão MongoDB está estabelecida.
    
    Returns:
        Gerenciador MongoDB conectado
        
    Raises:
        ConnectionFailure: Se não conseguir conectar
    """
    manager = await get_mongodb_manager()
    
    if not manager.is_connected():
        await manager.connect()
    
    return manager
