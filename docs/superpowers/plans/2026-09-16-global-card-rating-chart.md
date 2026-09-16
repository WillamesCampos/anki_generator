# Global Card and Rating Chart Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the approved black-bordered card surface global and render Home and deck-detail rating statistics through one accessible, tokenized chart component.

**Architecture:** Move the shared surface and title treatment into `Card.css`, leaving page CSS responsible only for local layout. Add a presentation-only `RatingDistributionChart` that normalizes the four FSRS ratings, owns Chart.js configuration and shared CSS, and accepts resolved data from both pages without making requests.

**Tech Stack:** React 18, Chart.js 4, react-chartjs-2 5, Vitest 4, Testing Library, CSS custom properties.

## Global Constraints

- Every `ui-card` uses a white background, `2px` black border, and `4px 4px 0` black shadow.
- Every card title uses the shared orange marker, large title token, and weight 700.
- Cards have no global hover, transform, or transition.
- At `max-width: 640px`, all cards use `var(--space-sm)` padding.
- The study-session card also uses the global black shadow; semantic rating-button colors remain unchanged.
- Rating order is always `again`, `hard`, `good`, `easy`, displayed as `Errou`, `Difícil`, `Bom`, `Fácil`.
- Home keeps PDF export; deck detail does not gain export.
- Keep APIs, loading, errors, routes, review behavior, forms, dialogs, and navigation unchanged.
- Use existing tokens only; add no dependency and no hardcoded color outside token files.

---

### Task 1: Promote the approved card surface to the global component

**Files:**
- Create: `frontend/src/components/ui/Card.test.jsx`
- Modify: `frontend/src/components/ui/Card.css`
- Modify: `frontend/src/pages/HomePage.test.jsx`
- Modify: `frontend/src/pages/HomePage.css`
- Modify: `frontend/src/pages/StudySessionPage.css`

**Interfaces:**
- Consumes: existing `.ui-card`, `.ui-card__title`, and `.ui-card__body` markup from `Card.jsx`.
- Produces: one global visual contract inherited by every existing `Card` consumer.

- [x] **Step 1: Write the failing global-card contract test**

Create `Card.test.jsx` with:

```jsx
import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "vitest";

import Card from "./Card";

const cardStyles = readFileSync(resolve("src/components/ui/Card.css"), "utf8");

test("renderiza título e conteúdo com os hooks globais", () => {
  render(<Card title="Resumo">Conteúdo</Card>);

  expect(screen.getByRole("heading", { name: "Resumo" })).toHaveClass("ui-card__title");
  expect(screen.getByText("Conteúdo")).toHaveClass("ui-card__body");
});

test("define a superfície, o título e o padding móvel no CSS global", () => {
  expect(cardStyles).toContain("border: 2px solid var(--color-text-primary);");
  expect(cardStyles).toContain("box-shadow: 4px 4px 0 var(--color-text-primary);");
  expect(cardStyles).toContain("font-size: var(--font-size-lg);");
  expect(cardStyles).toContain("font-weight: 700;");
  expect(cardStyles).toContain(".ui-card__title::before");
  expect(cardStyles).toContain("background: var(--color-accent);");
  expect(cardStyles).toContain("@media (max-width: 640px)");
  expect(cardStyles).toContain("padding: var(--space-sm);");
});
```

- [x] **Step 2: Run RED**

Run:

```bash
cd frontend
npm test -- src/components/ui/Card.test.jsx
```

Expected: the rendering test passes and the CSS contract fails because the current card still uses a neutral 1px border, no shadow, smaller title, and no marker/mobile rule.

- [x] **Step 3: Replace `Card.css` with the global surface**

Use this complete content:

```css
.ui-card {
  padding: var(--space-md);
  background: var(--color-white);
  border: 2px solid var(--color-text-primary);
  border-radius: var(--radius-card);
  box-shadow: 4px 4px 0 var(--color-text-primary);
}

.ui-card__title {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin: 0 0 var(--space-sm);
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.ui-card__title::before {
  content: "";
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  background: var(--color-accent);
  border-radius: var(--radius-circle);
}

.ui-card__body {
  color: var(--color-text-secondary);
}

@media (max-width: 640px) {
  .ui-card {
    padding: var(--space-sm);
  }
}
```

- [x] **Step 4: Remove obsolete Home card-surface rules and its local CSS test**

In `HomePage.css`, keep only the height behavior:

```css
.home-page__summary-grid .ui-card {
  height: 100%;
}

.home-page__goal-card,
.home-page__goal-card > .ui-card {
  height: 100%;
}
```

