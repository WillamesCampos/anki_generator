"""
Serviço de Qualidade de Cards

Este serviço de domínio é responsável por avaliar a qualidade dos cards gerados,
aplicando regras de negócio para garantir que os cards atendam aos padrões
de qualidade esperados.
"""

from typing import List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

from ..entities.card import Card


class QualityLevel(Enum):
    """
    Níveis de qualidade para um card.
    """
    EXCELLENT = "excellent"    # Qualidade excelente
    GOOD = "good"             # Qualidade boa
    FAIR = "fair"             # Qualidade razoável
    POOR = "poor"             # Qualidade ruim
    INVALID = "invalid"       # Card inválido


@dataclass
class QualityReport:
    """
    Relatório de qualidade de um card.
    """
    card: Card
    overall_score: float
    quality_level: QualityLevel
    issues: List[str]
    suggestions: List[str]
    metrics: Dict[str, float]


class CardQualityService:
    """
    Serviço para avaliação da qualidade de cards.
    
    Este serviço implementa diferentes critérios de qualidade:
    - Comprimento e complexidade da palavra
    - Qualidade da tradução
    - Adequação do exemplo
    - Diversidade do vocabulário
    - Clareza e utilidade
    """
    
    # Configurações de qualidade
    MIN_WORD_LENGTH = 3
    MAX_WORD_LENGTH = 50
    MIN_EXAMPLE_LENGTH = 10
    MAX_EXAMPLE_LENGTH = 200
    MIN_TRANSLATION_LENGTH = 2
    MAX_TRANSLATION_LENGTH = 100
    
    # Pesos para cálculo do score
    WORD_WEIGHT = 0.2
    TRANSLATION_WEIGHT = 0.3
    EXAMPLE_WEIGHT = 0.4
    DIVERSITY_WEIGHT = 0.1
    
    def evaluate_card(self, card: Card, context_cards: List[Card] = None) -> QualityReport:
        """
        Avalia a qualidade de um card.
        
        Args:
            card: Card para avaliar
            context_cards: Cards do contexto (para análise de diversidade)
            
        Returns:
            Relatório de qualidade
        """
        issues = []
        suggestions = []
        metrics = {}
        
        # Avalia a palavra
        word_score, word_issues, word_suggestions = self._evaluate_word(card.word.value)
        issues.extend(word_issues)
        suggestions.extend(word_suggestions)
        metrics['word_score'] = word_score
        
        # Avalia a tradução
        translation_score, translation_issues, translation_suggestions = self._evaluate_translation(card.translation.value)
        issues.extend(translation_issues)
        suggestions.extend(translation_suggestions)
        metrics['translation_score'] = translation_score
        
        # Avalia o exemplo
        example_score, example_issues, example_suggestions = self._evaluate_example(card.example.original, card.example.translated)
        issues.extend(example_issues)
        suggestions.extend(example_suggestions)
        metrics['example_score'] = example_score
        
        # Avalia diversidade (se há cards de contexto)
        diversity_score = 1.0
        if context_cards:
            diversity_score = self._evaluate_diversity(card, context_cards)
        metrics['diversity_score'] = diversity_score
        
        # Calcula score geral
        overall_score = (
            word_score * self.WORD_WEIGHT +
            translation_score * self.TRANSLATION_WEIGHT +
            example_score * self.EXAMPLE_WEIGHT +
            diversity_score * self.DIVERSITY_WEIGHT
        )
        
        # Determina nível de qualidade
        quality_level = self._determine_quality_level(overall_score, issues)
        
        return QualityReport(
            card=card,
            overall_score=overall_score,
            quality_level=quality_level,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics
        )
    
    def _evaluate_word(self, word: str) -> Tuple[float, List[str], List[str]]:
        """
        Avalia a qualidade da palavra.
        
        Args:
            word: Palavra para avaliar
            
        Returns:
            Tupla (score, issues, suggestions)
        """
        issues = []
        suggestions = []
        score = 1.0
        
        word_length = len(word)
        
        # Verifica comprimento
        if word_length < self.MIN_WORD_LENGTH:
            issues.append(f"Palavra muito curta ({word_length} caracteres)")
            score -= 0.3
        elif word_length > self.MAX_WORD_LENGTH:
            issues.append(f"Palavra muito longa ({word_length} caracteres)")
            score -= 0.2
        
        # Verifica se contém apenas letras e espaços
        if not word.replace(' ', '').isalpha():
            issues.append("Palavra contém caracteres inválidos")
            score -= 0.4
        
        # Verifica se é muito comum (palavras muito básicas)
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        if word.lower() in common_words:
            issues.append("Palavra muito comum, considere algo mais específico")
            suggestions.append("Use palavras mais específicas e úteis para aprendizado")
            score -= 0.2
        
        # Verifica se é uma palavra única (não frase muito longa)
        word_count = len(word.split())
        if word_count > 5:
            issues.append("Frase muito longa, considere usar uma palavra ou frase mais curta")
            suggestions.append("Mantenha foco em uma palavra ou frase curta")
            score -= 0.3
        
        return max(0.0, min(1.0, score)), issues, suggestions
    
    def _evaluate_translation(self, translation: str) -> Tuple[float, List[str], List[str]]:
        """
        Avalia a qualidade da tradução.
        
        Args:
            translation: Tradução para avaliar
            
        Returns:
            Tupla (score, issues, suggestions)
        """
        issues = []
        suggestions = []
        score = 1.0
        
        translation_length = len(translation)
        
        # Verifica comprimento
        if translation_length < self.MIN_TRANSLATION_LENGTH:
            issues.append(f"Tradução muito curta ({translation_length} caracteres)")
            score -= 0.4
        elif translation_length > self.MAX_TRANSLATION_LENGTH:
            issues.append(f"Tradução muito longa ({translation_length} caracteres)")
            score -= 0.2
        
        # Verifica se contém apenas caracteres válidos
        if not translation.replace(' ', '').replace(',', '').replace(';', '').replace('(', '').replace(')', '').isalpha():
            issues.append("Tradução contém caracteres inválidos")
            score -= 0.3
        
        # Verifica se tem múltiplas traduções (isso é bom)
        if ',' in translation or ';' in translation:
            score += 0.1
            suggestions.append("Boa! Múltiplas traduções aumentam o valor do card")
        
        # Verifica se é muito genérica
        generic_translations = {'coisa', 'algo', 'item', 'objeto', 'elemento'}
        if any(gen in translation.lower() for gen in generic_translations):
            issues.append("Tradução muito genérica")
            suggestions.append("Use traduções mais específicas e precisas")
            score -= 0.2
        
        return max(0.0, min(1.0, score)), issues, suggestions
    
    def _evaluate_example(self, original: str, translated: str) -> Tuple[float, List[str], List[str]]:
        """
        Avalia a qualidade do exemplo.
        
        Args:
            original: Frase original em inglês
            translated: Tradução da frase
            
        Returns:
            Tupla (score, issues, suggestions)
        """
        issues = []
        suggestions = []
        score = 1.0
        
        original_length = len(original)
        translated_length = len(translated)
        
        # Verifica comprimento da frase original
        if original_length < self.MIN_EXAMPLE_LENGTH:
            issues.append(f"Exemplo muito curto ({original_length} caracteres)")
            score -= 0.4
        elif original_length > self.MAX_EXAMPLE_LENGTH:
            issues.append(f"Exemplo muito longo ({original_length} caracteres)")
            score -= 0.2
        
        # Verifica comprimento da tradução
        if translated_length < self.MIN_EXAMPLE_LENGTH:
            issues.append(f"Tradução do exemplo muito curta ({translated_length} caracteres)")
            score -= 0.3
        
        # Verifica se o exemplo é muito genérico
        generic_examples = [
            "this is a", "that is a", "it is a", "here is a", "there is a"
        ]
        if any(gen in original.lower() for gen in generic_examples):
            issues.append("Exemplo muito genérico")
            suggestions.append("Use exemplos mais específicos e contextualizados")
            score -= 0.3
        
        # Verifica se o exemplo contém a palavra
        words_in_example = original.lower().split()
        if len(words_in_example) > 0:
            # Verifica se pelo menos uma palavra do exemplo é relevante
            # (isso seria melhorado com análise mais sofisticada)
            score += 0.1
        
        return max(0.0, min(1.0, score)), issues, suggestions
    
    def _evaluate_diversity(self, card: Card, context_cards: List[Card]) -> float:
        """
        Avalia a diversidade do card em relação aos cards de contexto.
        
        Args:
            card: Card para avaliar
            context_cards: Cards do contexto
            
        Returns:
            Score de diversidade (0.0 a 1.0)
        """
        if not context_cards:
            return 1.0
        
        # Verifica similaridade com outros cards
        similar_count = 0
        total_cards = len(context_cards)
        
        for context_card in context_cards:
            # Verifica se as palavras são muito similares
            if card.word.normalized == context_card.word.normalized:
                similar_count += 1
            # Verifica se as traduções são muito similares
            elif card.translation.normalized == context_card.translation.normalized:
                similar_count += 1
        
        # Calcula score de diversidade
        diversity_ratio = 1.0 - (similar_count / total_cards)
        
        return max(0.0, min(1.0, diversity_ratio))
    
    def _determine_quality_level(self, score: float, issues: List[str]) -> QualityLevel:
        """
        Determina o nível de qualidade baseado no score e issues.
        
        Args:
            score: Score geral de qualidade
            issues: Lista de problemas encontrados
            
        Returns:
            Nível de qualidade
        """
        if score >= 0.9 and len(issues) == 0:
            return QualityLevel.EXCELLENT
        elif score >= 0.8 and len(issues) <= 1:
            return QualityLevel.GOOD
        elif score >= 0.6 and len(issues) <= 3:
            return QualityLevel.FAIR
        elif score >= 0.4:
            return QualityLevel.POOR
        else:
            return QualityLevel.INVALID
    
    def batch_evaluate(self, cards: List[Card]) -> List[QualityReport]:
        """
        Avalia múltiplos cards em lote.
        
        Args:
            cards: Lista de cards para avaliar
            
        Returns:
            Lista de relatórios de qualidade
        """
        reports = []
        
        for i, card in enumerate(cards):
            # Usa os outros cards como contexto
            context_cards = cards[:i] + cards[i+1:]
            report = self.evaluate_card(card, context_cards)
            reports.append(report)
        
        return reports
    
    def get_quality_statistics(self, reports: List[QualityReport]) -> Dict[str, any]:
        """
        Gera estatísticas de qualidade para uma lista de relatórios.
        
        Args:
            reports: Lista de relatórios de qualidade
            
        Returns:
            Dicionário com estatísticas
        """
        if not reports:
            return {}
        
        total_cards = len(reports)
        scores = [report.overall_score for report in reports]
        
        quality_levels = {}
        for level in QualityLevel:
            quality_levels[level.value] = len([r for r in reports if r.quality_level == level])
        
        return {
            'total_cards': total_cards,
            'average_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'quality_distribution': quality_levels,
            'cards_with_issues': len([r for r in reports if r.issues]),
            'average_issues_per_card': sum(len(r.issues) for r in reports) / total_cards
        }
