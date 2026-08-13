import { useEffect, useRef, useState } from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip } from "chart.js";
import jsPDF from "jspdf";

import { fetchReviews } from "../api/reviews";
import { fetchDeck } from "../api/decks";
import { useApiResource } from "../api/hooks";
import { computeGoalProgress, getDailyGoal } from "../lib/goal";
import { computeRatingDistribution, mostRecentReview } from "../lib/stats";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import { colors, spacing } from "../tokens/tokens";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

function useLastStudiedDeck(mostRecent) {
  const [deck, setDeck] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // deck_id vem denormalizado direto no CardReview (ver
    // apps/decks/domain/entities/card_review.py) — evita um GET
    // /cards/{id}/ só pra descobrir o deck. Antes disso, "último deck
    // estudado" era uma cadeia de 2 requests, o suficiente pra estourar o
    // throttle de 3 req/s sob o double-effect do StrictMode em dev.
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

  const allReviews = reviews ? (reviews.results ?? reviews) : [];
  const goalProgress = computeGoalProgress(allReviews, getDailyGoal());
  const distribution = computeRatingDistribution(allReviews);

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

  function handleExportPdf() {
    const chart = chartRef.current;
    if (!chart) return;

    const imageData = chart.toBase64Image();
    const pdf = new jsPDF({ orientation: "landscape" });
    pdf.text("Estatísticas de estudo", 14, 15);
    pdf.addImage(imageData, "PNG", 14, 25, 260, 120);
    pdf.save("estatisticas-anki-generator.pdf");
  }

  return (
    <div>
      <h1>Home</h1>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: spacing.md }}>
        <Card title="Último deck estudado">
          {reviewsLoading && <p>Carregando…</p>}
          {!reviewsLoading && !recentReview && <p>Você ainda não revisou nenhum card.</p>}
          {!reviewsLoading && recentReview && lastDeckLoading && <p>Carregando deck…</p>}
          {!reviewsLoading && recentReview && !lastDeckLoading && lastDeckError && <p>Não foi possível carregar o deck.</p>}
          {!reviewsLoading && recentReview && !lastDeckLoading && !lastDeckError && lastDeck && (
            <>
              <p style={{ fontWeight: 600, margin: 0 }}>{lastDeck.title}</p>
              {lastDeck.description && <p style={{ marginTop: spacing.xs }}>{lastDeck.description}</p>}
            </>
          )}
        </Card>

        <Card title="Meta de estudo">
          <p>
            {goalProgress.reviewedToday} / {goalProgress.goal} cards hoje ({goalProgress.percentage}%)
          </p>
        </Card>
      </div>

      <Card title="Estatísticas">
        <Bar ref={chartRef} data={chartData} options={{ responsive: true }} />
        <div style={{ marginTop: spacing.sm }}>
          <Button onClick={handleExportPdf}>Exportar PDF</Button>
        </div>
      </Card>
    </div>
  );
}
