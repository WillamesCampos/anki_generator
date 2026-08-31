import { useEffect, useRef, useState } from "react";
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
import { colors } from "../tokens/tokens";
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

  const chartData = {
    labels: distribution.labels,
    datasets: [
      {
        label: "Revisões por resultado",
        data: distribution.values,
        backgroundColor: colors.accent,
        borderRadius: 8,
      },
    ],
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
            </>
          )}
        </Card>

        <Card title="Meta de estudo">
          <p>
            {goalProgress.reviewedToday} / {goalProgress.goal} cards hoje ({goalProgress.percentage}%)
          </p>
        </Card>
      </div>

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
                  data={chartData}
                  options={{ maintainAspectRatio: false, responsive: true }}
                />
              </div>
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
