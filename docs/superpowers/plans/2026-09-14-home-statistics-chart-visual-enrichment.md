# Home Statistics Chart Visual Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the Home statistics chart a professional orange/black presentation and an accessible textual value summary without changing its data flow or export behavior.

**Architecture:** Keep the existing Chart.js `Bar` and data calculation in `HomePage`. Enrich its dataset/options with existing JS tokens, add one semantic summary list fed by the same `distribution.values`, and scope every surface rule below `.home-page__statistics`.

**Tech Stack:** React 19, Chart.js, react-chartjs-2, Vitest, Testing Library, CSS custom properties.

## Global Constraints

- Preserve all review/deck API calls, loading/error branches, and `exportChartToPdf(chartRef.current)`.
- Keep the labels `Errou`, `Difícil`, `Bom`, and `Fácil` and their existing `again`, `hard`, `good`, `easy` ordering.
- Use only existing `colors`, `typography`, and `radius` JS tokens and existing CSS custom properties.
- Do not change global `Card`, `Button`, tokens, `DeckDetailPage`, Sidebar, study CTAs, or install dependencies.
- Keep normal Chart.js animation unchanged; set `animation: false` only when reduced motion is requested.
- At `<=640px`, the chart and summary must fit without horizontal overflow at a 320px viewport.

---

### Task 1: Enrich the Home statistics chart

**Files:**
- Modify: `frontend/src/pages/HomePage.test.jsx`
- Modify: `frontend/src/pages/HomePage.jsx`
- Modify: `frontend/src/pages/HomePage.css`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/design.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/tasks.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `distribution.labels: string[]`, `distribution.values: number[]`, `chartRef`, and existing design tokens.
- Produces: `chartOptions`, a themed dataset, and `<ul id="home-rating-summary">` associated with the existing chart.

- [ ] **Step 1: Upgrade the Bar mock so tests can observe visual configuration**

Replace the current `react-chartjs-2` mock in `HomePage.test.jsx` with:

```jsx
vi.mock("react-chartjs-2", () => ({
  Bar: ({ data, options, ...chartProps }) => (
    <div
      {...chartProps}
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
  ),
}));
```

Do not spread a `ref` value onto the test DOM node if the active React version exposes it in `chartProps`; destructure it separately if the focused test warns.

- [ ] **Step 2: Write failing tests for the themed chart, summary, and reduced motion**

Import the JS tokens:

```jsx
import { colors, radius } from "../tokens/tokens";
```

Add these assertions to the existing successful statistics test after locating `chart`:

```jsx
expect(chart).toHaveAttribute("aria-describedby", "home-rating-summary");
expect(chart).toHaveAttribute("data-border-color", colors.textPrimary);
expect(chart).toHaveAttribute("data-hover-background", colors.bgDark);
expect(chart).toHaveAttribute("data-border-radius", String(Number.parseFloat(radius.card)));
expect(chart).toHaveAttribute("data-x-grid", "false");
expect(chart).toHaveAttribute("data-y-begin-at-zero", "true");
expect(chart).toHaveAttribute("data-tooltip-background", colors.bgDark);

const summary = screen.getByRole("list", { name: "Resumo das classificações" });
expect(summary).toHaveAttribute("id", "home-rating-summary");
expect(summary).toHaveTextContent("Errou3");
expect(summary).toHaveTextContent("Difícil4");
expect(summary).toHaveTextContent("Bom3");
expect(summary).toHaveTextContent("Fácil2");
```

Add a focused test:

```jsx
test("desativa a animação do gráfico quando o usuário prefere movimento reduzido", async () => {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn().mockReturnValue({ matches: true }),
  });

  renderHome();

  const chart = await screen.findByRole("img", {
    name: "Distribuição das classificações da Home",
  });
  expect(chart).toHaveAttribute("data-animation", "disabled");
});
```

- [ ] **Step 3: Run the focused test and verify RED**

