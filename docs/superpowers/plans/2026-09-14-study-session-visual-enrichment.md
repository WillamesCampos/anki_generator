# Study Session Visual Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich the study-session card with centered hierarchy, the shared black border, and semantically colored rating actions while preserving the review flow.

**Architecture:** Keep `RATINGS` and `handleRate` unchanged. Add paired semantic color tokens, expose each existing rating through `data-rating`, and scope all surface, layout, interaction, responsive, and motion rules to `.study-session`.

**Tech Stack:** React 18, Vitest, Testing Library, CSS/JS design tokens.

## Global Constraints

- Preserve rating labels, values, ordering, API calls, loading, errors, empty/completed states, counters, routes, and disabled behavior.
- Do not modify global `Button` or `Card`.
- Use a white card, `2px` black border, orange offset shadow, and centered text.
- Rating colors must be tokenized: red/white, amber/black, blue/white, green/white.
- Desktop uses four columns, <=1024 uses two, <=640 uses one; no overflow at 320px.
- Support focus-visible, disabled, and reduced motion.

---

### Task 1: Add semantic rating buttons and the expressive study card

**Files:**
- Modify: `frontend/src/tokens/tokens.css`
- Modify: `frontend/src/tokens/tokens.js`
- Modify: `frontend/src/pages/StudySessionPage.test.jsx`
- Modify: `frontend/src/pages/StudySessionPage.jsx`
- Modify: `frontend/src/pages/StudySessionPage.css`
- Modify: `frontend/src/tokens/VISUAL_AUDIT.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/design.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/tasks.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: existing `RATINGS` and `Button` prop spreading.
- Produces: four CSS/JS rating tokens and `data-rating="again|hard|good|easy"`.

- [x] **Step 1: Write the failing semantic-rating test**

In the existing complete-flow test, after revealing the answer and before clicking `Bom`, add:

```jsx
const expectedRatings = [
  ["Errei", "again"],
  ["Difícil", "hard"],
  ["Bom", "good"],
  ["Fácil", "easy"],
];

expectedRatings.forEach(([label, rating]) => {
  const button = screen.getByRole("button", { name: label });
  expect(button).toHaveClass("ui-button", "ui-button--secondary");
  expect(button).toHaveAttribute("data-rating", rating);
});
```

Add a token test in the same file:

```jsx
import { colors } from "../tokens/tokens";

test("expõe as quatro cores semânticas de avaliação", () => {
  expect(colors.ratingAgain).toBe("rgb(220, 38, 38)");
  expect(colors.ratingHard).toBe("rgb(245, 158, 11)");
  expect(colors.ratingGood).toBe("rgb(37, 99, 235)");
  expect(colors.ratingEasy).toBe("rgb(21, 128, 61)");
});
```

- [x] **Step 2: Run RED**

Run `cd frontend && npm test -- StudySessionPage.test.jsx`.

Expected: failures because `data-rating` and the four JS token properties do not exist.

- [x] **Step 3: Add paired rating tokens**

Add to `tokens.css` after `--color-overlay`:

```css
--color-rating-again: rgb(220, 38, 38);
--color-rating-hard: rgb(245, 158, 11);
--color-rating-good: rgb(37, 99, 235);
--color-rating-easy: rgb(21, 128, 61);
```

Add to `colors` in `tokens.js`:

```js
ratingAgain: "rgb(220, 38, 38)",
ratingHard: "rgb(245, 158, 11)",
ratingGood: "rgb(37, 99, 235)",
ratingEasy: "rgb(21, 128, 61)",
```

Update `VISUAL_AUDIT.md` to record these four paired semantic rating tokens and their local use.

- [x] **Step 4: Expose the existing rating value to local CSS**

Add only this prop to each mapped rating `Button` in `StudySessionPage.jsx`:

```jsx
data-rating={value}
```

Do not add `className` and do not change `RATINGS` or `handleRate`.

- [x] **Step 5: Replace StudySessionPage.css with the enriched local styles**

Keep the existing error/summary/empty rules and add/replace the presentation with:

```css
.study-session__progress {
  width: fit-content;
  margin: 0 auto var(--space-md);
  padding: 5px var(--space-sm);
  color: var(--color-white);
  background: var(--color-text-primary);
  border-left: 5px solid var(--color-accent);
  border-radius: var(--radius-pill);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.study-session > .ui-card {
  border: 2px solid var(--color-text-primary);
  box-shadow: 4px 4px 0 var(--color-accent);
}

.study-session > .ui-card .ui-card__title {
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 700;
  text-align: center;
}

.study-session > .ui-card .ui-card__body {
  color: var(--color-text-primary);
  text-align: center;
}

.study-session__back {
  margin: 0;
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: 700;
}

.study-session__description {
  max-width: 60ch;
  margin: var(--space-xs) auto 0;
  color: var(--color-text-secondary);
}

.study-session__ratings {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-sm);
  width: 100%;
  margin-top: var(--space-md);
}