Delete these selectors and their declarations entirely:

```css
.home-page__goal-card > .ui-card
.home-page__goal-card .ui-card__title
.home-page__goal-card .ui-card__title::before
.home-page__statistics > .ui-card
.home-page__statistics .ui-card__title
.home-page__statistics .ui-card__title::before
```

Also delete the mobile `.home-page__statistics > .ui-card` padding rule. In `HomePage.test.jsx`, remove `readFileSync`, `resolve`, `homeStyles`, and the test named `usa a mesma sombra preta nos dois cards de resumo`; the new `Card.test.jsx` owns this global contract.

- [x] **Step 5: Remove obsolete StudySession surface overrides**

Replace the two card selectors with:

```css
.study-session > .ui-card .ui-card__title {
  justify-content: center;
  text-align: center;
}

.study-session > .ui-card .ui-card__body {
  color: var(--color-text-primary);
  text-align: center;
}
```

Delete `.study-session > .ui-card` and delete the mobile padding override for that selector. Do not change the progress or rating-button rules.

- [x] **Step 6: Run GREEN and focused regressions**

Run:

```bash
cd frontend
npm test -- src/components/ui/Card.test.jsx HomePage.test.jsx StudySessionPage.test.jsx
npm run lint
cd ..
git diff --check
```

Expected: all focused tests, lint, and diff check exit 0.

- [x] **Step 7: Commit the card foundation**

```bash
git add frontend/src/components/ui/Card.test.jsx frontend/src/components/ui/Card.css frontend/src/pages/HomePage.test.jsx frontend/src/pages/HomePage.css frontend/src/pages/StudySessionPage.css
git commit -m "feat(frontend): standardize global card surface"
```

---

### Task 2: Build the reusable rating-distribution chart

**Files:**
- Create: `frontend/src/components/charts/RatingDistributionChart.jsx`
- Create: `frontend/src/components/charts/RatingDistributionChart.css`
- Create: `frontend/src/components/charts/RatingDistributionChart.test.jsx`

**Interfaces:**
- Consumes props: `distribution`, `ariaLabel`, `summaryId`, `datasetLabel`, optional `chartRef`.
- Produces: Chart.js `Bar`, `.rating-chart__canvas`, and an accessible `.rating-chart__summary` list in fixed FSRS order.

- [x] **Step 1: Write failing component tests**

Create `RatingDistributionChart.test.jsx`:

```jsx
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
```

- [x] **Step 2: Run RED**

Run:

```bash
cd frontend
npm test -- src/components/charts/RatingDistributionChart.test.jsx
```

Expected: FAIL because `RatingDistributionChart.jsx` does not exist.

- [x] **Step 3: Create the component**

Create `RatingDistributionChart.jsx`:

```jsx
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
```

- [x] **Step 4: Create the shared chart CSS**

Create `RatingDistributionChart.css`:

```css
.rating-chart__canvas {
  position: relative;
  min-height: 320px;
  padding: var(--space-sm);
  overflow: hidden;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.rating-chart__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-xs);
  margin: var(--space-sm) 0 0;
  padding: 0;
  list-style: none;
}

.rating-chart__summary li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-xs);
  min-width: 0;
  padding: var(--space-xs);
  color: var(--color-text-primary);
  background: var(--color-white);
  border: 1px solid var(--color-border);
  border-left: 4px solid var(--color-accent);
  border-radius: var(--radius-card);
  font-size: var(--font-size-sm);
}

.rating-chart__summary strong {
  font-size: var(--font-size-md);
}

@media (max-width: 1024px) {
  .rating-chart__canvas {
    min-height: 260px;
  }
}

@media (max-width: 640px) {
  .rating-chart__canvas {
    min-height: 240px;
    padding: var(--space-xs);
  }

  .rating-chart__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .rating-chart__summary li {
    align-items: flex-start;
    flex-direction: column;
  }
}
```

- [x] **Step 5: Run GREEN and commit**

Run:

```bash
cd frontend
npm test -- src/components/charts/RatingDistributionChart.test.jsx
npm run lint
cd ..
git diff --check
git add frontend/src/components/charts/RatingDistributionChart.jsx frontend/src/components/charts/RatingDistributionChart.css frontend/src/components/charts/RatingDistributionChart.test.jsx
git commit -m "feat(frontend): add shared rating chart"
```

Expected: four component tests pass; lint and diff check exit 0.

---

### Task 3: Migrate Home and deck detail to the shared chart

