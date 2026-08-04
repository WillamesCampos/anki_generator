"""
Serviço de Detecção de Duplicatas

Este serviço de domínio é responsável por detectar cards duplicados ou muito similares.
Ele implementa algoritmos de similaridade e regras de negócio para identificar
possíveis duplicatas no sistema.
"""

from typing import List, Tuple
from difflib import SequenceMatcher
import re

from ..entities.card import Card
from ..repositories.icard_repository import ICardRepository


class DuplicateDetectionService:
    """
    Serviço para detecção de duplicatas entre cards.
    
    Este serviço implementa diferentes estratégias para detectar cards similares:
    - Comparação exata de palavras
    - Similaridade textual (difflib)
    - Análise de contexto
    - Verificação de traduções similares
    """
    
    def __init__(self, card_repository: ICardRepository):
        """
        Inicializa o serviço com o repositório de cards.
        
        Args:
            card_repository: Repositório para buscar cards existentes
        """
        self.card_repository = card_repository
    
    async def find_duplicates_for_card(self, card: Card, similarity_threshold: float = 0.8) -> List[Tuple[Card, float]]:
        """
        Busca cards duplicados ou similares para um card específico.
        
        Args:
            card: Card para verificar duplicatas
            similarity_threshold: Limiar de similaridade (0.0 a 1.0)
            
        Returns:
            Lista de tuplas (card_duplicado, score_similaridade)
        """
        duplicates = []
        
        # Busca cards existentes no mesmo deck
        if card.deck_id:
            existing_cards = await self.card_repository.find_by_deck_id(card.deck_id)
        else:
            # Se não tem deck_id, busca todos os cards
            existing_cards = await self._get_all_cards()
        
        for existing_card in existing_cards:
            # Não compara com o próprio card
            if existing_card.id == card.id:
                continue
            
            similarity_score = self._calculate_similarity(card, existing_card)
            
            if similarity_score >= similarity_threshold:
                duplicates.append((existing_card, similarity_score))
        
        # Ordena por score de similaridade (maior primeiro)
        duplicates.sort(key=lambda x: x[1], reverse=True)
        
        return duplicates
    
    async def find_exact_duplicates(self, word: str, deck_id: str = None) -> List[Card]:
        """
        Busca duplicatas exatas de uma palavra.
        
        Args:
            word: Palavra para verificar
            deck_id: ID do deck (opcional)
            
        Returns:
            Lista de cards com a mesma palavra
        """
        return await self.card_repository.find_by_word(word)
    
    async def find_similar_words(self, word: str, similarity_threshold: float = 0.7) -> List[Tuple[Card, float]]:
        """
        Busca palavras similares usando algoritmos de similaridade.
        
        Args:
            word: Palavra para comparar
            similarity_threshold: Limiar de similaridade
            
        Returns:
            Lista de tuplas (card, score_similaridade)
        """
        all_cards = await self._get_all_cards()
        similar_cards = []
        
        word_normalized = word.lower().strip()
        
        for card in all_cards:
            card_word_normalized = card.word.normalized
            
            # Calcula similaridade usando difflib
            similarity = SequenceMatcher(None, word_normalized, card_word_normalized).ratio()
            
            if similarity >= similarity_threshold:
                similar_cards.append((card, similarity))
        
        # Ordena por score de similaridade
        similar_cards.sort(key=lambda x: x[1], reverse=True)
        
        return similar_cards
    
    def _calculate_similarity(self, card1: Card, card2: Card) -> float:
        """
        Calcula a similaridade entre dois cards.
        
        Usa múltiplos critérios:
        - Similaridade da palavra (peso 0.6)
        - Similaridade da tradução (peso 0.3)
        - Similaridade do exemplo (peso 0.1)
        
        Args:
            card1: Primeiro card
            card2: Segundo card
            
        Returns:
            Score de similaridade (0.0 a 1.0)
        """
        # Similaridade da palavra
        word_similarity = SequenceMatcher(
            None, 
            card1.word.normalized, 
            card2.word.normalized
        ).ratio()
        
        # Similaridade da tradução
        translation_similarity = SequenceMatcher(
            None,
            card1.translation.normalized,
            card2.translation.normalized
        ).ratio()
        
        # Similaridade do exemplo
        example_similarity = SequenceMatcher(
            None,
            card1.example.original_normalized,
            card2.example.original_normalized
        ).ratio()
        
        # Calcula score ponderado
        weighted_score = (
            word_similarity * 0.6 +
            translation_similarity * 0.3 +
            example_similarity * 0.1
        )
        
        return weighted_score
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto para comparação.
        
        Args:
            text: Texto para normalizar
            
        Returns:
            Texto normalizado
        """
        if not text:
            return ""
        
        # Converte para lowercase
        normalized = text.lower()
        
        # Remove pontuação
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove espaços múltiplos
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    def are_translations_similar(self, translation1: str, translation2: str, threshold: float = 0.8) -> bool:
        """
        Verifica se duas traduções são similares.
        
        Args:
            translation1: Primeira tradução
            translation2: Segunda tradução
            threshold: Limiar de similaridade
            
        Returns:
            True se as traduções são similares
        """
        norm1 = self._normalize_text(translation1)
        norm2 = self._normalize_text(translation2)
        
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        return similarity >= threshold
    
    def suggest_alternatives(self, word: str, existing_cards: List[Card]) -> List[str]:
        """
        Sugere alternativas para uma palavra que pode ser duplicada.
        
        Args:
            word: Palavra original
            existing_cards: Cards existentes similares
            
        Returns:
            Lista de sugestões alternativas
        """
        suggestions = []
        
        # Se é uma palavra simples, sugere variações
        if len(word.split()) == 1:
            # Adiciona sufixos comuns
            suffixes = ['ing', 'ed', 's', 'ly']
            for suffix in suffixes:
                if not word.endswith(suffix):
                    suggestions.append(f"{word}{suffix}")
            
            # Adiciona prefixos comuns
            prefixes = ['un', 're', 'pre', 'mis']
            for prefix in prefixes:
                if not word.startswith(prefix):
                    suggestions.append(f"{prefix}{word}")
        
        # Sugere frases relacionadas baseadas nos cards existentes
        for card in existing_cards:
            if card.example.word_count > 1:
                # Extrai outras palavras do exemplo
                example_words = card.example.original.split()
                for example_word in example_words:
                    if example_word.lower() != word.lower() and len(example_word) > 3:
                        suggestions.append(example_word)
        
        # Remove duplicatas e limita a 5 sugestões
        unique_suggestions = list(set(suggestions))[:5]
        
        return unique_suggestions
    
    async def _get_all_cards(self) -> List[Card]:
        """
        Busca todos os cards do repositório.
        
        Returns:
            Lista de todos os cards
        """
        # Como não temos um método find_all no repositório, vamos simular
        # Em uma implementação real, seria necessário adicionar esse método
        # Por enquanto, retornamos lista vazia
        return []
    
    def validate_card_uniqueness(self, card: Card, existing_cards: List[Card]) -> Tuple[bool, List[str]]:
        """
        Valida se um card é único comparado com cards existentes.
        
        Args:
            card: Card para validar
            existing_cards: Lista de cards existentes
            
        Returns:
            Tupla (é_único, lista_de_problemas)
        """
        problems = []
        
        for existing_card in existing_cards:
            # Verifica duplicata exata
            if card.word.normalized == existing_card.word.normalized:
                problems.append(f"Palavra '{card.word.value}' já existe no card {existing_card.id}")
                continue
            
            # Verifica similaridade alta
            similarity = self._calculate_similarity(card, existing_card)
            if similarity > 0.9:
                problems.append(f"Card muito similar (similaridade: {similarity:.2f}) ao card {existing_card.id}")
            
            # Verifica traduções muito similares
            if self.are_translations_similar(card.translation.value, existing_card.translation.value):
                problems.append(f"Tradução muito similar ao card {existing_card.id}")
        
        is_unique = len(problems) == 0
        
        return is_unique, problems
