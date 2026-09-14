# Sidebar Toggle Visual Enrichment Implementation Plan

> **Nota de 2026-09-14:** o pedido explícito do usuário pela ausência de sombra no botão substitui toda exigência ou exemplo histórico de sombra branca neste plano.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved “Contraste expressivo” treatment to the Sidebar collapse/expand control while preserving its state, persistence, routes, logout, and responsive behavior.

**Architecture:** Keep `Sidebar` as the sole owner of `collapsed` and derive the existing labels plus new ARIA state from that boolean. Replace only the typographic glyph with one decorative inline SVG, link the button to the existing navigation list, and scope all sizing, tactile states, collapsed-fit adjustments, and reduced-motion rules to `Sidebar.css`.

**Tech Stack:** React 18.3, React Router 7.18, CSS custom properties, Vitest 4.1, Testing Library, user-event 14.6, ESLint 9, Vite 6.

## Global Constraints

- Use the approved `Contraste expressivo` direction.
- Preserve `COLLAPSED_KEY = "anki_generator_sidebar_collapsed"` and `TABLET_MEDIA_QUERY = "(max-width: 1024px)"` exactly.
- Preserve the current initialization, `matchMedia` listener, manual toggle persistence, logout, links, routes, link labels, and responsive behavior.
- Keep the Sidebar widths at `240px` expanded and `72px` collapsed.
- The local toggle must be exactly `44px × 44px`, orange with a black icon, `var(--radius-card)`, and a `2px` black border, with no box shadow in base, hover, or active states.
- Replace `«`/`»` with one inline double-chevron SVG; it points left when expanded and rotates `180deg` when collapsed.
- The SVG must be decorative and non-focusable with `aria-hidden="true"` and `focusable="false"`.
- The toggle must expose `aria-expanded={!collapsed}` and `aria-controls="sidebar-navigation-list"`; the existing list must expose `id="sidebar-navigation-list"`.
- Keep the current dynamic `aria-label` and `title` values: `Recolher menu` when expanded and `Expandir menu` when collapsed.
- Provide distinct tactile `:hover`, `:active`, and `:focus-visible` states without a box shadow.
- Under `prefers-reduced-motion: reduce`, remove transitions and hover/active transforms while retaining the collapsed icon orientation as an instantaneous state change.
- Adjust only the collapsed Sidebar/header horizontal padding needed to fit the control within `72px`.
- Use only existing tokens; do not modify `frontend/src/tokens/tokens.css` or add dependencies.
- Verify visual CSS with lint, build, and headless/manual inspection; do not add brittle tests that search CSS source text.

---

## File Structure

- `frontend/src/components/layout/Sidebar.test.jsx`: specify the accessible state/control relationship, decorative icon contract, dynamic labels, toggle result, and persisted preference.
- `frontend/src/components/layout/Sidebar.jsx`: add ARIA state/control wiring and replace only the glyph with the inline SVG.
- `frontend/src/components/layout/Sidebar.css`: define the expressive visual, tactile states, icon direction, exact collapsed fit, and reduced-motion behavior.

---

