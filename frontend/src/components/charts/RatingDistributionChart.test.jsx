import { render, screen } from "@testing-library/react";
import { createRef, forwardRef } from "react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, expect, test, vi } from "vitest";

import { colors, radius } from "../../tokens/tokens";
import RatingDistributionChart from "./RatingDistributionChart";

const chartStyles = readFileSync(
  resolve("src/components/charts/RatingDistributionChart.css"),
  "utf8",
);

vi.mock("react-chartjs-2", () => ({
  Bar: forwardRef(function Bar({ data, options, ...chartProps }, ref) {
    return (
      <div
        {...chartProps}
        ref={ref}
        role="img"
        data-values={data.datasets[0].data.join(",")}
        data-border-color={data.datasets[0].borderColor}
        data-hover-background={data.datasets[0].hoverBackgroundColor}
        data-border-radius={data.datasets[0].borderRadius}
        data-x-grid={String(options.scales.x.grid.display)}
        data-y-begin-at-zero={String(options.scales.y.beginAtZero)}
        data-tooltip-background={options.plugins.tooltip.backgroundColor}
        data-animation={options.animation === false ? "disabled" : "default"}
      />
    );
  }),
}));

afterEach(() => {
  vi.unstubAllGlobals();
});

test("normaliza a distribuição e expõe um resumo acessível", () => {
  render(
    <RatingDistributionChart
      distribution={{ again: 2, good: 5 }}
      ariaLabel="Distribuição de teste"
      summaryId="rating-summary-test"
      datasetLabel="Revisões de teste"
    />,
  );

  const chart = screen.getByRole("img", { name: "Distribuição de teste" });
  expect(chart).toHaveAttribute("data-values", "2,0,5,0");
  expect(chart).toHaveAttribute("aria-describedby", "rating-summary-test");
  expect(chart).toHaveAttribute("data-border-color", colors.textPrimary);
  expect(chart).toHaveAttribute("data-hover-background", colors.bgDark);
  expect(chart).toHaveAttribute("data-border-radius", String(Number.parseFloat(radius.card)));
  expect(chart).toHaveAttribute("data-x-grid", "false");
  expect(chart).toHaveAttribute("data-y-begin-at-zero", "true");
  expect(chart).toHaveAttribute("data-tooltip-background", colors.bgDark);

  const summary = screen.getByRole("list", { name: "Resumo das classificações" });
  expect(summary).toHaveAttribute("id", "rating-summary-test");
  expect(summary).toHaveTextContent("Errou2");
  expect(summary).toHaveTextContent("Difícil0");
  expect(summary).toHaveTextContent("Bom5");
  expect(summary).toHaveTextContent("Fácil0");
});

test("desativa animação quando o usuário prefere movimento reduzido", () => {
  vi.stubGlobal("matchMedia", vi.fn().mockReturnValue({ matches: true }));

  render(
    <RatingDistributionChart
      distribution={{}}
      ariaLabel="Distribuição reduzida"
      summaryId="rating-summary-reduced"
      datasetLabel="Revisões reduzidas"
    />,
  );

  expect(screen.getByRole("img", { name: "Distribuição reduzida" })).toHaveAttribute(
    "data-animation",
    "disabled",
  );
});

test("encaminha a referência opcional para o gráfico", () => {
  const chartRef = createRef();

  render(
    <RatingDistributionChart
      distribution={{}}
      ariaLabel="Distribuição exportável"
      summaryId="rating-summary-export"
      datasetLabel="Revisões exportáveis"
      chartRef={chartRef}
    />,
  );

  expect(chartRef.current).toBe(screen.getByRole("img", { name: "Distribuição exportável" }));
});

test("define o layout responsivo compartilhado", () => {
  expect(chartStyles).toContain(".rating-chart__canvas");
  expect(chartStyles).toContain("min-height: 320px;");
  expect(chartStyles).toContain(".rating-chart__summary");
  expect(chartStyles).toContain("grid-template-columns: repeat(4, minmax(0, 1fr));");
  expect(chartStyles).toContain("@media (max-width: 640px)");
  expect(chartStyles).toContain("grid-template-columns: repeat(2, minmax(0, 1fr));");
});
