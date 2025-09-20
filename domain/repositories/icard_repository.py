"""
Interface ICardRepository - Define operações de persistência para Cards

Esta interface define todas as operações necessárias para persistir e recuperar
cards do banco de dados. A implementação concreta ficará na camada de infraestrutura.

Princípios:
- Interface segregation: Define apenas operações específicas para Cards
- Dependency inversion: O domínio depende da abstração, não da implementação
- Single responsibility: Responsável apenas por operações de Card
"""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.card import Card


class ICardRepository(ABC):
    """
    Interface para repositório de Cards.
    
    Define todas as operações de persistência necessárias para a entidade Card.
    """
    
    @abstractmethod
    async def save(self, card: Card) -> Card:
        """
        Salva um card no banco de dados.
        
        Args:
            card: Card a ser salvo
            
        Returns:
            Card salvo (com ID gerado se for novo)
            
        Raises:
            RepositoryError: Se houver erro na persistência
        """
        pass
    
    @abstractmethod
    async def save_many(self, cards: List[Card]) -> List[Card]:
        """
        Salva múltiplos cards no banco de dados.
        
        Args:
            cards: Lista de cards a serem salvos
            
        Returns:
            Lista de cards salvos
            
        Raises:
            RepositoryError: Se houver erro na persistência
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, card_id: uuid.UUID) -> Optional[Card]:
        """
        Busca um card pelo ID.
        
        Args:
            card_id: ID do card
            
        Returns:
            Card se encontrado, None caso contrário
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_word(self, word: str) -> List[Card]:
        """
        Busca cards por palavra.
        
        Args:
            word: Palavra para buscar (case insensitive)
            
        Returns:
            Lista de cards que contêm a palavra
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_deck_id(self, deck_id: uuid.UUID) -> List[Card]:
        """
        Busca todos os cards de um deck.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            Lista de cards do deck
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_context(self, context: str) -> List[Card]:
        """
        Busca cards por contexto.
        
        Args:
            context: Contexto para buscar
            
        Returns:
            Lista de cards que usam o contexto
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_similar_cards(self, word: str, similarity_threshold: float = 0.8) -> List[Card]:
        """
        Busca cards similares à palavra especificada.
        
        Args:
            word: Palavra para comparar
            similarity_threshold: Limiar de similaridade (0.0 a 1.0)
            
        Returns:
            Lista de cards similares
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_duplicates(self, card: Card) -> List[Card]:
        """
        Busca cards duplicados ou muito similares.
        
        Args:
            card: Card para verificar duplicatas
            
        Returns:
            Lista de cards duplicados/similares
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def update(self, card: Card) -> Card:
        """
        Atualiza um card existente.
        
        Args:
            card: Card com dados atualizados
            
        Returns:
            Card atualizado
            
        Raises:
            RepositoryError: Se houver erro na atualização
            CardNotFoundError: Se o card não existir
        """
        pass
    
    @abstractmethod
    async def delete(self, card_id: uuid.UUID) -> bool:
        """
        Remove um card do banco de dados.
        
        Args:
            card_id: ID do card a ser removido
            
        Returns:
            True se o card foi removido, False se não foi encontrado
            
        Raises:
            RepositoryError: Se houver erro na remoção
        """
        pass
    
    @abstractmethod
    async def delete_by_deck_id(self, deck_id: uuid.UUID) -> int:
        """
        Remove todos os cards de um deck.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            Número de cards removidos
            
        Raises:
            RepositoryError: Se houver erro na remoção
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Conta o total de cards no banco.
        
        Returns:
            Número total de cards
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        pass
    
    @abstractmethod
    async def count_by_deck_id(self, deck_id: uuid.UUID) -> int:
        """
        Conta o número de cards de um deck.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            Número de cards do deck
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        pass
    
    @abstractmethod
    async def exists(self, card_id: uuid.UUID) -> bool:
        """
        Verifica se um card existe.
        
        Args:
            card_id: ID do card
            
        Returns:
            True se o card existe, False caso contrário
            
        Raises:
            RepositoryError: Se houver erro na verificação
        """
        pass
    
    @abstractmethod
    async def exists_by_word(self, word: str, deck_id: Optional[uuid.UUID] = None) -> bool:
        """
        Verifica se já existe um card com a palavra especificada.
        
        Args:
            word: Palavra para verificar
            deck_id: ID do deck (opcional, para verificar apenas em um deck)
            
        Returns:
            True se já existe um card com essa palavra
            
        Raises:
            RepositoryError: Se houver erro na verificação
        """
        pass
