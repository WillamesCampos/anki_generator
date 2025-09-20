"""
Configuração do Banco de Dados MongoDB

Este módulo centraliza todas as configurações relacionadas ao MongoDB,
incluindo conexão, configurações de performance e variáveis de ambiente.

Características:
- Configuração centralizada
- Suporte a variáveis de ambiente
- Configurações de performance otimizadas
- Validação de configurações
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv


# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


@dataclass
class MongoDBConfig:
    """
    Configuração para conexão com MongoDB.
    
    Atributos:
    - host: Host do MongoDB
    - port: Porta do MongoDB
    - username: Nome de usuário (opcional)
    - password: Senha (opcional)
    - database: Nome do banco de dados
    - auth_source: Banco de autenticação
    - max_pool_size: Tamanho máximo do pool de conexões
    - min_pool_size: Tamanho mínimo do pool de conexões
    - max_idle_time_ms: Tempo máximo de idle das conexões
    - connect_timeout_ms: Timeout para conexão
    - server_selection_timeout_ms: Timeout para seleção de servidor
    """
    
    # Configurações de conexão
    host: str = "localhost"
    port: int = 27017
    username: Optional[str] = None
    password: Optional[str] = None
    database: str = "anki_generator"
    auth_source: str = "admin"
    
    # Configurações de performance
    max_pool_size: int = 100
    min_pool_size: int = 10
    max_idle_time_ms: int = 30000
    connect_timeout_ms: int = 20000
    server_selection_timeout_ms: int = 5000
    
    # Configurações de SSL (para produção)
    ssl: bool = False
    ssl_cert_reqs: str = "CERT_REQUIRED"
    ssl_ca_certs: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'MongoDBConfig':
        """
        Cria configuração a partir de variáveis de ambiente.
        
        Variáveis de ambiente suportadas:
        - MONGODB_HOST: Host do MongoDB (padrão: localhost)
        - MONGODB_PORT: Porta do MongoDB (padrão: 27017)
        - MONGODB_USERNAME: Nome de usuário (opcional)
        - MONGODB_PASSWORD: Senha (opcional)
        - MONGODB_DATABASE: Nome do banco (padrão: anki_generator)
        - MONGODB_AUTH_SOURCE: Banco de autenticação (padrão: admin)
        - MONGODB_MAX_POOL_SIZE: Tamanho máximo do pool (padrão: 100)
        - MONGODB_MIN_POOL_SIZE: Tamanho mínimo do pool (padrão: 10)
        - MONGODB_SSL: Usar SSL (padrão: false)
        
        Returns:
            Configuração MongoDB criada
        """
        return cls(
            host=os.getenv("MONGODB_HOST", "localhost"),
            port=int(os.getenv("MONGODB_PORT", "27017")),
            username=os.getenv("MONGODB_USERNAME"),
            password=os.getenv("MONGODB_PASSWORD"),
            database=os.getenv("MONGODB_DATABASE", "anki_generator"),
            auth_source=os.getenv("MONGODB_AUTH_SOURCE", "admin"),
            max_pool_size=int(os.getenv("MONGODB_MAX_POOL_SIZE", "100")),
            min_pool_size=int(os.getenv("MONGODB_MIN_POOL_SIZE", "10")),
            max_idle_time_ms=int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "30000")),
            connect_timeout_ms=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "20000")),
            server_selection_timeout_ms=int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")),
            ssl=os.getenv("MONGODB_SSL", "false").lower() == "true",
            ssl_cert_reqs=os.getenv("MONGODB_SSL_CERT_REQS", "CERT_REQUIRED"),
            ssl_ca_certs=os.getenv("MONGODB_SSL_CA_CERTS")
        )
    
    def get_connection_string(self) -> str:
        """
        Gera a string de conexão MongoDB.
        
        Returns:
            String de conexão formatada
        """
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?authSource={self.auth_source}"
        else:
            return f"mongodb://{self.host}:{self.port}/{self.database}"
    
    def get_connection_params(self) -> dict:
        """
        Retorna parâmetros de conexão como dicionário.
        
        Returns:
            Dicionário com parâmetros de conexão
        """
        params = {
            "host": self.host,
            "port": self.port,
            "maxPoolSize": self.max_pool_size,
            "minPoolSize": self.min_pool_size,
            "maxIdleTimeMS": self.max_idle_time_ms,
            "connectTimeoutMS": self.connect_timeout_ms,
            "serverSelectionTimeoutMS": self.server_selection_timeout_ms,
        }
        
        # Adiciona autenticação se configurada
        if self.username and self.password:
            params.update({
                "username": self.username,
                "password": self.password,
                "authSource": self.auth_source,
            })
        
        # Adiciona SSL se configurado
        if self.ssl:
            params.update({
                "ssl": self.ssl,
                "ssl_cert_reqs": self.ssl_cert_reqs,
            })
            
            if self.ssl_ca_certs:
                params["ssl_ca_certs"] = self.ssl_ca_certs
        
        return params
    
    def validate(self) -> None:
        """
        Valida a configuração.
        
        Raises:
            ValueError: Se a configuração for inválida
        """
        if not self.host:
            raise ValueError("MongoDB host cannot be empty")
        
        if not (1 <= self.port <= 65535):
            raise ValueError("MongoDB port must be between 1 and 65535")
        
        if not self.database:
            raise ValueError("MongoDB database name cannot be empty")
        
        if self.max_pool_size < 1:
            raise ValueError("Max pool size must be at least 1")
        
        if self.min_pool_size < 0:
            raise ValueError("Min pool size cannot be negative")
        
        if self.min_pool_size > self.max_pool_size:
            raise ValueError("Min pool size cannot be greater than max pool size")
    
    def __str__(self) -> str:
        """
        Representação string da configuração (sem senha).
        """
        return f"MongoDBConfig(host={self.host}, port={self.port}, database={self.database}, ssl={self.ssl})"


# Configuração global (singleton)
_config: Optional[MongoDBConfig] = None


def get_mongodb_config() -> MongoDBConfig:
    """
    Retorna a configuração MongoDB global.
    
    Returns:
        Configuração MongoDB
    """
    global _config
    
    if _config is None:
        _config = MongoDBConfig.from_env()
        _config.validate()
    
    return _config


def set_mongodb_config(config: MongoDBConfig) -> None:
    """
    Define a configuração MongoDB global.
    
    Args:
        config: Nova configuração
    """
    global _config
    
    config.validate()
    _config = config
