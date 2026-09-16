# Home Goal Card Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the Home study-goal card into a white, accessible progress panel and give both top summary cards the same black border as the statistics card.

**Architecture:** Keep `computeGoalProgress` and the global `Card` unchanged. Derive only `remainingGoal` in `HomePage`, wrap the goal card with a local hook, render a semantic progressbar, and scope all presentation to Home selectors.

**Tech Stack:** React 18, Vitest, Testing Library, CSS custom properties.

## Global Constraints

- Keep the card background white.
- Both cards in `.home-page__summary-grid` receive a `2px` black border.
- Do not change APIs, localStorage, `computeGoalProgress`, global `Card`, global `Button`, CTAs, chart, or Sidebar.
- Progress values come only from `goalProgress.reviewedToday`, `goalProgress.goal`, and `goalProgress.percentage`.
- The progressbar uses a 0–100 ARIA scale and a textual reviewed/goal description.
- Use only existing CSS tokens and support 320px plus reduced motion.

---

### Task 1: Build the white study-goal progress panel

**Files:**
- Modify: `frontend/src/pages/HomePage.test.jsx`
- Modify: `frontend/src/pages/HomePage.jsx`
- Modify: `frontend/src/pages/HomePage.css`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/design.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/tasks.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `goalProgress: { reviewedToday: number, goal: number, percentage: number }`.
- Produces: `.home-page__goal-card`, `role="progressbar"`, and `--goal-progress` from `percentage`.

- [x] **Step 1: Add failing goal-card tests**

Add a `describe("meta de estudo da Home", ...)` block to `HomePage.test.jsx`. In its `beforeEach`, clear mocks and provide empty defaults for reviews. Add three tests:

```jsx
describe("meta de estudo da Home", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetchReviews.mockResolvedValue({ results: [] });
  });

  test("mostra a meta inicial como progresso acessível", async () => {
    renderHome();
    await screen.findByText("Você ainda não revisou nenhum card.");

    const progress = screen.getByRole("progressbar", { name: "Progresso da meta diária" });
    expect(progress).toHaveAttribute("aria-valuemin", "0");
    expect(progress).toHaveAttribute("aria-valuemax", "100");
    expect(progress).toHaveAttribute("aria-valuenow", "0");
    expect(progress).toHaveAttribute("aria-valuetext", "0 de 20 cards revisados hoje");
    expect(screen.getByText("20 cards para concluir sua meta")).toBeInTheDocument();
    expect(screen.getByText("0%", { selector: ".home-page__goal-percent" })).toBeInTheDocument();
  });

  test("calcula o progresso parcial com as revisões de hoje", async () => {
    const today = new Date().toISOString();
    fetchReviews.mockResolvedValue({
      results: Array.from({ length: 5 }, (_, index) => ({
        id: `review-${index}`,
        deck_id: "deck-last",
        rating: "good",
        reviewed_at: today,
      })),
    });
    fetchDeck.mockResolvedValue(LAST_DECK);
    fetchDeckStatistics.mockResolvedValue({ rating_distribution: {} });

    renderHome();

    const progress = screen.getByRole("progressbar", { name: "Progresso da meta diária" });
    await waitFor(() => expect(progress).toHaveAttribute("aria-valuenow", "25"));
    expect(progress).toHaveAttribute("aria-valuetext", "5 de 20 cards revisados hoje");
    expect(screen.getByText("15 cards para concluir sua meta")).toBeInTheDocument();
  });

  test("mostra a conclusão quando a meta diária é atingida", async () => {
    const today = new Date().toISOString();
    fetchReviews.mockResolvedValue({
      results: Array.from({ length: 20 }, (_, index) => ({
        id: `review-${index}`,
        deck_id: "deck-last",
        rating: "easy",
        reviewed_at: today,
      })),
    });
    fetchDeck.mockResolvedValue(LAST_DECK);
    fetchDeckStatistics.mockResolvedValue({ rating_distribution: {} });

    renderHome();

    const progress = screen.getByRole("progressbar", { name: "Progresso da meta diária" });
    await waitFor(() => expect(progress).toHaveAttribute("aria-valuenow", "100"));
    expect(screen.getByText("Meta concluída hoje!")).toBeInTheDocument();
  });
});
```