### Task 1: Enrich the Sidebar toggle without changing its behavior

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.test.jsx:53-75`
- Modify: `frontend/src/components/layout/Sidebar.jsx:56-76`
- Modify: `frontend/src/components/layout/Sidebar.css:10-50`

**Interfaces:**
- Consumes: existing React boolean state `collapsed`, `toggleCollapsed()`, `COLLAPSED_KEY`, `TABLET_MEDIA_QUERY`, and CSS tokens from `frontend/src/tokens/tokens.css`.
- Produces: button named `Recolher menu`/`Expandir menu` with `aria-expanded: boolean`, `aria-controls="sidebar-navigation-list"`, and one decorative `<svg className="sidebar__toggle-icon">`; list element with `id="sidebar-navigation-list"`.

- [ ] **Step 1: Strengthen the existing manual-preference test before production changes**

Replace the existing test `preserva e atualiza a preferência manual em viewport de tablet` in `frontend/src/components/layout/Sidebar.test.jsx` with this complete version:

```jsx
  test('expõe o estado acessível e preserva a preferência manual ao alternar', async () => {
    const user = userEvent.setup()
    localStorage.setItem('anki_generator_sidebar_collapsed', 'false')
    installMatchMedia(true)
    renderSidebar()

    const navigation = screen.getByRole('navigation')
    const toggle = screen.getByRole('button', { name: 'Recolher menu' })
    const navigationList = document.getElementById('sidebar-navigation-list')
    const icon = toggle.querySelector('svg')

    expect(navigation).not.toHaveClass('sidebar--collapsed')
    expect(navigationList).toBeInTheDocument()
    expect(navigationList?.tagName).toBe('UL')
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(toggle).toHaveAttribute('aria-controls', 'sidebar-navigation-list')
    expect(toggle).toHaveAttribute('title', 'Recolher menu')
    expect(icon).toHaveAttribute('aria-hidden', 'true')
    expect(icon).toHaveAttribute('focusable', 'false')

    await user.click(toggle)

    expect(navigation).toHaveClass('sidebar--collapsed')
    expect(screen.getByRole('button', { name: 'Expandir menu' })).toBe(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(toggle).toHaveAttribute('title', 'Expandir menu')
    expect(localStorage.getItem('anki_generator_sidebar_collapsed')).toBe('true')
  })
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run from `frontend/`:

```bash
npm test -- src/components/layout/Sidebar.test.jsx
```

Expected: the enriched test fails because the current button has no `aria-expanded`, no `aria-controls`, no SVG, and the list has no `sidebar-navigation-list` id. The two existing viewport tests continue to pass.

- [ ] **Step 3: Add the ARIA relationship and decorative double-chevron SVG**

In `frontend/src/components/layout/Sidebar.jsx`, replace the current toggle `<button>` and the opening `<ul>` tag with exactly:

```jsx
        <button
          type="button"
          className="sidebar__toggle"
          onClick={toggleCollapsed}
          aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
          aria-expanded={!collapsed}
          aria-controls="sidebar-navigation-list"
          title={collapsed ? "Expandir menu" : "Recolher menu"}
        >
          <svg
            className="sidebar__toggle-icon"
            viewBox="0 0 24 24"
            aria-hidden="true"
            focusable="false"
          >
            <path d="m13 17-5-5 5-5" />
            <path d="m19 17-5-5 5-5" />
          </svg>
        </button>
      </div>
      <ul id="sidebar-navigation-list" className="sidebar__list">
```

Do not change `toggleCollapsed`, either dynamic string, the `<nav>`, any list item, link, or logout markup.

- [ ] **Step 4: Implement the exact collapsed fit and expressive control styles**

In `frontend/src/components/layout/Sidebar.css`, replace the current `.sidebar--collapsed`, `.sidebar--collapsed .sidebar__header`, `.sidebar__toggle`, and `.sidebar__toggle:hover` rules with this complete set, keeping the intervening unchanged rules in their current order:

```css
.sidebar--collapsed {
  width: 72px;
  padding-right: var(--space-xs);
  padding-left: var(--space-xs);
}

.sidebar--collapsed .sidebar__header {
  flex-direction: column;
  gap: var(--space-sm);
  padding-right: 0;
  padding-left: 0;
}

.sidebar__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  box-sizing: border-box;
  flex-shrink: 0;
  background: var(--color-accent);
  border: 2px solid var(--color-text-primary);
  border-radius: var(--radius-card);
  box-shadow: 4px 4px 0 var(--color-white);
  color: var(--color-text-primary);
  cursor: pointer;
  font-family: var(--font-family);
  transition:
    box-shadow 0.15s ease,
    transform 0.15s ease;
}

.sidebar__toggle-icon {
  width: 22px;
  height: 22px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
  pointer-events: none;
  transition: transform 0.2s ease;
}

.sidebar--collapsed .sidebar__toggle-icon {
  transform: rotate(180deg);
}

.sidebar__toggle:hover {
  box-shadow: 2px 2px 0 var(--color-white);
  transform: translate(2px, 2px);
}

.sidebar__toggle:active {
  box-shadow: none;
  transform: translate(4px, 4px);
}

.sidebar__toggle:focus-visible {
  outline: 3px solid var(--color-white);
  outline-offset: 3px;
}
```

The collapsed padding produces `52px` of inner width (`72px - 10px - 10px`); with the collapsed header padding removed, the `44px` button plus its `4px` rightward shadow fits without changing the `72px` Sidebar width.

- [ ] **Step 5: Add reduced-motion behavior without hiding state**

Append this block after the existing `@media (max-width: 1024px)` block in `frontend/src/components/layout/Sidebar.css`:

```css
@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar__toggle,
  .sidebar__toggle-icon {
    transition: none;
  }

  .sidebar__toggle:hover,
  .sidebar__toggle:active {
    transform: none;
  }
}
```

Hover still uses the `2px` shadow and active still removes it, providing non-motion feedback. In reduced-motion mode, the SVG changes orientation instantly because its transition is disabled; Sidebar width/content, dynamic accessible label, `title`, and `aria-expanded` reinforce the state.

- [ ] **Step 6: Run the focused test and verify GREEN**

Run from `frontend/`:

```bash
npm test -- src/components/layout/Sidebar.test.jsx
```

Expected: all 3 tests in `Sidebar.test.jsx` pass, including the accessible-state, SVG, label, toggle, and persistence assertions.

- [ ] **Step 7: Run frontend regression checks**

Run from `frontend/`:

```bash
npm run lint
npm test
npm run build
```

Expected: ESLint exits with status 0, the complete Vitest suite passes, and Vite reports a successful production build.

- [ ] **Step 8: Inspect visual and interaction behavior**

Start the app from `frontend/`:

```bash
npm run dev -- --host 127.0.0.1
```

Expected: Vite serves the frontend at `http://127.0.0.1:5173/`. In an authenticated development session, verify all of the following in the browser or equivalent headless browser inspection:

1. Above `1024px`, the expanded control is `44px × 44px`, orange with black double-chevron, black `2px` border, card radius, and a crisp white `4px` shadow.
2. After clicking, the Sidebar remains exactly `72px`, the button and shadow stay inside it, and the chevron points right.
3. Clicking again restores the expanded state; reloading preserves the last manual preference.
4. Hover reduces the shadow and shifts the control; active visually presses it; keyboard Tab reveals the white focus outline.
5. At `1024px` and at `320px`, the existing collapse behavior remains intact and the control causes no horizontal overflow.
6. With `prefers-reduced-motion: reduce`, width, press, and icon transitions are absent; the icon still changes direction instantly, hover/active shadow changes remain visible, and the state remains available through Sidebar width/content, dynamic label/title, and `aria-expanded`.

Stop the development server after inspection.

- [ ] **Step 9: Inspect the scoped diff and commit**

Run from the repository root:

```bash
git diff --check -- \
  frontend/src/components/layout/Sidebar.jsx \
  frontend/src/components/layout/Sidebar.css \
  frontend/src/components/layout/Sidebar.test.jsx
git diff -- \
  frontend/src/components/layout/Sidebar.jsx \
  frontend/src/components/layout/Sidebar.css \
  frontend/src/components/layout/Sidebar.test.jsx
git add \
  frontend/src/components/layout/Sidebar.jsx \
  frontend/src/components/layout/Sidebar.css \
  frontend/src/components/layout/Sidebar.test.jsx
git diff --cached --check
git commit -m "feat(frontend): enrich sidebar toggle"
```

Expected: the first and fourth commands report no whitespace errors; the reviewed diff and resulting commit contain only the three Sidebar files, with no token, route, link, logout, or responsive-logic changes.
