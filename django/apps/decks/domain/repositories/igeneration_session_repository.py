"""
Interface IGenerationSessionRepository - Define operações de persistência para GenerationSessions

Esta interface define todas as operações necessárias para persistir e recuperar
sessões de geração do banco de dados.
"""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.generation_session import GenerationSession, GenerationStatus


class IGenerationSessionRepository(ABC):
    """
    Interface para repositório de GenerationSessions.
    
    Define todas as operações de persistência necessárias para a entidade GenerationSession.
    """
    
    @abstractmethod
    async def save(self, session: GenerationSession) -> GenerationSession:
        """
        Salva uma sessão de geração no banco de dados.
        
        Args:
            session: Sessão a ser salva
            
        Returns:
            Sessão salva (com ID gerado se for nova)
            
        Raises:
            RepositoryError: Se houver erro na persistência
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, session_id: uuid.UUID) -> Optional[GenerationSession]:
        """
        Busca uma sessão pelo ID.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Sessão se encontrada, None caso contrário
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_deck_id(self, deck_id: uuid.UUID) -> List[GenerationSession]:
        """
        Busca todas as sessões de um deck.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            Lista de sessões do deck
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: GenerationStatus) -> List[GenerationSession]:
        """
        Busca sessões por status.
        
        Args:
            status: Status das sessões
            
        Returns:
            Lista de sessões com o status especificado
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_by_context(self, context: str) -> List[GenerationSession]:
        """
        Busca sessões por contexto.
        
        Args:
            context: Contexto para buscar
            
        Returns:
            Lista de sessões que usam o contexto
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_active_sessions(self, deck_id: Optional[uuid.UUID] = None) -> List[GenerationSession]:
        """
        Busca sessões ativas (não finalizadas).
        
        Args:
            deck_id: ID do deck (opcional, para filtrar por deck)
            
        Returns:
            Lista de sessões ativas
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_finished_sessions(self, deck_id: Optional[uuid.UUID] = None) -> List[GenerationSession]:
        """
        Busca sessões finalizadas (concluídas, falhadas ou canceladas).
        
        Args:
            deck_id: ID do deck (opcional, para filtrar por deck)
            
        Returns:
            Lista de sessões finalizadas
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def find_recent_sessions(self, limit: int = 10, deck_id: Optional[uuid.UUID] = None) -> List[GenerationSession]:
        """
        Busca as sessões mais recentes.
        
        Args:
            limit: Número máximo de sessões a retornar
            deck_id: ID do deck (opcional, para filtrar por deck)
            
        Returns:
            Lista de sessões ordenadas por data de criação (mais recentes primeiro)
            
        Raises:
            RepositoryError: Se houver erro na consulta
        """
        pass
    
    @abstractmethod
    async def update(self, session: GenerationSession) -> GenerationSession:
        """
        Atualiza uma sessão existente.
        
        Args:
            session: Sessão com dados atualizados
            
        Returns:
            Sessão atualizada
            
        Raises:
            RepositoryError: Se houver erro na atualização
            SessionNotFoundError: Se a sessão não existir
        """
        pass
    
    @abstractmethod
    async def delete(self, session_id: uuid.UUID) -> bool:
        """
        Remove uma sessão do banco de dados.
        
        Args:
            session_id: ID da sessão a ser removida
            
        Returns:
            True se a sessão foi removida, False se não foi encontrada
            
        Raises:
            RepositoryError: Se houver erro na remoção
        """
        pass
    
    @abstractmethod
    async def delete_by_deck_id(self, deck_id: uuid.UUID) -> int:
        """
        Remove todas as sessões de um deck.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            Número de sessões removidas
            
        Raises:
            RepositoryError: Se houver erro na remoção
        """
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """
        Conta o total de sessões no banco.
        
        Returns:
            Número total de sessões
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        pass
    
    @abstractmethod
    async def count_by_deck_id(self, deck_id: uuid.UUID) -> int:
        """
        Conta o número de sessões de um deck.
        
        Args:
            deck_id: ID do deck
            
        Returns:
            Número de sessões do deck
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: GenerationStatus) -> int:
        """
        Conta o número de sessões com um status específico.
        
        Args:
            status: Status das sessões
            
        Returns:
            Número de sessões com o status
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        pass
    
    @abstractmethod
    async def exists(self, session_id: uuid.UUID) -> bool:
        """
        Verifica se uma sessão existe.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se a sessão existe, False caso contrário
            
        Raises:
            RepositoryError: Se houver erro na verificação
        """
        pass
    
    @abstractmethod
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """
        Remove sessões antigas (para limpeza de dados).
        
        Args:
            days_old: Número de dias para considerar uma sessão como antiga
            
        Returns:
            Número de sessões removidas
            
        Raises:
            RepositoryError: Se houver erro na limpeza
        """
        pass
