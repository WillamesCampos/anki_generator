# Sprint 4 Frontend Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Robustecer a SPA React com carregamento sob demanda do PDF, CSS consistente, fallback global de erro, layout tablet responsivo, favicon e uma fundação mínima de testes automatizados.

**Architecture:** Manter os limites atuais da SPA: páginas concentram composição, componentes de layout mantêm navegação e utilitários em `lib/` encapsulam efeitos não visuais. Vitest roda em jsdom com React Testing Library; cada comportamento novo entra por RED-GREEN-REFACTOR. CSS continua consumindo exclusivamente os tokens já auditados.

**Tech Stack:** React 18, Vite 6, React Router 7, Chart.js, jsPDF, Vitest 4, jsdom, React Testing Library e CSS dedicado por componente/página.

## Global Constraints

- Não alterar backend ou contratos da API.
- Não implementar navegação mobile; o breakpoint único é `1024px`.
- Não introduzir cores, tipografia, espaçamento ou componentes fora de `design_system/design-system.html` e `frontend/src/tokens/`.
- Manter a preferência manual da sidebar como autoridade quando existir em `localStorage`.
- Layout responsivo exige inspeção manual; jsdom não valida geometria real.
- Cobertura abrangente, thresholds e GitHub Actions permanecem na Sprint 8.

---

### Task 1: Fundação de testes e Error Boundary

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/vite.config.js`
- Create: `frontend/src/test/setup.js`
- Create: `frontend/src/components/ErrorBoundary.test.jsx`
- Create: `frontend/src/components/ErrorBoundary.jsx`
- Create: `frontend/src/components/ErrorBoundary.css`
- Modify: `frontend/src/App.jsx`

**Interfaces:**
- Produces: `ErrorBoundary({ children })`, ambiente Vitest/jsdom e scripts `npm test`/`npm run test:watch`.

- [ ] **Step 1: Instalar a infraestrutura mínima**

Run: `cd frontend && npm install --save-dev vite@^6.4.3 vitest@^4.1.11 jsdom@^25.0.1 @testing-library/react@^16.3.0 @testing-library/jest-dom@^6.9.1 @testing-library/user-event@^14.6.1`

Adicionar ao Vite `test: { environment: "jsdom", setupFiles: "./src/test/setup.js" }`; no setup importar `@testing-library/jest-dom/vitest` e registrar `cleanup` em `afterEach`. Adicionar scripts `"test": "vitest run"` e `"test:watch": "vitest"`.

- [ ] **Step 2: Escrever o teste RED do fallback**

```jsx
function BrokenChild() {
  throw new Error("falha de renderização");
}

render(
  <ErrorBoundary>
    <BrokenChild />
  </ErrorBoundary>,
);

expect(screen.getByRole("alert")).toHaveTextContent("Não foi possível carregar a aplicação");
```

Run: `cd frontend && npm test -- src/components/ErrorBoundary.test.jsx`
Expected: FAIL porque `ErrorBoundary.jsx` ainda não existe.

- [ ] **Step 3: Implementar o mínimo e integrar no App**

Criar class component com `getDerivedStateFromError`, `componentDidCatch` e fallback `role="alert"`; usar apenas tokens no CSS. Em `App.jsx`, envolver `AppRoutes` com `<ErrorBoundary>` dentro de `AuthProvider`.

- [ ] **Step 4: Verificar GREEN e regressões**

Run: `cd frontend && npm test -- src/components/ErrorBoundary.test.jsx`
Expected: PASS, 1 teste.

Run: `cd frontend && npm run lint`
Expected: exit 0.

### Task 2: Sidebar responsiva com preferência manual

**Files:**
- Create: `frontend/src/components/layout/Sidebar.test.jsx`
- Modify: `frontend/src/components/layout/Sidebar.jsx`
- Modify: `frontend/src/components/layout/Sidebar.css`
- Modify: `frontend/src/components/layout/AppShell.css`

**Interfaces:**
- Consumes: chave `anki_generator_sidebar_collapsed` já existente.
- Produces: `TABLET_MEDIA_QUERY = "(max-width: 1024px)"` e estado colapsado que reage ao viewport apenas sem preferência manual.

- [ ] **Step 1: Escrever RED para auto-colapso em tablet**

Renderizar `Sidebar` sob `MemoryRouter` + `AuthProvider`, com `window.matchMedia` retornando `matches: true` e `localStorage` vazio. Verificar `.sidebar` com classe `sidebar--collapsed`.

Run: `cd frontend && npm test -- src/components/layout/Sidebar.test.jsx`
Expected: FAIL, sidebar atual ignora `matchMedia`.

- [ ] **Step 2: Implementar inicialização e listener mínimos**

Inicializar pelo valor persistido quando existir; caso contrário usar `window.matchMedia(TABLET_MEDIA_QUERY).matches`. Registrar `change` listener que atualiza o estado somente enquanto a chave não existir. O toggle manual salva a chave e passa a prevalecer.

- [ ] **Step 3: Verificar GREEN**

Run: `cd frontend && npm test -- src/components/layout/Sidebar.test.jsx`
Expected: PASS para auto-colapso.

- [ ] **Step 4: Registrar o comportamento preservado da preferência manual**

Salvar `anki_generator_sidebar_collapsed=false`, simular tablet e verificar que a sidebar permanece expandida; depois clicar no toggle e verificar persistência do novo valor.

Run: `cd frontend && npm test -- src/components/layout/Sidebar.test.jsx`
Expected: PASS; é um teste de caracterização de um comportamento já existente que precisa permanecer válido depois do auto-colapso.

- [ ] **Step 5: Finalizar comportamento e CSS tablet**

Preservar a preferência manual e adicionar `@media (max-width: 1024px)` apenas para ajustes estruturais. Em `AppShell.css`, aplicar `min-width: 0`, largura fluida e padding baseado em tokens para impedir overflow.

- [ ] **Step 6: Verificar GREEN**

Run: `cd frontend && npm test -- src/components/layout/Sidebar.test.jsx`
Expected: todos os testes da sidebar PASS.

### Task 3: Exportação PDF sob demanda

**Files:**
- Create: `frontend/src/lib/exportPdf.test.js`
- Create: `frontend/src/lib/exportPdf.js`
- Modify: `frontend/src/pages/HomePage.jsx`

**Interfaces:**
- Produces: `exportChartToPdf(chart): Promise<boolean>`; retorna `false` sem chart e `true` depois de salvar o PDF.

- [ ] **Step 1: Escrever RED para o carregamento sob demanda**

Mockar `jspdf`, importar apenas `exportChartToPdf`, confirmar que o construtor ainda não foi chamado; chamar com chart fake (`toBase64Image`) e verificar construtor, `text`, `addImage` e `save`.

Run: `cd frontend && npm test -- src/lib/exportPdf.test.js`
Expected: FAIL porque `exportPdf.js` ainda não existe.

- [ ] **Step 2: Implementar utilitário com import dinâmico**

```js
export async function exportChartToPdf(chart) {
  if (!chart) return false;
  const [{ default: jsPDF }] = await Promise.all([import("jspdf")]);
  const pdf = new jsPDF({ orientation: "landscape" });
  pdf.text("Estatísticas de estudo", 14, 15);
  pdf.addImage(chart.toBase64Image(), "PNG", 14, 25, 260, 120);
  pdf.save("estatisticas-anki-generator.pdf");
  return true;
}
```

O handler da Home apenas chama `await exportChartToPdf(chartRef.current)`; remover o import estático de `jspdf`.

- [ ] **Step 3: Verificar GREEN**

Run: `cd frontend && npm test -- src/lib/exportPdf.test.js`
Expected: PASS e nenhuma instanciação antes da chamada.

### Task 4: CSS dedicado e responsividade das páginas

**Files:**
- Create: `frontend/src/pages/HomePage.css`
- Modify: `frontend/src/pages/HomePage.jsx`
- Create: `frontend/src/pages/LoginPage.css`
- Modify: `frontend/src/pages/LoginPage.jsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: tokens CSS de `frontend/src/tokens/tokens.css`.
- Produces: páginas sem atributo `style`, largura máxima consistente e grid sem overflow horizontal.