- [x] **Step 2: Run RED**

Run `cd frontend && npm test -- HomePage.test.jsx`.

Expected: three new tests fail because no progressbar, percent badge, or helper exists.

- [x] **Step 3: Implement the semantic goal panel**

After `goalProgress` in `HomePage.jsx`, add:

```jsx
const remainingGoal = Math.max(goalProgress.goal - goalProgress.reviewedToday, 0);
const goalComplete = goalProgress.percentage >= 100;
```

Replace the current goal `Card` with:

```jsx
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
```

- [x] **Step 4: Add the local white-card CSS**

Add to `HomePage.css` after `.home-page__summary-grid`:

```css
.home-page__summary-grid .ui-card {
  height: 100%;
  border: 2px solid var(--color-text-primary);
}

.home-page__goal-card,
.home-page__goal-card > .ui-card {
  height: 100%;
}

.home-page__goal-card > .ui-card {
  background: var(--color-white);
  box-shadow: 4px 4px 0 var(--color-accent);
}

.home-page__goal-card .ui-card__title {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  color: var(--color-text-primary);
}

.home-page__goal-card .ui-card__title::before {
  content: "";
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: var(--radius-circle);
  background: var(--color-accent);
}

.home-page__goal-overview {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.home-page__goal-count,
.home-page__goal-label,
.home-page__goal-helper {
  margin: 0;
}

.home-page__goal-count {
  display: flex;
  align-items: baseline;
  color: var(--color-text-primary);
}

.home-page__goal-count strong {
  font-size: var(--font-size-xl);
  line-height: 1;
}

.home-page__goal-count span,
.home-page__goal-label,
.home-page__goal-helper {
  color: var(--color-text-secondary);
}

.home-page__goal-percent {
  padding: 4px var(--space-xs);
  color: var(--color-text-primary);
  background: var(--color-accent);
  border: 2px solid var(--color-text-primary);
  border-radius: var(--radius-pill);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.home-page__goal-progress {
  height: 14px;
  margin-top: var(--space-sm);
  overflow: hidden;
  background: var(--color-bg-light);
  border: 2px solid var(--color-text-primary);
  border-radius: var(--radius-pill);
}

.home-page__goal-progress-fill {
  display: block;
  width: var(--goal-progress);
  height: 100%;
  background: var(--color-accent);
  transition: width 0.25s ease;
}

.home-page__goal-helper {
  margin-top: var(--space-xs);
  font-size: var(--font-size-sm);
  font-weight: 600;
}
```

Add to the existing reduced-motion block:

```css
.home-page__goal-progress-fill {
  transition: none;
}
```

- [x] **Step 5: Run GREEN and regression checks**

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

Expected: Home tests and the complete frontend suite pass; lint/build/diff check exit 0.

- [x] **Step 6: Update Sprint 9 records and commit**

Append task 7.9 to `openspec/changes/sprint-9-tela-de-estudo/tasks.md`, add a design decision for the white goal progress panel and shared top-card border, and add one concise CHANGELOG item. Then commit only the six files:

```bash
git add frontend/src/pages/HomePage.test.jsx frontend/src/pages/HomePage.jsx frontend/src/pages/HomePage.css openspec/changes/sprint-9-tela-de-estudo/design.md openspec/changes/sprint-9-tela-de-estudo/tasks.md CHANGELOG.md
git commit -m "feat(frontend): enrich home study goal"
```

## Plan self-review

- Covers white surface, shared black border, orange accent, ARIA, zero/partial/complete states, 320px, reduced motion, docs, and isolation.
- Uses existing `goalProgress` fields consistently and introduces no API or global-component change.
- Contains no deferred implementation placeholders.
