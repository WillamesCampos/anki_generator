"""
Implementação MongoDB do CardRepository

Este módulo implementa a interface ICardRepository usando MongoDB como
banco de dados. Utiliza Motor para operações assíncronas e implementa
todas as operações definidas na interface.

Características:
- Operações assíncronas com Motor
- Validação de dados com schemas
- Tratamento de erros específicos
- Otimizações de performance
"""

import uuid
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson import ObjectId

from domain.entities.card import Card
from domain.repositories.icard_repository import ICardRepository
from infrastructure.database.mongodb_connection import ensure_mongodb_connection
from infrastructure.database.schemas import CardSchema


class RepositoryError(Exception):
    """
    Exceção base para erros de repositório.
    """
    pass


class CardNotFoundError(RepositoryError):
    """
    Exceção para quando um card não é encontrado.
    """
    pass


class CardRepository(ICardRepository):
    """
    Implementação MongoDB do CardRepository.
    
    Implementa todas as operações definidas na interface ICardRepository
    usando MongoDB como banco de dados.
    """
    
    def __init__(self):
        """
        Inicializa o repositório.
        """
        self._collection_name = "cards"
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    async def _get_collection(self) -> AsyncIOMotorCollection:
        """
        Retorna a collection MongoDB.
        
        Returns:
            Collection MongoDB
            
        Raises:
            RepositoryError: Se não conseguir conectar
        """
        if self._collection is None:
            try:
                mongodb_manager = await ensure_mongodb_connection()
                self._collection = await mongodb_manager.get_collection(self._collection_name)
            except Exception as e:
                raise RepositoryError(f"Failed to get MongoDB collection: {e}")
        
        return self._collection
    
    async def save(self, card: Card) -> Card:
        """
        Salva um card no banco de dados.
        
        Args:
            card: Card a ser salvo
            
        Returns:
            Card salvo
            
        Raises:
            RepositoryError: Se houver erro na persistência
        """
        try:
            collection = await self._get_collection()
            card_data = card.to_dict()
            document = CardSchema.to_document(card_data)
            
            # Insere o documento
            result = await collection.insert_one(document)
            
            # Atualiza o ID do card com o ObjectId gerado
            card.id = uuid.UUID(str(result.inserted_id))
            
            return card
            
        except DuplicateKeyError as e:
            raise RepositoryError(f"Card with duplicate key: {e}")
        except Exception as e:
            raise RepositoryError(f"Failed to save card: {e}")
    
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
        if not cards:
            return []
        
        try:
            collection = await self._get_collection()
            documents = []
            
            # Converte todos os cards para documentos
            for card in cards:
                card_data = card.to_dict()
                document = CardSchema.to_document(card_data)
                documents.append(document)
            
            # Insere todos os documentos
            result = await collection.insert_many(documents)
            
            # Atualiza os IDs dos cards
            for i, card in enumerate(cards):
                card.id = uuid.UUID(str(result.inserted_ids[i]))
            
            return cards
            
        except Exception as e:
            raise RepositoryError(f"Failed to save cards: {e}")
    
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
        try:
            collection = await self._get_collection()
            document = await collection.find_one({"_id": ObjectId(str(card_id))})
            
            if document is None:
                return None
            
            card_data = CardSchema.from_document(document)
            return Card.from_dict(card_data)
            
        except Exception as e:
            raise RepositoryError(f"Failed to find card by ID: {e}")
    
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
        try:
            collection = await self._get_collection()
            word_normalized = word.lower().strip()
            
            # Busca por palavra normalizada
            cursor = collection.find({"word.normalized": word_normalized})
            documents = await cursor.to_list(length=None)
            
            cards = []
            for document in documents:
                card_data = CardSchema.from_document(document)
                card = Card.from_dict(card_data)
                cards.append(card)
            
            return cards
            
        except Exception as e:
            raise RepositoryError(f"Failed to find cards by word: {e}")
    
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
        try:
            collection = await self._get_collection()
            cursor = collection.find({"deck_id": ObjectId(str(deck_id))})
            documents = await cursor.to_list(length=None)
            
            cards = []
            for document in documents:
                card_data = CardSchema.from_document(document)
                card = Card.from_dict(card_data)
                cards.append(card)
            
            return cards
            
        except Exception as e:
            raise RepositoryError(f"Failed to find cards by deck ID: {e}")
    
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
        try:
            collection = await self._get_collection()
            cursor = collection.find({"context": context})
            documents = await cursor.to_list(length=None)
            
            cards = []
            for document in documents:
                card_data = CardSchema.from_document(document)
                card = Card.from_dict(card_data)
                cards.append(card)
            
            return cards
            
        except Exception as e:
            raise RepositoryError(f"Failed to find cards by context: {e}")
    
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
        try:
            collection = await self._get_collection()
            word_normalized = word.lower().strip()
            
            # Usa regex para busca parcial (implementação simples)
            # Em uma implementação mais sofisticada, usaria text search ou aggregation
            regex_pattern = f".*{word_normalized}.*"
            
            cursor = collection.find({
                "$or": [
                    {"word.normalized": {"$regex": regex_pattern, "$options": "i"}},
                    {"translation.normalized": {"$regex": regex_pattern, "$options": "i"}}
                ]
            })
            
            documents = await cursor.to_list(length=None)
            
            cards = []
            for document in documents:
                card_data = CardSchema.from_document(document)
                card = Card.from_dict(card_data)
                cards.append(card)
            
            return cards
            
        except Exception as e:
            raise RepositoryError(f"Failed to find similar cards: {e}")
    
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
        try:
            collection = await self._get_collection()
            
            # Busca por palavra exata
            exact_matches = await collection.find({
                "word.normalized": card.word.normalized
            }).to_list(length=None)
            
            cards = []
            for document in exact_matches:
                # Não inclui o próprio card
                if str(document["_id"]) != str(card.id):
                    card_data = CardSchema.from_document(document)
                    duplicate_card = Card.from_dict(card_data)
                    cards.append(duplicate_card)
            
            return cards
            
        except Exception as e:
            raise RepositoryError(f"Failed to find duplicates: {e}")
    
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
        try:
            collection = await self._get_collection()
            card_data = card.to_dict()
            document = CardSchema.to_document(card_data)
            
            # Remove o _id do documento para atualização
            document.pop("_id", None)
            
            result = await collection.replace_one(
                {"_id": ObjectId(str(card.id))},
                document
            )
            
            if result.matched_count == 0:
                raise CardNotFoundError(f"Card with ID {card.id} not found")
            
            return card
            
        except CardNotFoundError:
            raise
        except Exception as e:
            raise RepositoryError(f"Failed to update card: {e}")
    
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
        try:
            collection = await self._get_collection()
            result = await collection.delete_one({"_id": ObjectId(str(card_id))})
            
            return result.deleted_count > 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to delete card: {e}")
    
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
        try:
            collection = await self._get_collection()
            result = await collection.delete_many({"deck_id": ObjectId(str(deck_id))})
            
            return result.deleted_count
            
        except Exception as e:
            raise RepositoryError(f"Failed to delete cards by deck ID: {e}")
    
    async def count(self) -> int:
        """
        Conta o total de cards no banco.
        
        Returns:
            Número total de cards
            
        Raises:
            RepositoryError: Se houver erro na contagem
        """
        try:
            collection = await self._get_collection()
            return await collection.count_documents({})
            
        except Exception as e:
            raise RepositoryError(f"Failed to count cards: {e}")
    
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
        try:
            collection = await self._get_collection()
            return await collection.count_documents({"deck_id": ObjectId(str(deck_id))})
            
        except Exception as e:
            raise RepositoryError(f"Failed to count cards by deck ID: {e}")
    
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
        try:
            collection = await self._get_collection()
            count = await collection.count_documents({"_id": ObjectId(str(card_id))})
            return count > 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to check if card exists: {e}")
    
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
        try:
            collection = await self._get_collection()
            word_normalized = word.lower().strip()
            
            query = {"word.normalized": word_normalized}
            if deck_id:
                query["deck_id"] = ObjectId(str(deck_id))
            
            count = await collection.count_documents(query)
            return count > 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to check if word exists: {e}")
