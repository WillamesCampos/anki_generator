"""
Configurações Compartilhadas

Este módulo contém todas as configurações compartilhadas da aplicação,
incluindo banco de dados, APIs externas e outras configurações globais.
"""

from .database import MongoDBConfig, get_mongodb_config, set_mongodb_config

__all__ = [
    'MongoDBConfig',
    'get_mongodb_config',
    'set_mongodb_config'
]
