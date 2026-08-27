## Why

Auditoria via `backend-mentor` (grep direto no código, não suposição) encontrou pontas reais da Sprint 3 nunca fechadas: zero responsividade (nenhuma `@media` query em todo o CSS, apesar de ser `<regra_obrigatoria>` em `PROMPT_REFINADO.md`), nenhum error boundary (uma exceção JS derruba a tela pra branco sem recuperação), `LoginPage.jsx`/`HomePage.jsx` usando inline `style` enquanto os outros 6 componentes usam CSS dedicado com tokens, bundle sem code-splitting (`jsPDF`+`html2canvas` no chunk principal mesmo sem uso), e `index.html` sem nenhum `<link rel="icon">`. Inserida antes das Sprints 5/6/7 (que adicionam bastante UI nova) de propósito — construir mais telas sobre um frontend inconsistente só reproduziria o mesmo problema em vez de corrigi-lo.

## What Changes

- Code-splitting: `import()` dinâmico de `jsPDF`+`html2canvas`, carregados só ao clicar "Exportar PDF".
- `LoginPage.jsx`/`HomePage.jsx` migrados de inline `style` pra CSS dedicado com tokens, no mesmo padrão dos demais componentes.
- Error boundary global em `App.jsx`, com tela de fallback simples em vez de branco.
- Responsividade: breakpoint tablet (~1024px) — sidebar colapsa automaticamente (reaproveita o toggle já existente da Sprint 3), grid da Home e formulários com `max-width`, sem quebra horizontal. Mobile de verdade (nav diferente) fica fora de escopo por decisão explícita — projeto pessoal, sem uso mobile previsto no curto prazo.
- Favicon derivado do mascote exibido no `README.md` e adicionado a `index.html`.
- Fundação mínima de testes frontend com Vitest + React Testing Library + jsdom, cobrindo os novos comportamentos críticos desta sprint; cobertura ampla e CI continuam na Sprint 8.

## Capabilities

### New Capabilities
- `pdf-export-code-splitting`: `jsPDF`/`html2canvas` carregados sob demanda, fora do bundle principal.
- `frontend-css-consistency`: `LoginPage`/`HomePage` usando CSS dedicado com tokens, mesmo padrão dos demais componentes.
- `global-error-boundary`: tela de fallback em vez de branco numa exceção JS não tratada.
- `tablet-responsive-layout`: breakpoint ~1024px, sidebar auto-colapsa, sem quebra horizontal em tablet.
- `app-favicon`: ícone da aba do navegador.
- `frontend-testing-foundation`: configuração mínima de Vitest/RTL e testes dos comportamentos críticos introduzidos nesta sprint.

### Modified Capabilities
(nenhuma — `sprint-3-frontend-base-home-dashboard` nunca foi arquivada em `openspec/specs/`, então não há capability canônica pra alterar via delta)

## Impact

- Frontend apenas — nenhuma mudança de backend/API.
- `frontend/src/pages/HomePage.jsx`: exportação de PDF passa a usar `import()` dinâmico; estilos migram pra `HomePage.css`.
- `frontend/src/pages/LoginPage.jsx`: estilos migram pra `LoginPage.css`.
- `frontend/src/App.jsx`: novo componente de error boundary envolvendo as rotas.
- `frontend/src/components/layout/Sidebar.css` e demais CSS: breakpoint tablet adicionado.
- `frontend/index.html`: `<link rel="icon">` adicionado.
- `frontend/package.json` e arquivos de configuração/setup de teste: scripts, dependências e ambiente jsdom.
