# Home Study CTA Styling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Amendment — 2026-09-14:** A pedido do usuário, o botão secundário usa um olho aberto decorativo inline no lugar da seta diagonal. Esta decisão substitui todas as referências e exemplos anteriores à seta diagonal; o play da CTA primária continua sendo um pseudo-elemento CSS.

**Goal:** Apply the approved “Contraste expressivo” visual hierarchy to the Home study CTAs while preserving their existing destinations and rendering rules.

**Architecture:** Keep the global `Button` component unchanged and scope every visual rule to the two Home-specific classes. Change only the primary CTA copy in JSX, use empty CSS pseudo-elements for decorative symbols, and preserve all existing data loading, conditional rendering, error handling, and navigation.

**Tech Stack:** React 18.3, React Router 7.18, CSS custom properties, Vitest 4.1, Testing Library, ESLint 9, Vite 6.

## Global Constraints

- Use the approved “B — Contraste expressivo” direction.
- The primary action must be labeled `Continuar estudando` and keep the destination `/decks/{deckId}/estudar`.
- The secondary action must remain labeled `Ver meus decks` and keep the destination `/decks`.
- Preserve the current conditional copy beside `Ver meus decks` without edits.
- Preserve loading, empty, inaccessible-deck, and error branches exactly as they behave today.
- Do not modify the global `Button` component, global button variants, tokens, sidebar, cards, chart, or deck-list CTAs.
- Use only existing design tokens: `--color-accent`, `--color-text-primary`, `--color-white`, `--radius-card`, and existing spacing tokens.
- Use empty CSS pseudo-elements for the play and diagonal-arrow decorations so accessible link names remain text-only.
- Primary visual: orange background, black text, `var(--radius-card)`, full width, solid black offset shadow.
- Secondary visual: black background, white text, `var(--radius-card)`, smaller intrinsic width on desktop, solid orange offset shadow.
- Both controls need distinct `:hover`, `:active`, and `:focus-visible` states.
- At viewport widths up to `640px`, the secondary CTA block must stack and `Ver meus decks` must occupy full width without horizontal overflow at 320 px.
- Under `prefers-reduced-motion: reduce`, remove transitions and transforms while preserving each control's resting shadow.
- The existing uncommitted `HomePage.jsx`/`HomePage.css` changes are in-scope preliminary CTA work; preserve and incorporate them rather than reverting them.

---

## File Structure

- `frontend/src/pages/HomePage.test.jsx`: define the accessible label and unchanged navigation contract before production edits.
- `frontend/src/pages/HomePage.jsx`: change only the Home primary CTA copy; retain current component props and conditional placement.
- `frontend/src/pages/HomePage.css`: implement both local visual variants, interaction states, reduced motion, and the 640 px layout.
- `openspec/changes/sprint-9-tela-de-estudo/specs/study-entry-points/spec.md`: update only the Home-specific accessible label.
- `openspec/changes/sprint-9-tela-de-estudo/design.md`, `proposal.md`, `tasks.md`, `PRD.md`, `CHANGELOG.md`: align the Sprint 9 record with the approved Home label and styling.

---

### Task 1: Implement the expressive Home CTA hierarchy

**Files:**
- Modify: `frontend/src/pages/HomePage.test.jsx:90-146`
- Modify: `frontend/src/pages/HomePage.jsx:121-159`
- Modify: `frontend/src/pages/HomePage.css:26-70`

**Interfaces:**
- Consumes: `Button` with `as={Link}`, `to`, `variant`, and `className`; existing `hasValidLastDeck` conditional state.
- Produces: accessible link `Continuar estudando` at `/decks/{lastDeck.id}/estudar` when a valid last deck exists, plus the unchanged `Ver meus decks` link at `/decks`.

- [ ] **Step 1: Update the Home behavior tests before production code**

Replace the `describe("caminhos até a tela de estudo", ...)` block in `frontend/src/pages/HomePage.test.jsx` with:

