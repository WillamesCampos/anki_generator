# Sidebar Lucide Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Use Lucide icons throughout the Sidebar, with icon-plus-label expanded items and icon-only collapsed items that reveal accessible visual tooltips.

**Architecture:** Install `lucide-react`, add icon component references to `NAV_ITEMS`, and keep all rendering in `Sidebar`. CSS hides labels only in the collapsed state and reveals local tooltip spans on hover/focus without changing routes, persistence, or layout state.

**Tech Stack:** React 18, React Router, lucide-react, Vitest, Testing Library, CSS.

## Global Constraints

- Use only named imports from `lucide-react`.
- Preserve all routes, labels, order, logout, localStorage key, breakpoint, widths, ARIA state, and toggle behavior.
- Expanded items show icon plus label; collapsed items show only icon.
- Collapsed hover and focus show an orange/black tooltip with the complete label.
- Icons are decorative; collapsed controls retain complete accessible names.
- Toggle stays 44×44, orange, black-bordered, and without box-shadow.
- No wildcard icon import, copied SVG, global icon component, or second icon library.

---

### Task 1: Install Lucide and convert the Sidebar navigation

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/src/components/layout/Sidebar.test.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Modify: `frontend/src/components/layout/Sidebar.css`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/design.md`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/tasks.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: existing `collapsed`, `NAV_ITEMS`, `NavLink`, and toggle semantics.
- Produces: Lucide SVG components, `.sidebar__link-label`, `.sidebar__tooltip`, and complete collapsed `aria-label` values.

- [x] **Step 1: Write failing icon and collapsed-label tests**

Extend `Sidebar.test.jsx` with:

```jsx
const NAV_LABELS = ["Home", "Decks", "Categorias", "Relatórios", "Chat com IA"];

test("mostra ícone e nome em todos os itens quando o menu está aberto", () => {
  localStorage.setItem("anki_generator_sidebar_collapsed", "false");
  installMatchMedia(false);
  renderSidebar();

  NAV_LABELS.forEach((label) => {
    const link = screen.getByRole("link", { name: label });
    expect(link.querySelector(".sidebar__item-icon")).toHaveAttribute("aria-hidden", "true");
    expect(link.querySelector(".sidebar__link-label")).toHaveTextContent(label);
  });

  const logoutButton = screen.getByRole("button", { name: "Sair" });
  expect(logoutButton.querySelector(".sidebar__item-icon")).toHaveAttribute("aria-hidden", "true");
});

test("mantém nomes completos e tooltips no menu recolhido", () => {
  localStorage.setItem("anki_generator_sidebar_collapsed", "true");
  installMatchMedia(false);
  renderSidebar();

  NAV_LABELS.forEach((label) => {
    const link = screen.getByRole("link", { name: label });
    expect(link).toHaveAttribute("aria-label", label);
    expect(link.querySelector(".sidebar__item-icon")).toBeInTheDocument();
    expect(link.querySelector(".sidebar__tooltip")).toHaveTextContent(label);
    expect(link.querySelector(".sidebar__tooltip")).toHaveAttribute("aria-hidden", "true");
  });

  expect(screen.getByRole("button", { name: "Sair" })).toHaveAttribute("aria-label", "Sair");
});
```

In the existing toggle test, assert the initial icon has class `lucide-chevrons-left` and the post-click icon has class `lucide-chevrons-right`.

- [x] **Step 2: Run RED**

Run `cd frontend && npm test -- src/components/layout/Sidebar.test.jsx`.

Expected: failures for missing item icons, label spans, tooltip spans, complete collapsed accessible names, and Lucide toggle classes.

- [x] **Step 3: Install and validate Lucide exports**

Run:

```bash
cd frontend
npm install lucide-react
node --input-type=module -e 'import { House, Layers3, Tags, ChartColumn, Bot, LogOut, ChevronsLeft, ChevronsRight } from "lucide-react"; console.log([House, Layers3, Tags, ChartColumn, Bot, LogOut, ChevronsLeft, ChevronsRight].every(Boolean))'
```

Expected: npm updates only the frontend manifests and Node prints `true`.

- [x] **Step 4: Render named icons, labels, and tooltips**

Add the named imports to `Sidebar.jsx`. Change `NAV_ITEMS` to:

```jsx
const NAV_ITEMS = [
  { to: "/", label: "Home", icon: House, end: true },
  { to: "/decks", label: "Decks", icon: Layers3 },
  { to: "/categorias", label: "Categorias", icon: Tags },
  { to: "/relatorios", label: "Relatórios", icon: ChartColumn },
  { to: "/chat-ia", label: "Chat com IA", icon: Bot },
];
```

Inside the component, add:

```jsx
const ToggleIcon = collapsed ? ChevronsRight : ChevronsLeft;
```

Replace the manual toggle SVG with:

```jsx
<ToggleIcon
  className="sidebar__toggle-icon"
  size={22}
  strokeWidth={2.5}
  aria-hidden="true"
  focusable="false"