Run:

```bash
cd frontend && npm test -- HomePage.test.jsx
```

Expected: FAIL because the dataset has no border/hover configuration, the options have no scales/tooltip theme or reduced-motion value, and `home-rating-summary` does not exist.

- [ ] **Step 4: Add token-driven chart data and options**

Change the token import in `HomePage.jsx`:

```jsx
import { colors, radius, typography } from "../tokens/tokens";
```

Immediately after `hasValidLastDeck`, derive motion preference:

```jsx
const prefersReducedMotion = Boolean(
  typeof window !== "undefined"
  && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,
);
```

Replace `chartData` and add `chartOptions`:

```jsx
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
```

- [ ] **Step 5: Associate the chart with a semantic value summary**

Replace only the successful chart fragment with:

```jsx
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
```

Keep the existing `home-page__actions` and export button immediately after this list.

- [ ] **Step 6: Add locally scoped expressive CSS**

Extend `HomePage.css` without changing the study-action rules:

```css
.home-page__statistics > .ui-card {
  border: 2px solid var(--color-text-primary);
  box-shadow: 4px 4px 0 var(--color-text-primary);
}

.home-page__statistics .ui-card__title {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--font-size-lg);
}

.home-page__statistics .ui-card__title::before {
  content: "";
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: var(--radius-circle);
  background: var(--color-accent);
}

.home-page__chart {
  position: relative;
  min-height: 320px;
  padding: var(--space-sm);
  overflow: hidden;
  background: var(--color-bg-light);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.home-page__statistics-values {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-xs);
  margin: var(--space-sm) 0 0;
  padding: 0;
  list-style: none;
}

.home-page__statistics-values li {
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

.home-page__statistics-values strong {
  font-size: var(--font-size-md);
}
```

Under the existing `@media (max-width: 640px)` block add:

```css
.home-page__statistics > .ui-card {
  padding: var(--space-sm);
}

.home-page__chart {
  min-height: 240px;
  padding: var(--space-xs);
}

.home-page__statistics-values {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
```

- [ ] **Step 7: Run GREEN verification**

Run:

```bash
cd frontend
npm test -- HomePage.test.jsx
npm run lint
npm test
npm run build
cd ..
git diff --check
```

Expected: focused Home tests pass, all frontend tests pass, lint/build exit 0, and diff check is clean.

- [ ] **Step 8: Update Sprint 9 records**

In `openspec/changes/sprint-9-tela-de-estudo/design.md`, add a decision recording the local expressive statistics card, token-driven Chart.js theme, textual value summary, and reduced-motion option.

In `openspec/changes/sprint-9-tela-de-estudo/tasks.md`, append:

```markdown
- [x] 7.8 HomePage: enriquecer o gráfico de estatísticas com tema “Contraste expressivo”, resumo textual acessível, responsividade e redução de movimento
```

In the existing Sprint 9 Home entry of `CHANGELOG.md`, mention the themed chart and accessible four-value summary without changing the recorded test count until verification proves a new count.

- [ ] **Step 9: Commit the isolated feature**

```bash
git add frontend/src/pages/HomePage.test.jsx frontend/src/pages/HomePage.jsx frontend/src/pages/HomePage.css openspec/changes/sprint-9-tela-de-estudo/design.md openspec/changes/sprint-9-tela-de-estudo/tasks.md CHANGELOG.md
git diff --cached --check
git commit -m "feat(frontend): enrich home statistics chart"
```

Expected: one commit containing only the six files above.

## Plan self-review

- Spec coverage: chart surface, dataset/options, textual equivalent, mobile behavior, reduced motion, export ref, and docs are each assigned to explicit steps.
- Placeholder scan: no TBD/TODO or deferred implementation remains.
- Type consistency: token names match `tokens.js`; the summary uses existing `distribution.labels`, `distribution.values`, and `RATING_KEYS`; `chartRef` remains on `Bar`.
