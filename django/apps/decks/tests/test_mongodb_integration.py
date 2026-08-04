"""
Teste de Integração MongoDB

Testa a integração completa com MongoDB (conexão, índices, CRUD nos
repositórios). Portado de `test_mongodb_integration.py` (raiz do projeto,
pré-Sprint-0) para `apps/decks/tests/`, agora importável a partir da raiz do
projeto sem depender de `legacy/` no path (ver tasks.md, tarefa 3.4).

Para executar (requer MongoDB rodando — `docker compose up -d mongo`):
    poetry run python -m apps.decks.tests.test_mongodb_integration
"""

import asyncio

from apps.decks.domain.entities.card import Card
from apps.decks.domain.entities.deck import Deck
from apps.decks.domain.entities.generation_session import GenerationSession, GenerationStatus
from apps.decks.domain.value_objects.example import Example
from apps.decks.domain.value_objects.translation import Translation
from apps.decks.domain.value_objects.word import Word
from apps.decks.infrastructure.mongodb_connection import ensure_mongodb_connection
from apps.decks.infrastructure.repositories.card_repository import CardRepository
from apps.decks.infrastructure.repositories.deck_repository import DeckRepository
from apps.decks.infrastructure.repositories.generation_session_repository import (
    GenerationSessionRepository,
)


async def test_mongodb_connection():
    """Testa a conexão com MongoDB."""
    print("🔌 Testando conexão com MongoDB...")

    try:
        mongodb_manager = await ensure_mongodb_connection()
        health = await mongodb_manager.health_check()

        print(f"✅ MongoDB conectado: {health['status']}")
        print(f"   Versão do servidor: {health.get('server_version', 'N/A')}")
        print(f"   Banco: {health.get('database_name', 'N/A')}")

        return mongodb_manager

    except Exception as e:
        print(f"❌ Erro ao conectar MongoDB: {e}")
        raise


async def test_create_indexes(mongodb_manager):
    """Testa a criação de índices."""
    print("\n📊 Criando índices...")

    try:
        await mongodb_manager.create_indexes()
        print("✅ Índices criados com sucesso")

    except Exception as e:
        print(f"❌ Erro ao criar índices: {e}")
        raise


async def test_deck_repository():
    """Testa operações do DeckRepository."""
    print("\n📚 Testando DeckRepository...")

    try:
        deck_repo = DeckRepository()

        deck = Deck(
            title="Deck de Teste",
            description="Deck criado para testes de integração",
            max_cards_per_generation=5,
        )

        saved_deck = await deck_repo.save(deck)
        print(f"✅ Deck salvo: {saved_deck.id}")

        found_deck = await deck_repo.find_by_id(saved_deck.id)
        if found_deck:
            print(f"✅ Deck encontrado: {found_deck.title}")
        else:
            print("❌ Deck não encontrado")

        decks_by_title = await deck_repo.find_by_title("Teste")
        print(f"✅ Decks encontrados por título: {len(decks_by_title)}")

        deck_count = await deck_repo.count()
        print(f"✅ Total de decks: {deck_count}")

        return saved_deck

    except Exception as e:
        print(f"❌ Erro no DeckRepository: {e}")
        raise


async def test_card_repository(deck):
    """Testa operações do CardRepository."""
    print("\n🃏 Testando CardRepository...")

    try:
        card_repo = CardRepository()

        word = Word("algorithm")
        translation = Translation("algoritmo")
        example = Example(
            original="I implemented a sorting algorithm in Python.",
            translated="Eu implementei um algoritmo de ordenação em Python.",
        )

        card = Card(
            word=word,
            translation=translation,
            example=example,
            context="programming",
            deck_id=deck.id,
        )

        saved_card = await card_repo.save(card)
        print(f"✅ Card salvo: {saved_card.id}")

        found_card = await card_repo.find_by_id(saved_card.id)
        if found_card:
            print(f"✅ Card encontrado: {found_card.word.value}")
        else:
            print("❌ Card não encontrado")

        cards_by_word = await card_repo.find_by_word("algorithm")
        print(f"✅ Cards encontrados por palavra: {len(cards_by_word)}")

        cards_by_deck = await card_repo.find_by_deck_id(deck.id)
        print(f"✅ Cards encontrados no deck: {len(cards_by_deck)}")

        word_exists = await card_repo.exists_by_word("algorithm", deck.id)
        print(f"✅ Palavra existe no deck: {word_exists}")

        card_count = await card_repo.count()
        print(f"✅ Total de cards: {card_count}")

        return saved_card

    except Exception as e:
        print(f"❌ Erro no CardRepository: {e}")
        raise


async def test_generation_session_repository(deck):
    """Testa operações do GenerationSessionRepository."""
    print("\n🔄 Testando GenerationSessionRepository...")

    try:
        session_repo = GenerationSessionRepository()

        session = GenerationSession(
            context="programming concepts",
            deck_id=deck.id,
            max_cards=3,
        )

        saved_session = await session_repo.save(session)
        print(f"✅ Sessão salva: {saved_session.id}")

        found_session = await session_repo.find_by_id(saved_session.id)
        if found_session:
            print(f"✅ Sessão encontrada: {found_session.status.value}")
        else:
            print("❌ Sessão não encontrada")

        sessions_by_deck = await session_repo.find_by_deck_id(deck.id)
        print(f"✅ Sessões encontradas no deck: {len(sessions_by_deck)}")

        active_sessions = await session_repo.find_active_sessions()
        print(f"✅ Sessões ativas: {len(active_sessions)}")

        pending_sessions = await session_repo.find_by_status(GenerationStatus.PENDING)
        print(f"✅ Sessões pendentes: {len(pending_sessions)}")

        session_count = await session_repo.count()
        print(f"✅ Total de sessões: {session_count}")

        return saved_session

    except Exception as e:
        print(f"❌ Erro no GenerationSessionRepository: {e}")
        raise


async def test_cleanup(mongodb_manager):
    """Limpa os dados de teste."""
    print("\n🧹 Limpando dados de teste...")

    try:
        await mongodb_manager.drop_collection("decks")
        await mongodb_manager.drop_collection("cards")
        await mongodb_manager.drop_collection("generation_sessions")

        print("✅ Dados de teste removidos")

    except Exception as e:
        print(f"⚠️ Aviso ao limpar dados: {e}")


async def main():
    """Função principal do teste."""
    print("🚀 Iniciando teste de integração MongoDB...\n")

    mongodb_manager = None
    try:
        mongodb_manager = await test_mongodb_connection()
        await test_create_indexes(mongodb_manager)

        deck = await test_deck_repository()
        await test_card_repository(deck)
        await test_generation_session_repository(deck)

        await test_cleanup(mongodb_manager)

        print("\n🎉 Todos os testes passaram com sucesso!")
        print("✅ Integração MongoDB funcionando perfeitamente!")

    except Exception as e:
        print(f"\n❌ Teste falhou: {e}")
        return False

    finally:
        if mongodb_manager is not None:
            await mongodb_manager.disconnect()
            print("\n🔌 Desconectado do MongoDB")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())

    if success:
        print("\n✅ Teste concluído com sucesso!")
        raise SystemExit(0)
    else:
        print("\n❌ Teste falhou!")
        raise SystemExit(1)
