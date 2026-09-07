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

    async def find_duplicates_for_card(
        self, card: Card, similarity_threshold: float = 0.8
    ) -> List[Tuple[Card, float]]:
        """
        Busca cards duplicados ou similares para um card específico, dentro
        do mesmo owner (isolamento multi-tenant — card.owner_id já identifica
        o dono, ver D1 em openspec/changes/sprint-2-decks-cards/design.md).

        Args:
            card: Card para verificar duplicatas
            similarity_threshold: Limiar de similaridade (0.0 a 1.0)

        Returns:
            Lista de tuplas (card_duplicado, score_similaridade)
        """
        duplicates = []

        # Busca cards existentes no mesmo deck
        if card.deck_id:
            existing_cards = await self.card_repository.find_by_deck_id(
                card.deck_id, card.owner_id
            )
        else:
            # Se não tem deck_id, busca todos os cards do mesmo owner
            existing_cards = await self._get_all_cards(card.owner_id)

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

    async def find_exact_duplicates(
        self, front: str, owner_id: str, deck_id: str = None
    ) -> List[Card]:
        """
        Busca duplicatas exatas de uma palavra, dentro do owner especificado.

        Args:
            front: Frente para verificar
            owner_id: dono dos cards (isolamento multi-tenant)
            deck_id: ID do deck (opcional)

        Returns:
            Lista de cards com a mesma palavra
        """
        return await self.card_repository.find_by_front(front, owner_id)

    async def find_similar_fronts(
        self, front: str, owner_id: str, similarity_threshold: float = 0.7
    ) -> List[Tuple[Card, float]]:
        """
        Busca palavras similares usando algoritmos de similaridade, dentro
        do owner especificado.

        Args:
            front: Frente para comparar
            owner_id: dono dos cards (isolamento multi-tenant)
            similarity_threshold: Limiar de similaridade

        Returns:
            Lista de tuplas (card, score_similaridade)
        """
        all_cards = await self._get_all_cards(owner_id)
        similar_cards = []

        front_normalized = front.lower().strip()

        for card in all_cards:
            card_front_normalized = card.front.normalized

            # Calcula similaridade usando difflib
            similarity = SequenceMatcher(
                None, front_normalized, card_front_normalized
            ).ratio()

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
        front_similarity = SequenceMatcher(
            None, card1.front.normalized, card2.front.normalized
        ).ratio()

        # Similaridade da tradução
        back_similarity = SequenceMatcher(
            None, card1.back.normalized, card2.back.normalized
        ).ratio()

        # Similaridade do exemplo
        description_similarity = SequenceMatcher(
            None,
            self._normalize_text(card1.front_description),
            self._normalize_text(card2.front_description),
        ).ratio()

        # Calcula score ponderado
        weighted_score = (
            front_similarity * 0.6
            + back_similarity * 0.3
            + description_similarity * 0.1
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
        normalized = re.sub(r"[^\w\s]", "", normalized)

        # Remove espaços múltiplos
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.strip()

    def are_backs_similar(self, back1: str, back2: str, threshold: float = 0.8) -> bool:
        """
        Verifica se duas traduções são similares.

        Args:
            back1: Primeiro back
            back2: Segundo back
            threshold: Limiar de similaridade

        Returns:
            True se as traduções são similares
        """
        norm1 = self._normalize_text(back1)
        norm2 = self._normalize_text(back2)

        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        return similarity >= threshold

    def suggest_alternatives(self, front: str, existing_cards: List[Card]) -> List[str]:
        """
        Sugere alternativas para uma palavra que pode ser duplicada.

        Args:
            front: Frente original
            existing_cards: Cards existentes similares

        Returns:
            Lista de sugestões alternativas
        """
        suggestions = []

        # Se é uma palavra simples, sugere variações
        if len(front.split()) == 1:
            # Adiciona sufixos comuns
            suffixes = ["ing", "ed", "s", "ly"]
            for suffix in suffixes:
                if not front.endswith(suffix):
                    suggestions.append(f"{front}{suffix}")

            # Adiciona prefixos comuns
            prefixes = ["un", "re", "pre", "mis"]
            for prefix in prefixes:
                if not front.startswith(prefix):
                    suggestions.append(f"{prefix}{front}")

        # Sugere frases relacionadas baseadas nos cards existentes
        for card in existing_cards:
            if len(card.front_description.split()) > 1:
                # Extrai outras palavras do exemplo
                example_words = card.front_description.split()
                for example_word in example_words:
                    if example_word.lower() != front.lower() and len(example_word) > 3:
                        suggestions.append(example_word)

        # Remove duplicatas e limita a 5 sugestões
        unique_suggestions = list(set(suggestions))[:5]

        return unique_suggestions

    async def _get_all_cards(self, owner_id: str) -> List[Card]:
        """
        Busca todos os cards do owner especificado.

        Returns:
            Lista de todos os cards do owner
        """
        # ICardRepository não tem um "find_all" genérico (só buscas
        # filtradas por deck/palavra/contexto/due) — mantido como no-op,
        # como já era antes desta sprint; nada no domínio chama este caminho
        # sem deck_id hoje.
        return []

    def validate_card_uniqueness(
        self, card: Card, existing_cards: List[Card]
    ) -> Tuple[bool, List[str]]:
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
            if card.front.normalized == existing_card.front.normalized:
                problems.append(
                    f"Frente '{card.front.value}' já existe no card {existing_card.id}"
                )
                continue

            # Verifica similaridade alta
            similarity = self._calculate_similarity(card, existing_card)
            if similarity > 0.9:
                problems.append(
                    f"Card muito similar (similaridade: {similarity:.2f}) ao card {existing_card.id}"
                )

            # Verifica traduções muito similares
            if self.are_backs_similar(card.back.value, existing_card.back.value):
                problems.append(f"Verso muito similar ao card {existing_card.id}")

        is_unique = len(problems) == 0

        return is_unique, problems
