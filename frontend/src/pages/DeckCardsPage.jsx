import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { createCard, deleteCard, fetchCardsByDeck, updateCard } from "../api/cards";
import { fetchDeck } from "../api/decks";
import CardForm from "../components/cards/CardForm";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import "./DeckManagement.css";
import "./DeckDetailPage.css";

function collectionItems(response) {
  return response?.results ?? response ?? [];
}

const PAGE_SIZE = 10;

function requestError(error, fallback) {
  return error?.status === 403 ? error.message : fallback;
}

export default function DeckCardsPage() {
  const { deckId } = useParams();
  const [deck, setDeck] = useState(null);
  const [cards, setCards] = useState([]);
  const [cardCount, setCardCount] = useState(0);
  const [nextPage, setNextPage] = useState(null);
  const [previousPage, setPreviousPage] = useState(null);
  const [page, setPage] = useState(1);
  const [reloadKey, setReloadKey] = useState(0);
  const [deckLoading, setDeckLoading] = useState(true);
  const [cardsLoading, setCardsLoading] = useState(true);
  const [deckError, setDeckError] = useState("");
  const [cardsError, setCardsError] = useState("");
  const [actionError, setActionError] = useState("");
  const [editingCardId, setEditingCardId] = useState(null);
  const [pendingDeletion, setPendingDeletion] = useState(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    fetchDeck(deckId)
      .then((response) => {
        if (!cancelled) setDeck(response);
      })
      .catch((error) => {
        if (!cancelled) setDeckError(requestError(error, "Não foi possível carregar o deck."));
      })
      .finally(() => {
        if (!cancelled) setDeckLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [deckId]);

  useEffect(() => {
    let cancelled = false;

    setCardsLoading(true);
    setCardsError("");

    fetchCardsByDeck(deckId, page)
      .then((response) => {
        if (!cancelled) {
          const items = collectionItems(response);
          setCards(items);
          setCardCount(response?.count ?? items.length);
          setNextPage(response?.next ?? null);
          setPreviousPage(response?.previous ?? null);
        }
      })
      .catch((error) => {
        if (!cancelled) setCardsError(requestError(error, "Não foi possível carregar os cards."));
      })
      .finally(() => {
        if (!cancelled) setCardsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [deckId, page, reloadKey]);

  async function handleCardCreate(payload) {
    await createCard(payload);
    if (page === 1) {
      setReloadKey((current) => current + 1);
    } else {
      setPage(1);
    }
  }

  async function handleCardUpdate(cardId, payload) {
    const updatedCard = await updateCard(cardId, payload);
    setCards((current) => current.map((card) => (card.id === cardId ? updatedCard : card)));
    setEditingCardId(null);
  }

  async function handleConfirmDeletion() {
    setDeleting(true);
    setActionError("");

    try {
      await deleteCard(pendingDeletion.id);
      setPendingDeletion(null);
      if (cards.length === 1 && page > 1) {
        setPage((current) => current - 1);
      } else {
        setReloadKey((current) => current + 1);
      }
    } catch (error) {
      setActionError(requestError(error, "Não foi possível excluir o card."));
      setPendingDeletion(null);
    } finally {
      setDeleting(false);
    }
  }

  if (deckLoading) return <p>Carregando deck…</p>;
  if (deckError) return <p role="alert">{deckError}</p>;
  if (!deck) return null;

  const totalPages = Math.max(1, Math.ceil(cardCount / PAGE_SIZE));

  return (
    <section className="deck-page deck-detail">
      <header className="deck-page__header">
        <div>
          <p className="deck-page__eyebrow">Conteúdo do deck</p>
          <h1 className="deck-page__title">Cards de {deck.title}</h1>
        </div>
        <Button as={Link} variant="secondary" to={`/decks/${deckId}`}>
          Voltar ao deck
        </Button>
      </header>

      {actionError && <p className="deck-detail__error" role="alert">{actionError}</p>}

      <section className="deck-detail__create" aria-labelledby="new-card-title">
        <Card title="Adicionar card">
          <h2 className="deck-detail__form-title" id="new-card-title">Novo conteúdo</h2>
          <CardForm
            deckId={deckId}
            ariaLabel="Adicionar card"
            submitLabel="Adicionar card"
            onSubmit={handleCardCreate}
          />
        </Card>
      </section>

      <section className="deck-detail__cards" aria-labelledby="cards-title">
        <div className="deck-detail__section-heading">
          <div>
            <p className="deck-page__eyebrow">Todos os cards</p>
            <h2 id="cards-title">Lista</h2>
          </div>
          {!cardsLoading && !cardsError && (
            <p>{cardCount} {cardCount === 1 ? "card" : "cards"}</p>
          )}
        </div>

        {cardsLoading && <p>Carregando cards…</p>}
        {!cardsLoading && cardsError && <p role="alert">{cardsError}</p>}
        {!cardsLoading && !cardsError && cards.length === 0 && (
          <Card title="Nenhum card por aqui">
            <p className="deck-detail__empty-text">Este deck ainda não tem cards.</p>
          </Card>
        )}

        {!cardsLoading && !cardsError && cards.length > 0 && (
          <>
            <div className="deck-detail__card-list">
              {cards.map((card) => (
                <Card key={card.id} title={card.front}>
                {editingCardId === card.id ? (
                  <CardForm
                    deckId={deckId}
                    initialCard={card}
                    ariaLabel={`Editar card ${card.front}`}
                    submitLabel="Salvar card"
                    onSubmit={(payload) => handleCardUpdate(card.id, payload)}
                    onCancel={() => setEditingCardId(null)}
                  />
                ) : (
                  <>
                    <p className="deck-detail__back">{card.back}</p>
                    <p className="deck-detail__card-description">{card.front_description}</p>
                    <p className="deck-detail__card-description">{card.back_description}</p>
                    {card.tags?.length > 0 && (
                      <p className="deck-detail__tags">{card.tags.join(" · ")}</p>
                    )}
                    <div className="deck-detail__card-actions">
                      <Button
                        variant="secondary"
                        onClick={() => setEditingCardId(card.id)}
                        aria-label={`Editar card ${card.front}`}
                      >
                        Editar
                      </Button>
                      <Button
                        onClick={() => setPendingDeletion(card)}
                        aria-label={`Excluir card ${card.front}`}
                      >
                        Excluir
                      </Button>
                    </div>
                  </>
                )}
                </Card>
              ))}
            </div>
            <nav className="deck-detail__pagination" aria-label="Paginação dos cards">
              <Button
                variant="secondary"
                onClick={() => setPage((current) => current - 1)}
                disabled={!previousPage || cardsLoading}
              >
                Anterior
              </Button>
              <p aria-live="polite">Página {page} de {totalPages}</p>
              <Button
                variant="secondary"
                onClick={() => setPage((current) => current + 1)}
                disabled={!nextPage || cardsLoading}
              >
                Próxima
              </Button>
            </nav>
          </>
        )}
      </section>

      <ConfirmDialog
        open={Boolean(pendingDeletion)}
        title="Excluir card"
        message={`O card “${pendingDeletion?.front ?? ""}” deixará de aparecer neste deck.`}
        onConfirm={handleConfirmDeletion}
        onCancel={() => setPendingDeletion(null)}
        loading={deleting}
      />
    </section>
  );
}