**Files:**
- Modify: `frontend/src/pages/HomePage.jsx`
- Modify: `frontend/src/pages/HomePage.css`
- Modify: `frontend/src/pages/HomePage.test.jsx`
- Modify: `frontend/src/pages/DeckDetailPage.jsx`
- Modify: `frontend/src/pages/DeckDetailPage.css`
- Modify: `frontend/src/pages/DeckDetailPage.test.jsx`
- Modify: `frontend/src/tokens/VISUAL_AUDIT.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/design.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/tasks.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/plans/2026-09-16-global-card-rating-chart.md`

**Interfaces:**
- Consumes: `RatingDistributionChart` from Task 2 and the global `Card` surface from Task 1.
- Produces: identical rating-chart presentation on Home and deck detail while preserving each page's data source and errors.

- [x] **Step 1: Strengthen the deck-detail chart test before migration**

Change the `react-chartjs-2` mock in `DeckDetailPage.test.jsx` to expose the shared configuration:

```jsx
vi.mock("react-chartjs-2", () => ({
  Bar: ({ data, options, ...chartProps }) => (
    <div
      {...chartProps}
      role="img"
      data-values={data.datasets[0].data.join(",")}
      data-border-color={data.datasets[0].borderColor}
      data-hover-background={data.datasets[0].hoverBackgroundColor}
      data-x-grid={String(options.scales.x.grid.display)}
      data-y-begin-at-zero={String(options.scales.y.beginAtZero)}
      data-tooltip-background={options.plugins.tooltip.backgroundColor}
    />
  ),
}));
```

Import `colors` from `../tokens/tokens`. In `mostra a distribuição histórica...`, replace the four colon-text assertions with:

```jsx
expect(chart).toHaveAttribute("aria-describedby", "deck-rating-summary");
expect(chart).toHaveAttribute("data-border-color", colors.textPrimary);
expect(chart).toHaveAttribute("data-hover-background", colors.bgDark);
expect(chart).toHaveAttribute("data-x-grid", "false");
expect(chart).toHaveAttribute("data-y-begin-at-zero", "true");
expect(chart).toHaveAttribute("data-tooltip-background", colors.bgDark);

const summary = screen.getByRole("list", { name: "Resumo das classificações" });
expect(summary).toHaveAttribute("id", "deck-rating-summary");
expect(summary).toHaveTextContent("Errou2");
expect(summary).toHaveTextContent("Difícil3");
expect(summary).toHaveTextContent("Bom5");
expect(summary).toHaveTextContent("Fácil7");
```

- [x] **Step 2: Run the deck-detail RED test**

Run:

```bash
cd frontend
npm test -- DeckDetailPage.test.jsx
```

Expected: the historical-distribution test fails because the current deck chart has no shared tokenized options, no `aria-describedby`, and no labeled summary list.

- [x] **Step 3: Migrate `HomePage.jsx`**

Remove direct imports from `react-chartjs-2`, `chart.js`, and `colors`, `radius`, `typography`. Remove `ChartJS.register`, `RATING_KEYS`, `RATING_LABELS`, `distribution`, `prefersReducedMotion`, `chartData`, and `chartOptions`.

Import:

```jsx
import RatingDistributionChart from "../components/charts/RatingDistributionChart";
```

Keep:

```jsx
const ratingDistribution = deckStatistics?.rating_distribution ?? {};
```

Replace the chart wrapper and summary list with:

```jsx
<RatingDistributionChart
  distribution={ratingDistribution}
  ariaLabel="Distribuição das classificações da Home"
  summaryId="home-rating-summary"
  datasetLabel="Revisões por resultado"
  chartRef={chartRef}
/>
```

- [x] **Step 4: Remove chart-only rules from `HomePage.css`**

Delete these selectors and their media overrides:

```css
.home-page__chart
.home-page__statistics-values
.home-page__statistics-values li
.home-page__statistics-values strong
```

Do not alter `.home-page__actions`, CTAs, goal progress, or reduced-motion rules for CTA/progress.

- [x] **Step 5: Migrate `DeckDetailPage.jsx`**

Remove direct imports from `react-chartjs-2`, `chart.js`, and `colors`; remove `ChartJS.register`, `RATING_LABELS`, `RATING_KEYS`, `ratingValues`, and `chartData`.

Import:

```jsx
import RatingDistributionChart from "../components/charts/RatingDistributionChart";
```

Replace the chart wrapper and summary list with:

```jsx
<RatingDistributionChart
  distribution={ratingDistribution}
  ariaLabel="Distribuição das classificações do deck"
  summaryId="deck-rating-summary"
  datasetLabel="Revisões por classificação"
/>
```

