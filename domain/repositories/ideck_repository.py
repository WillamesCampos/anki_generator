"""
Interface IDeckRepository - Define operações de persistência para Decks

Esta interface define todas as operações necessárias para persistir e recuperar
decks do banco de dados.
"""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.deck import Deck


class IDeckRepository(ABC):
    """
    Interface para repositório de Decks.
    
    Define todas as operações de persistência necessárias para a entidade Deck.
    """
    
    @abstractmethod
    async def save(self, deck: Deck) -> Deck:
        """
        Salva um deck no banco de dados.
        
        Args:
            deck: Deck a ser salvo
            
        Returns:
            Deck salvo (com ID gerado se for novo)
            
        Raises:
            RepositoryError: Se houver erro na persistência
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, deck_id: uuid.UUID) -> Optional[Deck]:
        """
        Busca um deck pelo ID.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            Deck se encontrado, None caso contrário
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_title(self, title: str) -> List[Deck]:
        """
        Busca decks por título.
        
        Args:
            title: Título para buscar (case insensitive)
            
        Returns:
            Lista de decks com títulos similares
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Deck]:
        """
        Busca todos os decks com paginação.
        
        Args:
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de decks
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Deck]:
        """
        Busca decks de um usuário específico.
        
        Args:
            user_id: ID do usuário
            skip: Número de registros para pular
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de decks do usuário
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def update(self, deck: Deck) -> Deck:
        """
        Atualiza um deck existente.
        
        Args:
            deck: Deck com dados atualizados
            
        Returns:
            Deck atualizado
            
        Raises:
            RepositoryError: Se houver erro na atualização
            DeckNotFoundError: Se o deck não existir
        """
        pass
    
    @abstractmethod
    async def delete(self, deck_id: uuid.UUID) -> bool:
        """
        Remove um deck do banco de dados.
        
        Args:
            deck_id: ID do deck a ser removido
            
        Returns:
            True se o deck foi removido, False se não foi encontrado
            
        Raises:
            RepositoryError: Se houver erro na remoção
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Conta o total de decks no banco.
        
        Returns:
            Número total de decks
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        pass
    
    @abstractmethod
    async def count_by_user_id(self, user_id: str) -> int:
        """
        Conta o número de decks de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Número de decks do usuário
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        pass
    
    @abstractmethod
    async def exists(self, deck_id: uuid.UUID) -> bool:
        """
        Verifica se um deck existe.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            True se o deck existe, False caso contrário
            
        Raises:
            RepositoryError: Se houver erro na verificação
        """
        pass
    
    @abstractmethod
    async def exists_by_title(self, title: str, user_id: Optional[str] = None) -> bool:
        """
        Verifica se já existe um deck com o título especificado.
        
        Args:
            title: Título para verificar
            user_id: ID do usuário (opcional, para verificar apenas para um usuário)
            
        Returns:
            True se já existe um deck com esse título
            
        Raises:
            RepositoryError: Se houver erro na verificação
        """
        pass