.study-session [data-rating] {
  min-height: 44px;
  border: 2px solid var(--color-text-primary);
  border-radius: var(--radius-card);
  box-shadow: 3px 3px 0 var(--color-text-primary);
  opacity: 1;
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.2s ease;
}

.study-session [data-rating="again"] {
  color: var(--color-white);
  background: var(--color-rating-again);
}

.study-session [data-rating="hard"] {
  color: var(--color-text-primary);
  background: var(--color-rating-hard);
}

.study-session [data-rating="good"] {
  color: var(--color-white);
  background: var(--color-rating-good);
}

.study-session [data-rating="easy"] {
  color: var(--color-white);
  background: var(--color-rating-easy);
}

.study-session [data-rating]:hover:not(:disabled) {
  box-shadow: 1px 1px 0 var(--color-text-primary);
  opacity: 1;
  transform: translate(2px, 2px);
}

.study-session [data-rating]:active:not(:disabled) {
  box-shadow: none;
  transform: translate(3px, 3px);
}

.study-session [data-rating]:focus-visible {
  outline: 3px solid var(--color-text-primary);
  outline-offset: 3px;
}

.study-session [data-rating]:disabled {
  box-shadow: 3px 3px 0 var(--color-text-primary);
  opacity: 0.55;
  transform: none;
}
```

Add the responsive and reduced-motion rules exactly as follows:

```css
@media (max-width: 1024px) {
  .study-session__ratings {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .study-session > .ui-card {
    padding: var(--space-sm);
  }

  .study-session__ratings {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (prefers-reduced-motion: reduce) {
  .study-session [data-rating] {
    transition: none;
  }

  .study-session [data-rating]:hover:not(:disabled),
  .study-session [data-rating]:active:not(:disabled) {
    box-shadow: 3px 3px 0 var(--color-text-primary);
    transform: none;
  }
}
```

- [x] **Step 6: Run GREEN and regression checks**

Run focused StudySession tests, ESLint, full Vitest, Vite build, the visual-audit hardcoded-color search, and `git diff --check`. Expected: all exit 0.

- [x] **Step 7: Update Sprint records and commit**

Append task 7.11, add a design decision for the study-session surface and semantic rating tokens, and add a concise CHANGELOG entry. Commit only the nine listed files:

```bash
git add frontend/src/tokens/tokens.css frontend/src/tokens/tokens.js frontend/src/tokens/VISUAL_AUDIT.md frontend/src/pages/StudySessionPage.test.jsx frontend/src/pages/StudySessionPage.jsx frontend/src/pages/StudySessionPage.css openspec/changes/sprint-9-tela-de-estudo/design.md openspec/changes/sprint-9-tela-de-estudo/tasks.md CHANGELOG.md
git commit -m "feat(frontend): enrich study session feedback"
```

## Plan self-review

- Covers exact paired tokens, TDD, preserved ratings/API, centered white card, black border, semantic colors, all interaction states, breakpoints, reduced motion, audit/docs, and isolated commit.
- `data-rating` relies on the existing Button prop spread and does not replace global classes.
- Contains no deferred implementation placeholders.