/>
```

Render each item with `const Icon = item.icon`, remove the native `title`, add `aria-label={collapsed ? item.label : undefined}`, and use:

```jsx
<Icon className="sidebar__item-icon" size={20} strokeWidth={2} aria-hidden="true" focusable="false" />
<span className="sidebar__link-label">{item.label}</span>
<span className="sidebar__tooltip" aria-hidden="true">{item.label}</span>
```

Render logout with the same three children using `LogOut`, `Sair`, and `aria-label={collapsed ? "Sair" : undefined}`. Preserve `handleLogout` unchanged.

- [x] **Step 5: Implement expanded alignment and collapsed tooltips**

Change `.sidebar__link` to flex alignment with `position: relative`, `gap: var(--space-xs)`, and `overflow: visible`. Add:

```css
.sidebar__item-icon {
  flex: 0 0 auto;
}

.sidebar__link-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar__tooltip {
  display: none;
}

.sidebar--collapsed .sidebar__link {
  align-items: center;
  justify-content: center;
  position: relative;
  text-align: center;
  overflow: visible;
}

.sidebar--collapsed .sidebar__link-label {
  display: none;
}

.sidebar--collapsed .sidebar__tooltip {
  position: absolute;
  top: 50%;
  left: calc(100% + var(--space-xs));
  z-index: 20;
  display: block;
  width: max-content;
  max-width: 180px;
  padding: 6px var(--space-xs);
  color: var(--color-text-primary);
  background: var(--color-accent);
  border: 2px solid var(--color-text-primary);
  border-radius: var(--radius-card);
  font-size: var(--font-size-sm);
  font-weight: 700;
  line-height: 1.2;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translate(6px, -50%);
  transition: opacity 0.15s ease, transform 0.15s ease, visibility 0.15s ease;
}

.sidebar--collapsed .sidebar__link:hover .sidebar__tooltip,
.sidebar--collapsed .sidebar__link:focus-visible .sidebar__tooltip {
  opacity: 1;
  visibility: visible;
  transform: translate(0, -50%);
}

.sidebar__link:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```

Remove the now-obsolete SVG stroke rules and collapsed rotation. In reduced motion, include `.sidebar__tooltip` in `transition: none` and force its visible transform to `translate(0, -50%)`.

- [x] **Step 6: Run GREEN and full checks**

Run focused tests, ESLint, full Vitest, Vite build, and `git diff --check`. Expected: all exit 0 and the new Sidebar tests pass.

- [x] **Step 7: Update Sprint records and commit**

Append task 7.10, add a design decision for Lucide/icons/tooltips, and add a concise CHANGELOG entry. Commit only the eight listed files:

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/components/layout/Sidebar.test.jsx frontend/src/components/layout/Sidebar.jsx frontend/src/components/layout/Sidebar.css openspec/changes/sprint-9-tela-de-estudo/design.md openspec/changes/sprint-9-tela-de-estudo/tasks.md CHANGELOG.md
git commit -m "feat(frontend): add Lucide navigation icons"
```

## Plan self-review

- Covers dependency, exact exports, icon mapping, open/collapsed states, tooltips, ARIA, toggle, reduced motion, tests, docs, and isolated commit.
- Does not change navigation behavior or introduce a global abstraction.
- Contains no deferred implementation placeholders.
