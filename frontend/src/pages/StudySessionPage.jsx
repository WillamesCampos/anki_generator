import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchDueCards } from "../api/cards";
import { fetchDeck } from "../api/decks";
import { createReview } from "../api/reviews";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import "./StudySessionPage.css";

const RATINGS = [
  { value: "again", label: "Errei" },
  { value: "hard", label: "Difícil" },
  { value: "good", label: "Bom" },
  { value: "easy", label: "Fácil" },
];

function requestError(error, fallback) {
  return error?.status === 403 ? error.message : fallback;
}

export default function StudySessionPage() {
  const { deckId } = useParams();
  const [deck, setDeck] = useState(null);
  const [cards, setCards] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [reviewedCount, setReviewedCount] = useState(0);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Busca os cards devidos do deck uma única vez, ao montar — sem sessão
  // persistida (D2 em design.md): reabrir a tela sempre recomeça do zero,
  // buscando os cards devidos naquele momento.
  useEffect(() => {
    let cancelled = false;

    Promise.all([fetchDeck(deckId), fetchDueCards(deckId)])
      .then(([deckResponse, cardsResponse]) => {
        if (cancelled) return;
        setDeck(deckResponse);
        setCards(cardsResponse?.results ?? cardsResponse ?? []);
      })
      .catch((requestErr) => {
        if (!cancelled) {
          setError(requestError(requestErr, "Não foi possível carregar a sessão de estudo."));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [deckId]);

  async function handleRate(rating) {
    const currentCard = cards[currentIndex];
    setSubmitting(true);
    setError("");

    try {
      await createReview(currentCard.id, rating);
      setReviewedCount((count) => count + 1);

      if (currentIndex + 1 >= cards.length) {
        setSessionComplete(true);
      } else {
        setCurrentIndex((index) => index + 1);
        setRevealed(false);
      }
    } catch (requestErr) {
      setError(requestError(requestErr, "Não foi possível registrar a avaliação."));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p>Carregando sessão de estudo…</p>;
  if (error && cards.length === 0) return <p role="alert">{error}</p>;
  if (!deck) return null;

  const total = cards.length;

  return (
    <section className="deck-page study-session">
      <header className="deck-page__header">
        <div>
          <p className="deck-page__eyebrow">Sessão de estudo</p>
          <h1 className="deck-page__title">{deck.title}</h1>
        </div>
        <Button as={Link} variant="secondary" to={`/decks/${deckId}`}>
          Voltar ao deck
        </Button>
      </header>

      {error && <p className="study-session__error" role="alert">{error}</p>}

      {total === 0 && (
        <Card title="Nada por aqui agora">
          <p className="study-session__empty-text">
            Nenhum card devido agora neste deck.
          </p>
        </Card>
      )}

      {total > 0 && sessionComplete && (
        <Card title="Sessão concluída">
          <p className="study-session__summary">
            Você revisou {reviewedCount} {reviewedCount === 1 ? "card" : "cards"} neste deck.
          </p>
          <Button as={Link} to={`/decks/${deckId}`}>Voltar ao deck</Button>
        </Card>
      )}

      {total > 0 && !sessionComplete && (
        <>
          <p className="study-session__progress" aria-live="polite">
            Card {currentIndex + 1} de {total}
          </p>

          <Card title={cards[currentIndex].front}>
            {!revealed && (
              <Button onClick={() => setRevealed(true)}>Mostrar resposta</Button>
            )}

            {revealed && (
              <>
                <p className="study-session__back">{cards[currentIndex].back}</p>
                <p className="study-session__description">
                  {cards[currentIndex].front_description}
                </p>
                <p className="study-session__description">
                  {cards[currentIndex].back_description}
                </p>

                <div className="study-session__ratings">
                  {RATINGS.map(({ value, label }) => (
                    <Button
                      key={value}
                      variant="secondary"
                      disabled={submitting}
                      onClick={() => handleRate(value)}
                    >
                      {label}
                    </Button>
                  ))}
                </div>
              </>
            )}
          </Card>
        </>
      )}
    </section>
  );
}
