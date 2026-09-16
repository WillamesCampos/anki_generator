import { Bar } from "react-chartjs-2";
import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from "chart.js";

import { colors, radius, typography } from "../../tokens/tokens";
import "./RatingDistributionChart.css";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

const RATING_ITEMS = [
  { key: "again", label: "Errou" },
  { key: "hard", label: "Difícil" },
  { key: "good", label: "Bom" },
  { key: "easy", label: "Fácil" },
];

export default function RatingDistributionChart({
  distribution = {},
  ariaLabel,
  summaryId,
  datasetLabel,
  chartRef,
}) {
  const labels = RATING_ITEMS.map(({ label }) => label);
  const values = RATING_ITEMS.map(({ key }) => distribution[key] ?? 0);
  const prefersReducedMotion = Boolean(
    typeof window !== "undefined"
      && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,
  );
  const data = {
    labels,
    datasets: [
      {
        label: datasetLabel,
        data: values,
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
  const options = {
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

  return (
    <>
      <div className="rating-chart__canvas">
        <Bar
          ref={chartRef}
          aria-label={ariaLabel}
          aria-describedby={summaryId}
          data={data}
          options={options}
        />
      </div>
      <ul
        id={summaryId}
        className="rating-chart__summary"
        aria-label="Resumo das classificações"
      >
        {RATING_ITEMS.map(({ key, label }, index) => (
          <li key={key}>
            <span>{label}</span>
            <strong>{values[index]}</strong>
          </li>
        ))}
      </ul>
    </>
  );
}