```jsx
describe("caminhos até a tela de estudo", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("com último deck válido: botão 'Continuar estudando' aponta pro deck, e o CTA convida a trocar de deck", async () => {
    fetchReviews.mockResolvedValue({
      results: [
        { id: "review-1", deck_id: "deck-last", rating: "again", reviewed_at: "2026-08-31T12:00:00Z" },
      ],
    });
    fetchDeck.mockResolvedValue(LAST_DECK);
    fetchDeckStatistics.mockResolvedValue({ rating_distribution: {} });

    renderHome();

    await screen.findByText("Hospedagem e Transporte");

    expect(screen.getByRole("link", { name: "Continuar estudando" })).toHaveAttribute(
      "href",
      "/decks/deck-last/estudar",
    );
    expect(
      screen.getByText("Não é o deck que deseja estudar agora? Escolha o seu deck!"),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver meus decks" })).toHaveAttribute("href", "/decks");
  });

  test("sem nenhuma revisão: sem botão 'Continuar estudando', CTA convida a escolher um deck", async () => {
    fetchReviews.mockResolvedValue({ results: [] });

    renderHome();

    await screen.findByText("Você ainda não revisou nenhum card.");

    expect(screen.queryByRole("link", { name: "Continuar estudando" })).not.toBeInTheDocument();
    expect(screen.getByText("Escolha um deck pra começar a estudar!")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver meus decks" })).toHaveAttribute("href", "/decks");
  });

  test("deck da revisão mais recente não está mais acessível: sem botão 'Continuar estudando', CTA neutro", async () => {
    fetchReviews.mockResolvedValue({
      results: [
        { id: "review-1", deck_id: "deck-deleted", rating: "again", reviewed_at: "2026-08-31T12:00:00Z" },
      ],
    });
    fetchDeck.mockRejectedValue({ status: 404, message: "Not found" });

    renderHome();

    await waitFor(() => expect(fetchDeck).toHaveBeenCalledWith("deck-deleted"));
    await waitFor(() =>
      expect(screen.queryByRole("link", { name: "Continuar estudando" })).not.toBeInTheDocument(),
    );
    expect(screen.getByText("Escolha um deck pra começar a estudar!")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run from `frontend/`:

```bash
npm test -- HomePage.test.jsx
```

Expected: the valid-deck scenario fails because the rendered link is still named `Estudar`, proving the new accessible-label contract is not implemented yet.

- [ ] **Step 3: Change only the primary Home CTA copy**

In `frontend/src/pages/HomePage.jsx`, retain all current props and replace the button content:

```jsx
<Button
  as={Link}
  variant="primary"
  to={`/decks/${lastDeck.id}/estudar`}
  className="home-page__deck-study-button"
>
  Continuar estudando
</Button>
```

Do not change the `Ver meus decks` JSX or either conditional branch.

- [ ] **Step 4: Implement the approved local CSS variants and interaction states**

Replace the current `.home-page__deck-study-button` and `.home-page__decks-cta-button` rules in `frontend/src/pages/HomePage.css`, and add the shared state rules immediately after them:

```css
.home-page__deck-study-button,
.home-page__decks-cta-button {
  gap: var(--space-xs);
  min-height: 44px;
  border-radius: var(--radius-card);
  opacity: 1;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    opacity 0.2s ease;
}

.home-page__deck-study-button {
  width: 100%;
  margin-top: var(--space-sm);
  background: var(--color-accent);
  color: var(--color-text-primary);
  box-shadow: 4px 4px 0 var(--color-text-primary);
}

.home-page__deck-study-button::before {
  content: "";
  width: 0;
  height: 0;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  border-left: 7px solid currentColor;
}

.home-page__decks-cta-button {
  background: var(--color-text-primary);
  color: var(--color-white);
  box-shadow: 3px 3px 0 var(--color-accent);
}

.home-page__decks-cta-button::after {
  content: "";
  width: 7px;
  height: 7px;
  border-top: 2px solid currentColor;
  border-right: 2px solid currentColor;
}

.home-page__deck-study-button:hover,
.home-page__decks-cta-button:hover {
  opacity: 1;
  transform: translate(2px, 2px);
}

.home-page__deck-study-button:hover {
  box-shadow: 2px 2px 0 var(--color-text-primary);
}

.home-page__decks-cta-button:hover {
  box-shadow: 1px 1px 0 var(--color-accent);
}

.home-page__deck-study-button:active,
.home-page__decks-cta-button:active {
  box-shadow: none;
  transform: translate(4px, 4px);
}

.home-page__deck-study-button:focus-visible {
  outline: 3px solid var(--color-text-primary);
  outline-offset: 3px;
}

