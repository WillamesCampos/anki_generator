import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from "chart.js";
import { Link, useNavigate, useParams } from "react-router-dom";

import { fetchCardCount } from "../api/cards";
import { deleteDeck, fetchDeck, fetchDeckStatistics, updateDeck } from "../api/decks";
import DeckForm from "../components/decks/DeckForm";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import { colors } from "../tokens/tokens";
import "./DeckManagement.css";
import "./DeckDetailPage.css";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

const RATING_LABELS = ["Errou", "Difícil", "Bom", "Fácil"];
const RATING_KEYS = ["again", "hard", "good", "easy"];
const EMPTY_DISTRIBUTION = { again: 0, hard: 0, good: 0, easy: 0 };

function requestError(error, fallback) {
  return error?.status === 403 ? error.message : fallback;
}

export default function DeckDetailPage() {
  const { deckId } = useParams();
  const navigate = useNavigate();
  const [deck, setDeck] = useState(null);
  const [cardCount, setCardCount] = useState(null);
  const [ratingDistribution, setRatingDistribution] = useState(EMPTY_DISTRIBUTION);
  const [deckLoading, setDeckLoading] = useState(true);
  const [countLoading, setCountLoading] = useState(true);
  const [statisticsLoading, setStatisticsLoading] = useState(true);
  const [deckError, setDeckError] = useState("");
  const [countError, setCountError] = useState("");
  const [statisticsError, setStatisticsError] = useState("");
  const [actionError, setActionError] = useState("");
  const [editingDeck, setEditingDeck] = useState(false);
  const [confirmingDeletion, setConfirmingDeletion] = useState(false);
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

    fetchDeckStatistics(deckId)
      .then((response) => {
        if (!cancelled) {
          setRatingDistribution({
            ...EMPTY_DISTRIBUTION,
            ...response.rating_distribution,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setStatisticsError("Não foi possível carregar as estatísticas do deck.");
        }
      })
      .finally(() => {
        if (!cancelled) setStatisticsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [deckId]);

  useEffect(() => {
    let cancelled = false;

    fetchCardCount(deckId)
      .then((response) => {
        if (!cancelled) setCardCount(response.count);
      })
      .catch((error) => {
        if (!cancelled) {
          setCountError(requestError(error, "Não foi possível carregar a quantidade de cards."));
        }
      })
      .finally(() => {
        if (!cancelled) setCountLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [deckId]);

  async function handleDeckUpdate(payload) {
    const updatedDeck = await updateDeck(deckId, payload);
    setDeck(updatedDeck);
    setEditingDeck(false);
  }

  async function handleConfirmDeletion() {
    setDeleting(true);
    setActionError("");

    try {
      await deleteDeck(deckId);
      navigate("/decks");
    } catch (error) {
      setActionError(requestError(error, "Não foi possível excluir o deck."));
      setConfirmingDeletion(false);
    } finally {
      setDeleting(false);
    }
  }

  if (deckLoading) return <p>Carregando deck…</p>;
  if (deckError) return <p role="alert">{deckError}</p>;
  if (!deck) return null;

  const ratingValues = RATING_KEYS.map((rating) => ratingDistribution[rating]);
  const chartData = {
    labels: RATING_LABELS,
    datasets: [{
      label: "Revisões por classificação",
      data: ratingValues,
      backgroundColor: colors.accent,
      borderRadius: 8,
    }],
  };

  return (
    <section className="deck-page deck-detail">
      <header className="deck-page__header">
        <div>
          <p className="deck-page__eyebrow">Detalhe do deck</p>
          <h1 className="deck-page__title">{deck.title}</h1>
        </div>
        <div className="deck-detail__header-actions">
          <Button as={Link} variant="secondary" to="/decks">Voltar</Button>
          <Button
            variant="secondary"
            onClick={() => setEditingDeck((current) => !current)}
          >
            {editingDeck ? "Cancelar edição" : "Editar deck"}
          </Button>
          <Button onClick={() => setConfirmingDeletion(true)}>Excluir deck</Button>
        </div>
      </header>

      {actionError && <p className="deck-detail__error" role="alert">{actionError}</p>}

      {editingDeck ? (
        <Card title="Editar deck">
          <DeckForm
            initialDeck={deck}
            submitLabel="Salvar alterações"
            onSubmit={handleDeckUpdate}
          />
        </Card>
      ) : (
        <Card title="Sobre este deck">
          <p className="deck-detail__description">{deck.description || "Deck sem descrição."}</p>
          <p className="deck-detail__meta">
            Meta diária: {deck.daily_review_goal ?? "não definida"}
          </p>
        </Card>
      )}

      <section className="deck-detail__cards" aria-labelledby="cards-title">
        <div className="deck-detail__section-heading">
          <div>
            <p className="deck-page__eyebrow">Conteúdo</p>
            <h2 id="cards-title">Cards</h2>
          </div>
          <Button as={Link} to={`/decks/${deckId}/cards`}>Ver todos os cards</Button>
        </div>

        <Card title="Quantidade de cards">
          {countLoading && <p>Carregando quantidade…</p>}
          {!countLoading && countError && <p role="alert">{countError}</p>}
          {!countLoading && !countError && (
            <p className="deck-detail__count">
              {cardCount} {cardCount === 1 ? "card" : "cards"}
            </p>
          )}
        </Card>
      </section>

      <section className="deck-detail__statistics" aria-labelledby="statistics-title">
        <div className="deck-detail__section-heading">
          <div>
            <p className="deck-page__eyebrow">Histórico de estudo</p>
            <h2 id="statistics-title">Estatísticas</h2>
          </div>
        </div>

        <Card title="Classificações do deck">
          {statisticsLoading && <p>Carregando estatísticas…</p>}
          {!statisticsLoading && statisticsError && <p role="alert">{statisticsError}</p>}
          {!statisticsLoading && !statisticsError && (
            <>
              <div className="deck-detail__chart">
                <Bar
                  aria-label="Distribuição das classificações do deck"
                  data={chartData}
                  options={{ maintainAspectRatio: false, responsive: true }}
                />
              </div>
              <ul className="deck-detail__statistics-values">
                {RATING_LABELS.map((label, index) => (
                  <li key={RATING_KEYS[index]}>{label}: {ratingValues[index]}</li>
                ))}
              </ul>
            </>
          )}
        </Card>
      </section>

      <ConfirmDialog
        open={confirmingDeletion}
        title="Excluir deck"
        message={`O deck “${deck.title}” e seus cards deixarão de aparecer na sua lista.`}
        onConfirm={handleConfirmDeletion}
        onCancel={() => setConfirmingDeletion(false)}
        loading={deleting}
      />
    </section>
  );
}