- [ ] **Step 1: Criar classes equivalentes aos estilos existentes**

Home: `home-page`, `home-page__summary-grid`, `home-page__deck-title`, `home-page__deck-description`, `home-page__statistics`, `home-page__chart`, `home-page__actions`. Login: `login-page`, `login-page__form`, `login-page__divider`, `login-page__error`, `login-page__google-message`. Usar somente `var(--*)`.

- [ ] **Step 2: Migrar JSX e remover imports JS de estilo não usados**

Remover todos os `style={{...}}`, importar os CSS dedicados e manter `colors.accent` apenas na configuração Chart.js.

- [ ] **Step 3: Auditar consistência automaticamente**

Run: `cd frontend && ! rg 'style=\{\{' src/pages src/components`
Expected: exit 0.

Run: `cd frontend && ! rg 'rgb\(|#[0-9a-fA-F]{3,8}' src --glob '*.css' --glob '*.jsx' --glob '!tokens/**'`
Expected: exit 0.

Run: `cd frontend && npm run lint && npm test`
Expected: exit 0 em ambos.

### Task 5: Favicon e documentação

**Files:**
- Create: `frontend/public/favicon.png`
- Modify: `frontend/index.html`
- Modify: `frontend/README.md`
- Modify: `README.md`
- Modify: `PRD.md`
- Modify: `CHANGELOG.md`
- Modify: `openspec/changes/sprint-4-robustecimento-frontend/tasks.md`
- Modify: `frontend/src/tokens/VISUAL_AUDIT.md`

**Interfaces:**
- Produces: favicon PNG 192×192 derivado do mascote do README e documentação da Sprint 4 concluída.

- [ ] **Step 1: Adicionar favicon alinhado à identidade do projeto**

Derivar um close simplificado do mascote exibido no `README.md`, otimizar para PNG 192×192 e referenciar com `<link rel="icon" type="image/png" sizes="192x192" href="/favicon.png">`.

- [ ] **Step 2: Atualizar documentação**

Marcar 4.1–4.7 no PRD; registrar Sprint 4 no changelog; atualizar READMEs com scripts de teste, responsividade e roadmap; atualizar auditoria visual e checklist OpenSpec.

- [ ] **Step 3: Verificação final completa**

Run: `cd frontend && npm test`
Expected: todos os testes PASS.

Run: `cd frontend && npm run lint`
Expected: exit 0.

Run: `cd frontend && npm run build`
Expected: exit 0; `jspdf`/dependências aparecem em chunk separado do `index-*`.

Run: `git diff --check`
Expected: exit 0.

Run: `rg -n 'jspdf' frontend/dist/assets/index-*.js`
Expected: nenhuma correspondência de implementação eager no chunk principal.
