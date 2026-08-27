## 1. Code-splitting do PDF

- [x] 1.1 `import()` dinâmico de `jsPDF`/`html2canvas` no handler de "Exportar PDF" (`HomePage.jsx`), em vez de import estático no topo do arquivo
- [x] 1.2 Validar via `npm run build` que os dois pacotes saem do chunk principal, viram chunk(s) separado(s) carregado(s) sob demanda

## 2. Consistência de CSS

- [x] 2.1 `LoginPage.css` novo — migra todo `style={{...}}` de `LoginPage.jsx` pra classes usando tokens (`var(--color-*)`, `var(--space-*)`, etc.)
- [x] 2.2 `HomePage.css` novo — mesma migração pra `HomePage.jsx`
- [x] 2.3 Conferir visualmente que nada mudou de aparência (é refactor, não redesign)

## 3. Error boundary

- [x] 3.1 Componente `ErrorBoundary` (class component, `componentDidCatch`/`getDerivedStateFromError`) em `frontend/src/components/`
- [x] 3.2 Envolver as rotas em `App.jsx` com o `ErrorBoundary`, tela de fallback simples
- [x] 3.3 Validar com teste automatizado forçando um erro de render

## 4. Responsividade tablet

- [x] 4.1 Breakpoint (~1024px) via `matchMedia` — sidebar colapsa automaticamente quando não há preferência manual salva em `localStorage`
- [x] 4.2 `max-width` no formulário de login e nos cards da Home pra não esticar em telas largas de tablet
- [x] 4.3 Validar manualmente em viewport de tablet (devtools ou dispositivo real) — sem quebra horizontal, sidebar e grid se comportando corretamente

## 5. Favicon

- [x] 5.1 Adicionar favicon PNG derivado do mascote do `README.md` e `<link rel="icon">` em `index.html`

## 6. Documentação

- [x] 6.1 Atualizar `PRD.md` (Sprint 4) marcando as tarefas concluídas
- [x] 6.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 4]`

## 7. Fundação mínima de testes frontend

- [x] 7.1 Configurar Vitest + React Testing Library + jsdom, com setup compartilhado e scripts `test`/`test:watch`
- [x] 7.2 Testar que o `ErrorBoundary` troca uma exceção de renderização pela tela de fallback
- [x] 7.3 Testar o auto-colapso da sidebar em viewport de tablet sem preferência salva e a precedência da preferência manual persistida em `localStorage`
- [x] 7.4 Testar que a exportação PDF carrega e executa o módulo somente após o clique do usuário
- [x] 7.5 Rodar a suíte completa junto de lint e build; confirmar o code-splitting nos artefatos de produção
