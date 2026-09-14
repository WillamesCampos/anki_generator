import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip } from "chart.js";

import { fetchReviews } from "../api/reviews";
import { fetchDeck, fetchDeckStatistics } from "../api/decks";
import { useApiResource } from "../api/hooks";
import { computeGoalProgress, getDailyGoal } from "../lib/goal";
import { exportChartToPdf } from "../lib/exportPdf";
import { mostRecentReview } from "../lib/stats";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import { colors, radius, typography } from "../tokens/tokens";
import "./HomePage.css";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

const RATING_KEYS = ["again", "hard", "good", "easy"];
const RATING_LABELS = ["Errou", "Difícil", "Bom", "Fácil"];

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
  const ratingDistribution = deckStatistics?.rating_distribution ?? {};
  const distribution = {
    labels: RATING_LABELS,
    values: RATING_KEYS.map((rating) => ratingDistribution[rating] ?? 0),
  };
  const chartLoading = reviewsLoading || (Boolean(recentReview) && statisticsLoading);
  const hasValidLastDeck = Boolean(
    !reviewsLoading && recentReview && !lastDeckLoading && !lastDeckError && lastDeck,
  );
  const prefersReducedMotion = Boolean(
    typeof window !== "undefined"
    && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,
  );

  const chartData = {
    labels: distribution.labels,
    datasets: [
      {
        label: "Revisões por resultado",
        data: distribution.values,
        backgroundColor: colors.accent,
        hoverBackgroundColor: colors.bgDark,
        borderColor: colors.textPrimary,
        hoverBorderColor: colors.accent,
        borderWidth: 2,
        borderSkipped: false,
        borderRadius: Number.parseFloat(radius.card),
        maxBarThickness: 64,
      },
    ],
  };

  const chartOptions = {
    maintainAspectRatio: false,
    responsive: true,
    animation: prefersReducedMotion ? false : undefined,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: colors.bgDark,
        titleColor: colors.textOnDark,
        bodyColor: colors.textOnDark,
        borderColor: colors.accent,
        borderWidth: 1,
        displayColors: false,
        padding: 12,
        titleFont: { family: typography.fontFamily, weight: "600" },
        bodyFont: { family: typography.fontFamily },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: colors.textPrimary,
          font: { family: typography.fontFamily, weight: "600" },
          maxRotation: 0,
          minRotation: 0,
        },
      },
      y: {
        beginAtZero: true,
        grid: { color: colors.border },
        ticks: {
          color: colors.textSecondary,
          font: { family: typography.fontFamily },
          precision: 0,
        },
      },
    },
  };

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

        <Card title="Meta de estudo">
          <p>
            {goalProgress.reviewedToday} / {goalProgress.goal} cards hoje ({goalProgress.percentage}%)
          </p>
        </Card>
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
              <div className="home-page__chart">
                <Bar
                  ref={chartRef}
                  aria-label="Distribuição das classificações da Home"
                  aria-describedby="home-rating-summary"
                  data={chartData}
                  options={chartOptions}
                />
              </div>
              <ul
                id="home-rating-summary"
                className="home-page__statistics-values"
                aria-label="Resumo das classificações"
              >
                {distribution.labels.map((label, index) => (
                  <li key={RATING_KEYS[index]}>
                    <span>{label}</span>
                    <strong>{distribution.values[index]}</strong>
                  </li>
                ))}
              </ul>
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