.home-page__decks-cta-button:focus-visible {
  outline: 3px solid var(--color-accent);
  outline-offset: 3px;
}
```

Remove the old comment about merely darkening the secondary variant; the new selectors document themselves through the approved visual hierarchy.

- [ ] **Step 5: Add mobile and reduced-motion behavior**

Append these blocks after the existing `@media (max-width: 1024px)` block in `frontend/src/pages/HomePage.css`:

```css
@media (max-width: 640px) {
  .home-page__study-cta {
    align-items: stretch;
    flex-direction: column;
  }

  .home-page__decks-cta-button {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .home-page__deck-study-button,
  .home-page__decks-cta-button {
    transition: none;
  }

  .home-page__deck-study-button:hover,
  .home-page__deck-study-button:active,
  .home-page__decks-cta-button:hover,
  .home-page__decks-cta-button:active {
    transform: none;
  }

  .home-page__deck-study-button:hover,
  .home-page__deck-study-button:active {
    box-shadow: 4px 4px 0 var(--color-text-primary);
  }

  .home-page__decks-cta-button:hover,
  .home-page__decks-cta-button:active {
    box-shadow: 3px 3px 0 var(--color-accent);
  }
}
```

- [ ] **Step 6: Run focused tests and verify GREEN**

Run from `frontend/`:

```bash
npm test -- HomePage.test.jsx
```

Expected: all tests in `HomePage.test.jsx` pass, including all three entry-point scenarios.

- [ ] **Step 7: Run frontend regression checks**

Run from `frontend/`:

```bash
npm run lint
npm test
npm run build
```

Expected: ESLint exits 0, all Vitest tests pass, and Vite produces a successful production build.

- [ ] **Step 8: Inspect the scoped diff and commit**

Run from the repository root:

```bash
git diff --check -- frontend/src/pages/HomePage.jsx frontend/src/pages/HomePage.css frontend/src/pages/HomePage.test.jsx
git diff -- frontend/src/components/ui/Button.jsx frontend/src/components/ui/Button.css frontend/src/tokens frontend/src/components/layout frontend/src/pages/DeckListPage.jsx
git add frontend/src/pages/HomePage.jsx frontend/src/pages/HomePage.css frontend/src/pages/HomePage.test.jsx
git diff --cached --check
git commit -m "feat(frontend): style home study actions"
```

Expected: the first command reports no whitespace errors; the second command is empty; the commit contains only the three Home files. The in-scope preliminary Home changes are incorporated in this commit.

---

### Task 2: Align the Sprint 9 study-entry documentation

**Files:**
- Modify: `openspec/changes/sprint-9-tela-de-estudo/specs/study-entry-points/spec.md:3-17`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/design.md:56`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/proposal.md:13,33`
- Modify: `openspec/changes/sprint-9-tela-de-estudo/tasks.md:40,44`
- Modify: `PRD.md:251`
- Modify: `CHANGELOG.md:21`

**Interfaces:**
- Consumes: the `Continuar estudando` accessible label implemented and verified in Task 1.
- Produces: canonical Sprint 9 documentation that reserves `Continuar estudando` for the Home's recent-deck CTA while leaving `Estudar` unchanged on deck detail and deck list.

- [ ] **Step 1: Update the normative Home requirement**

In `openspec/changes/sprint-9-tela-de-estudo/specs/study-entry-points/spec.md`, replace only the four Home-specific occurrences of the button name `Estudar` with `Continuar estudando`:

```markdown
### Requirement: Home oferece um caminho direto pro último deck estudado
O sistema SHALL exibir, dentro do card "Último deck estudado" da Home, um botão "Continuar estudando" que navega pra `/decks/{deckId}/estudar` do deck mais recentemente estudado, apenas quando esse deck existe e está acessível.

#### Scenario: Usuário com histórico de estudo vê o botão
- **WHEN** um usuário autenticado com pelo menos uma revisão registrada acessa a Home, e o deck da revisão mais recente ainda existe e pertence a ele
- **THEN** o card "Último deck estudado" mostra um botão "Continuar estudando" que navega pra `/decks/{deckId}/estudar` daquele deck

#### Scenario: Usuário sem nenhuma revisão não vê o botão
- **WHEN** um usuário autenticado sem nenhuma revisão registrada acessa a Home
- **THEN** o card "Último deck estudado" não mostra o botão "Continuar estudando" (mantém a mensagem de estado vazio já existente)

#### Scenario: Deck da revisão mais recente não está mais acessível
- **WHEN** o deck da revisão mais recente do usuário foi soft-deletado ou não pode ser carregado
- **THEN** o card "Último deck estudado" não mostra o botão "Continuar estudando"
```

Do not change the `Estudar` label in the deck-list or sidebar requirements later in the same file.

- [ ] **Step 2: Align descriptive Sprint 9 records**

Make these exact terminology changes:

```markdown
# openspec/changes/sprint-9-tela-de-estudo/design.md — D6 Home paragraph
Card "Último deck estudado" (Home): o botão "Continuar estudando" só é renderizado dentro do bloco que já existe pra `lastDeck` presente — herda de graça a proteção contra usuário novo (zero reviews) e deck soft-deletado (`fetchDeck` de um deck excluído já cai no branch de erro existente). O CTA secundário abaixo do card **sempre aparece**, com dois textos possíveis: "Não é o deck que deseja estudar agora? Escolha o seu deck!" quando há `lastDeck`, "Escolha um deck pra começar a estudar!" quando não há — nos dois casos leva pra `/decks`. Os dois CTAs usam a direção visual “Contraste expressivo”: ação primária laranja com sombra preta e ação secundária preta com sombra laranja.

# openspec/changes/sprint-9-tela-de-estudo/proposal.md — What Changes
- Caminho de descoberta até a tela de estudo, que ficou faltando na entrega original: botão "Continuar estudando" no card "Último deck estudado" da Home, CTA secundário "Ver meus decks" levando pra `/decks`, e botão "Estudar" em cada item de `DeckListPage` — sem alterar o menu lateral. Os CTAs da Home usam a direção visual “Contraste expressivo”.

# openspec/changes/sprint-9-tela-de-estudo/proposal.md — Impact
- Frontend: `HomePage.jsx` (botão "Continuar estudando" no card "Último deck estudado" + CTA secundário condicional "Ver meus decks"), `HomePage.css` (hierarquia “Contraste expressivo”), `DeckListPage.jsx` (botão "Estudar" por item, ao lado de "Abrir deck"). `Sidebar.jsx` **não muda** — decisão explícita via `backend-mentor` (ver D6 em `design.md`), pra evitar dois itens de menu com o mesmo destino (`/decks`).

# openspec/changes/sprint-9-tela-de-estudo/tasks.md
- [x] 7.1 `HomePage.jsx`: botão "Continuar estudando" dentro do bloco já existente de `lastDeck` (card "Último deck estudado"), navegando pra `/decks/{deckId}/estudar`
- [x] 7.5 Testes automatizados (frontend): botão "Continuar estudando" da Home aparece só com `lastDeck` válido, CTA secundário troca de texto conforme o estado, botão "Estudar" presente em cada item de `DeckListPage`
- [x] 7.7 `HomePage.css`: estilizar "Continuar estudando" e "Ver meus decks" na direção “Contraste expressivo”, com estados hover/active/focus, layout móvel e redução de movimento
```

- [ ] **Step 3: Align PRD and changelog wording**

In `PRD.md` Sprint 9 item 9.9, preserve the full item and replace its Home description with:

```markdown
botão "Continuar estudando" no card "Último deck estudado" da Home (só com deck válido), estilizado como ação primária laranja com sombra preta; CTA secundário "Ver meus decks" sempre visível na Home levando pra `/decks`, com fundo preto, sombra laranja e texto condicional
```

In the Sprint 9 “Caminhos de descoberta” entry in `CHANGELOG.md`, preserve its full explanation and replace the Home button sentence with:

```markdown
`HomePage.jsx` ganha um botão "Continuar estudando" dentro do card "Último deck estudado" (só quando há um deck válido) e um CTA secundário "Ver meus decks" sempre visível levando pra `/decks`; ambos recebem a direção visual “Contraste expressivo”, com hierarquia, estados de interação, responsividade e redução de movimento
```

- [ ] **Step 4: Verify terminology and scope**

Run from the repository root:

```bash
rg -n 'Home.*botão "Estudar"|botão "Estudar".*Home|card "Último deck estudado".*botão "Estudar"' \
  PRD.md CHANGELOG.md \
  openspec/changes/sprint-9-tela-de-estudo
rg -n 'DeckListPage.*"Continuar estudando"|listagem.*"Continuar estudando"' \
  PRD.md CHANGELOG.md \
  openspec/changes/sprint-9-tela-de-estudo
git diff --check
```

Expected: both `rg` commands have no matches; `git diff --check` reports no whitespace errors.

- [ ] **Step 5: Commit documentation separately**

```bash
git add PRD.md CHANGELOG.md \
  openspec/changes/sprint-9-tela-de-estudo/design.md \
  openspec/changes/sprint-9-tela-de-estudo/proposal.md \
  openspec/changes/sprint-9-tela-de-estudo/tasks.md \
  openspec/changes/sprint-9-tela-de-estudo/specs/study-entry-points/spec.md
git diff --cached --check
git commit -m "docs: record home study action styling"
```

Expected: the commit contains only the six listed Sprint 9 documentation files.