- [x] **Step 6: Remove chart-only rules from `DeckDetailPage.css`**

Delete these selectors and their media overrides:

```css
.deck-detail__chart
.deck-detail__statistics-values
```

Preserve header, card-list, pagination, form, error, and responsive navigation rules.

- [x] **Step 7: Run page GREEN tests**

Run:

```bash
cd frontend
npm test -- HomePage.test.jsx DeckDetailPage.test.jsx src/components/charts/RatingDistributionChart.test.jsx
```

Expected: all Home, deck-detail, and shared-component tests pass.

- [x] **Step 8: Update Sprint 9 documentation**

Append this decision to `design.md`:

```markdown
### D11 — Card global e gráfico de classificações compartilhado
`Card.css` passa a ser a fonte única da superfície branca com borda preta de 2 px, sombra preta deslocada e título com marcador laranja. O padrão alcança listas, formulários, estados vazios, diálogos, Home, detalhe e sessão de estudo; CSS de página mantém somente composição local. Não há hover global porque nem todo card é interativo.

Home e detalhe do deck passam a consumir `RatingDistributionChart`, que normaliza `again`/`hard`/`good`/`easy`, concentra dataset/opções tokenizados, resumo textual associado e redução de movimento. Requests, loading e erros continuam nas páginas; somente a Home fornece `chartRef` para exportação PDF.

- **Alternativa descartada**: copiar o CSS/configuração da Home para o detalhe. Rejeitada porque manteria duas fontes de verdade e permitiria nova divergência visual.
```

Append to `tasks.md`:

```markdown
- [x] 7.13 Globalizar superfície/título de `Card`, remover sobrescritas duplicadas e extrair `RatingDistributionChart` compartilhado entre Home e detalhe, preservando APIs, erros, exportação e comportamento das páginas
```

Add this Sprint 9 CHANGELOG bullet:

```markdown
- **Design system de cards e estatísticas**: `Card` passa a fornecer globalmente fundo branco, borda/sombra pretas, título forte e marcador laranja; Home e detalhe do deck compartilham o mesmo gráfico tokenizado, resumo acessível, responsividade e redução de movimento. A sessão de estudo adota a sombra preta global sem perder os botões semânticos.
```

Change the Sprint 9 validation count from `55 de frontend` to `60 de frontend` after the full suite confirms it. Append to `VISUAL_AUDIT.md`:

```markdown
## Revalidação — Sprint 9 (cards e gráficos globais)

- `Card.css` é a fonte única de fundo, borda, sombra, título e marcador para todas as superfícies `ui-card`; páginas mantêm apenas layout contextual.
- `RatingDistributionChart.css` concentra canvas, resumo textual e breakpoints dos gráficos da Home e do detalhe, sem cores literais fora dos tokens.
- A auditoria automatizada de cores, a suíte completa, o lint e o build foram reexecutados após a remoção das regras duplicadas.
```

- [x] **Step 9: Run full verification**

Run:

```bash
cd frontend
npm run lint
npm test
npm run build
rg -n --glob '*.css' --glob '*.jsx' --glob '!*.test.jsx' 'rgb\(|#[0-9a-fA-F]{3,8}' src | rg -v 'src/tokens/tokens\.(css|js)' || true
cd ..
git diff --check
```

Expected: lint, all frontend tests, build, color audit, and diff check exit 0; the color audit prints no application matches.

- [x] **Step 10: Complete the plan and commit**

Mark every checkbox in this plan complete, then run:

```bash
git add frontend/src/pages/HomePage.jsx frontend/src/pages/HomePage.css frontend/src/pages/HomePage.test.jsx frontend/src/pages/DeckDetailPage.jsx frontend/src/pages/DeckDetailPage.css frontend/src/pages/DeckDetailPage.test.jsx frontend/src/tokens/VISUAL_AUDIT.md openspec/changes/sprint-9-tela-de-estudo/design.md openspec/changes/sprint-9-tela-de-estudo/tasks.md CHANGELOG.md docs/superpowers/plans/2026-09-16-global-card-rating-chart.md
git commit -m "refactor(frontend): unify card and rating chart UI"
```

## Plan self-review

- Covers every approved Card consumer through the global component without adding variants.
- Covers the shared chart interface, tokenized options, summary accessibility, reduced motion, optional export ref, and both page integrations.
- Preserves loading, errors, API calls, PDF export, study behavior, routes, forms, and dialogs.
- Removes every identified page-local duplicate while retaining layout-specific selectors.
- Contains exact test, component, CSS, migration, documentation, verification, and commit steps with no deferred implementation placeholders.
