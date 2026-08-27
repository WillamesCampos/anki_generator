## Context

Verificado por grep direto no código (não suposição): `grep -rn "@media" **/*.css` não encontra nada em todo `frontend/src`; nenhum `ErrorBoundary`/`componentDidCatch` em lugar nenhum; `grep -c "style={{" pages/*.jsx components/**/*.jsx` mostra `LoginPage.jsx` (5 ocorrências) e `HomePage.jsx` (4) usando inline `style`, contra zero em `Sidebar`/`Card`/`Button`/`Input`/`AppShell`/`PlaceholderPage`; `index.html` não tem `<link rel="icon">`. O bundle de produção já tem um aviso conhecido (~720KB não comprimido no chunk principal, documentado no `[Sprint 3]` do `CHANGELOG.md`), causado por `jsPDF`+`html2canvas`+Chart.js carregados eagerly mesmo quando o usuário nunca clica "Exportar PDF".

## Goals / Non-Goals

**Goals:**
- Reduzir o bundle inicial tirando `jsPDF`/`html2canvas` do caminho crítico.
- Consistência: toda tela usa CSS dedicado com tokens, não inline `style`.
- Uma exceção JS não tratada mostra uma tela de erro, não branco.
- Layout não quebra horizontalmente num tablet (~1024px e acima).
- Favicon.

**Non-Goals:**
- Redesenho mobile-first (nav diferente tipo drawer/bottom-bar) — decisão explícita do usuário: projeto pessoal, sem uso mobile previsto no curto prazo. Se isso mudar, é uma sprint própria, não uma extensão silenciosa desta.
- Cobertura frontend abrangente, relatório/limites de cobertura e pipeline de CI — continuam na Sprint 8. Esta sprint antecipa apenas a fundação Vitest/RTL e os testes dos comportamentos novos e críticos da própria Sprint 4.
- Tratamento de `403` na SPA — depende de `permission_classes` (Sprint 5) existir primeiro; vira tarefa na Sprint 6 (Ciclo de Vida de Deck/Card).

## Decisions

### D1 — Code-splitting via `import()` dinâmico, não `React.lazy`
`jsPDF`/`html2canvas` não são componentes React, então `React.lazy` (pensado pra componentes) não se aplica diretamente — o padrão certo é `import()` dinâmico dentro do handler de clique do botão "Exportar PDF" (`const { default: jsPDF } = await import("jspdf")`), que o Vite já trata como um chunk separado automaticamente, sem configuração extra em `vite.config.js`.

### D2 — Migração de inline `style` pra CSS: por que só `LoginPage`/`HomePage`
São as duas únicas telas com esse padrão — os 6 demais componentes já usam CSS dedicado com tokens desde que foram criados na Sprint 3. Não é uma decisão de "qual abordagem usar" (já está decidida, é o padrão majoritário do projeto), é fechar uma inconsistência pontual antes que mais telas copiem o padrão errado.

### D3 — Error boundary como componente de classe simples, sem biblioteca externa
React ainda não tem hook equivalente a `componentDidCatch`/`getDerivedStateFromError` (só class components implementam isso nativamente) — um único componente `ErrorBoundary` de ~20 linhas em `App.jsx` é suficiente, sem precisar de `react-error-boundary` ou similar pra um caso de uso simples (uma tela de fallback, sem retry granular por seção).

### D4 — Responsividade via breakpoint único (~1024px), reaproveitando o collapse já existente
Em vez de desenhar um padrão de navegação novo pra telas menores, a sidebar passa a colapsar automaticamente (mesmo mecanismo/CSS da Sprint 3, hoje só manual) quando a viewport cruza ~1024px, via `matchMedia`. Grid da Home (`repeat(auto-fit, minmax(260px, 1fr))`, já responsivo por natureza) e formulários (`LoginPage`) ganham `max-width` pra não esticar feio em telas largas de tablet. Escopo deliberadamente raso: resolve "não quebra", não redesenha a experiência.

### D5 — Favicon: derivação simples do mascote, sem múltiplos tamanhos/manifest
Um PNG 192×192 derivado do mascote exibido no `README.md`, simplificado para permanecer legível em tamanho pequeno e referenciado em `index.html` — sem PWA manifest ou família de ícones por dispositivo, que seriam escopo real de um app instalável, não pedido aqui.

### D6 — Fundação mínima de testes agora; cobertura ampla e CI na Sprint 8
Vitest + React Testing Library + jsdom entram nesta sprint porque integram nativamente com o Vite atual e permitem proteger os comportamentos de robustecimento antes de novas telas serem construídas. A suíte mínima cobre: fallback do `ErrorBoundary`; auto-colapso da sidebar quando `matchMedia` indica tablet e não existe preferência salva; precedência da preferência manual do `localStorage`; e acionamento da importação sob demanda ao exportar PDF. CSS responsivo continua com validação manual, pois jsdom não executa layout, e code-splitting continua confirmado pelo build de produção. Relatório de cobertura, testes abrangentes de API/auth/hooks/telas e GitHub Actions permanecem na Sprint 8.

## Risks / Trade-offs

- **[Risco]** `matchMedia` pra auto-colapsar a sidebar pode conflitar com o toggle manual do usuário (ex.: usuário expande manualmente numa tela de tablet, depois a tela redimensiona) — → **Mitigação**: o estado manual (já persistido em `localStorage` desde a Sprint 3) continua sendo a fonte de verdade quando existe; o auto-colapso só se aplica na ausência de uma preferência manual explícita já salva.
- **[Risco]** Error boundary genérico não distingue tipos de erro (rede vs. bug de render) — → **Mitigação**: aceitável pro escopo desta sprint (evitar tela branca); diferenciação mais fina fica para quando houver observabilidade real (Sprint 14).

## Migration Plan

Sem migração de dados nem de infraestrutura — mudanças de frontend puro, sem impacto em API/schema. Deploy normal (build + arquivos estáticos).
