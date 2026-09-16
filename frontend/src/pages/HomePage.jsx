import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { fetchReviews } from "../api/reviews";
import { fetchDeck, fetchDeckStatistics } from "../api/decks";
import { useApiResource } from "../api/hooks";
import RatingDistributionChart from "../components/charts/RatingDistributionChart";
import { computeGoalProgress, getDailyGoal } from "../lib/goal";
import { exportChartToPdf } from "../lib/exportPdf";
import { mostRecentReview } from "../lib/stats";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import "./HomePage.css";

function useLastStudiedDeck(mostRecent) {
  const [deck, setDeck] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // deck_id vem denormalizado direto no CardReview (ver
    // apps/decks/domain/entities/card_review.py) — evita um GET
    // /cards/{id}/ só pra descobrir o deck. Antes disso, "último deck
    // estudado" era uma cadeia de 2 requests, o suficiente pra estourar o
    // throttle sob o double-effect do StrictMode em dev.
    if (!mostRecent?.deck_id) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchDeck(mostRecent.deck_id)
      .then((deckData) => {
        if (!cancelled) setDeck(deckData);
      })
      .catch((err) => {
        if (!cancelled) {
          console.error("Falha ao buscar o último deck estudado:", err);
          setError(err);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [mostRecent]);

  return { deck, loading, error };
}

export default function HomePage() {
  const { data: reviews, loading: reviewsLoading } = useApiResource(fetchReviews, []);
  const chartRef = useRef(null);

  const recentReview = reviews ? mostRecentReview(reviews.results ?? reviews) : null;
  const { deck: lastDeck, loading: lastDeckLoading, error: lastDeckError } = useLastStudiedDeck(recentReview);
  const lastDeckId = recentReview?.deck_id;
  const {
    data: deckStatistics,
    loading: statisticsLoading,
    error: statisticsError,
  } = useApiResource(
    () => lastDeckId ? fetchDeckStatistics(lastDeckId) : Promise.resolve(null),
    [lastDeckId],
  );

  const allReviews = reviews ? (reviews.results ?? reviews) : [];
  const goalProgress = computeGoalProgress(allReviews, getDailyGoal());
  const remainingGoal = Math.max(goalProgress.goal - goalProgress.reviewedToday, 0);
  const goalComplete = goalProgress.percentage >= 100;
  const ratingDistribution = deckStatistics?.rating_distribution ?? {};
  const chartLoading = reviewsLoading || (Boolean(recentReview) && statisticsLoading);
  const hasValidLastDeck = Boolean(
    !reviewsLoading && recentReview && !lastDeckLoading && !lastDeckError && lastDeck,
  );

  async function handleExportPdf() {
    await exportChartToPdf(chartRef.current);
  }

  return (
    <section className="home-page">
      <h1 className="home-page__title">Home</h1>

      <div className="home-page__summary-grid">
        <Card title="Último deck estudado">
          {reviewsLoading && <p>Carregando…</p>}
          {!reviewsLoading && !recentReview && <p>Você ainda não revisou nenhum card.</p>}
          {!reviewsLoading && recentReview && lastDeckLoading && <p>Carregando deck…</p>}
          {!reviewsLoading && recentReview && !lastDeckLoading && lastDeckError && (
            <p>
              {lastDeckError.status === 403
                ? lastDeckError.message
                : "Não foi possível carregar o deck."}
            </p>
          )}
          {!reviewsLoading && recentReview && !lastDeckLoading && !lastDeckError && lastDeck && (
            <>
              <p className="home-page__deck-title">{lastDeck.title}</p>
              {lastDeck.description && <p className="home-page__deck-description">{lastDeck.description}</p>}
              <Button
                as={Link}
                variant="primary"
                to={`/decks/${lastDeck.id}/estudar`}
                data-home-action="continue"
              >
                Continuar estudando
              </Button>
            </>
          )}
        </Card>

        <div className="home-page__goal-card">
          <Card title="Meta de estudo">
            <div className="home-page__goal-overview">
              <div>
                <p className="home-page__goal-count">
                  <strong>{goalProgress.reviewedToday}</strong>
                  <span> / {goalProgress.goal}</span>
                </p>
                <p className="home-page__goal-label">cards hoje</p>
              </div>
              <span className="home-page__goal-percent" aria-hidden="true">
                {goalProgress.percentage}%
              </span>
            </div>
            <div
              className="home-page__goal-progress"
              role="progressbar"
              aria-label="Progresso da meta diária"
              aria-valuemin="0"
              aria-valuemax="100"
              aria-valuenow={goalProgress.percentage}
              aria-valuetext={`${goalProgress.reviewedToday} de ${goalProgress.goal} cards revisados hoje`}
            >
              <span
                className="home-page__goal-progress-fill"
                style={{ "--goal-progress": `${goalProgress.percentage}%` }}
              />
            </div>
            <p className="home-page__goal-helper">
              {goalComplete
                ? "Meta concluída hoje!"
                : `${remainingGoal} ${remainingGoal === 1 ? "card" : "cards"} para concluir sua meta`}
            </p>
          </Card>
        </div>
      </div>

      {!reviewsLoading && (
        <div className="home-page__study-cta">
          <p className="home-page__study-cta-copy">
            {hasValidLastDeck
              ? "Não é o deck que deseja estudar agora? Escolha o seu deck!"
              : "Escolha um deck pra começar a estudar!"}
          </p>
          <Button
            as={Link}
            variant="secondary"
            to="/decks"
            data-home-action="decks"
          >
            Ver meus decks
            <svg
              className="home-page__decks-eye-icon"
              viewBox="0 0 24 24"
              aria-hidden="true"
              focusable="false"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </Button>
        </div>
      )}

      <div className="home-page__statistics">
        <Card title="Estatísticas">
          {chartLoading && <p>Carregando estatísticas…</p>}
          {!chartLoading && recentReview && statisticsError && (
            <p role="alert">Não foi possível carregar as estatísticas do último deck.</p>
          )}
          {!chartLoading && (!recentReview || !statisticsError) && (
            <>
              <RatingDistributionChart
                distribution={ratingDistribution}
                ariaLabel="Distribuição das classificações da Home"
                summaryId="home-rating-summary"
                datasetLabel="Revisões por resultado"
                chartRef={chartRef}
              />
              <div className="home-page__actions">
                <Button onClick={handleExportPdf}>Exportar PDF</Button>
              </div>
            </>
          )}
        </Card>
      </div>
    </section>
  );
}
