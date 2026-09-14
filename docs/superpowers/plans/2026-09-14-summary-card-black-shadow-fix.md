# Summary Card Black Shadow Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give both Home summary cards the same black `4px 4px 0` shadow as the statistics card and remove the goal card's orange shadow override.

**Architecture:** Keep the existing markup and global `Card` unchanged. Define the border and black shadow once on `.home-page__summary-grid .ui-card`; retain only the white background in the goal-specific surface rule.

**Tech Stack:** React 18, Vitest, Node filesystem API in tests, CSS custom properties.

## Global Constraints

- Both summary cards keep a `2px` black border.
- Both summary cards use `box-shadow: 4px 4px 0 var(--color-text-primary)`.
- The goal card must not override the shared shadow with orange.
- Orange remains on the goal marker, percentage badge, and progress fill.
- Do not change JSX, APIs, progress calculations, global `Card`, CTAs, chart, or Sidebar.

---

### Task 1: Unify the summary-card shadow

**Files:**
- Modify: `frontend/src/pages/HomePage.test.jsx`
- Modify: `frontend/src/pages/HomePage.css`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/design.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/tasks.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `.home-page__summary-grid .ui-card` and `.home-page__goal-card > .ui-card`.
- Produces: one shared black-shadow declaration for both summary cards.

- [x] **Step 1: Add the failing visual-contract test**

Add the filesystem import and stylesheet fixture to `HomePage.test.jsx`:

```jsx
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const homeStyles = readFileSync(resolve("src/pages/HomePage.css"), "utf8");
```

Add this test to `describe("meta de estudo da Home", ...)`:

```jsx
test("usa a mesma sombra preta nos dois cards de resumo", () => {
  expect(homeStyles).toContain(`.home-page__summary-grid .ui-card {
  height: 100%;
  border: 2px solid var(--color-text-primary);
  box-shadow: 4px 4px 0 var(--color-text-primary);
}`);
  expect(homeStyles).not.toMatch(
    /\.home-page__goal-card > \.ui-card\s*\{[^}]*box-shadow:/,
  );
});
```

- [x] **Step 2: Run RED**

Run:

```bash
cd frontend
npm test -- HomePage.test.jsx
```

Expected: the new test fails because the shared rule has no shadow and the goal-specific rule declares an orange shadow.

- [x] **Step 3: Apply the minimal CSS correction**

Change the two rules in `HomePage.css` to exactly:

```css
.home-page__summary-grid .ui-card {
  height: 100%;
  border: 2px solid var(--color-text-primary);
  box-shadow: 4px 4px 0 var(--color-text-primary);
}

.home-page__goal-card > .ui-card {
  background: var(--color-white);
}
```

- [x] **Step 4: Run GREEN and regressions**

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

Expected: 11 Home tests and 55 total frontend tests pass; lint, build, and diff check exit 0.

- [x] **Step 5: Update Sprint records and commit**

In `design.md`, clarify D8 with the shared black shadow. Add task 7.12 and update the Sprint 9 CHANGELOG bullet plus frontend test count. Commit only the five listed files and this completed plan:

```bash
git add frontend/src/pages/HomePage.test.jsx frontend/src/pages/HomePage.css openspec/changes/sprint-9-tela-de-estudo/design.md openspec/changes/sprint-9-tela-de-estudo/tasks.md CHANGELOG.md docs/superpowers/plans/2026-09-14-summary-card-black-shadow-fix.md
git commit -m "fix(frontend): unify Home summary card shadows"
```

## Plan self-review

- Covers the approved border/shadow distinction and keeps orange only inside the goal card.
- Uses existing selectors and tokens without markup or global-component changes.
- Includes a RED/GREEN regression that detects both the missing shared shadow and future goal-specific overrides.
- Contains no deferred implementation placeholders.
