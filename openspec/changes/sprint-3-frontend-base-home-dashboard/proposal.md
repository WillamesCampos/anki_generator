## Why

Sprints 1–2 entregaram uma API funcional (auth JWT, multi-tenant, CRUD de decks/cards/categorias, repetição espaçada) sem nenhuma superfície visual — o produto só existe via `curl`/testes. Sprint 3 é a primeira tela real, consumindo essa API já pronta, e estabelece a base (scaffold, tokens visuais, roteamento, camada de dados) sobre a qual todas as telas futuras (Sprints 4+) serão construídas.

## What Changes

- Scaffold da SPA React (build tool, roteamento, estrutura de pastas) — primeiro código frontend do projeto.
- Extração de tokens visuais a partir de `design_system/design-system.html` (que por sua vez documenta `refs/Ashley_files/style.css`, um template estático jQuery/Bootstrap/GSAP) para um formato consumível por componentes React — nenhuma cor/fonte/espaçamento pode ser inventado fora dessa fonte.
- Tela Home: último deck estudado, meta de estudo + % alcançado, gráfico de estatísticas (client-side, consumindo a API do Django).
- Exportação do gráfico da home para PDF.
- Menu lateral de navegação: decks, categorias, geração de relatórios, chat com agente de IA (placeholder até a Sprint 5 — item ainda sem backend).
- Processo de auditoria de consistência visual contra o design system (revisão manual/checklist, não necessariamente automatizado).

## Capabilities

### New Capabilities
- `frontend-app-shell`: scaffold da SPA (build tool, roteamento, estrutura de pastas, camada de chamada à API do Django).
- `design-tokens`: tokens visuais (cor, tipografia, espaçamento) extraídos do design system para uso consistente em todos os componentes React.
- `home-dashboard`: tela Home (último deck estudado, meta de estudo, gráfico de estatísticas) e exportação desse gráfico para PDF.
- `app-navigation`: menu lateral com as seções do produto (decks, categorias, relatórios, chat IA placeholder).
- `review-history-api` (backend, adicionado em implementação — ver Impact): `GET /api/v1/reviews/`, expondo o histórico de `CardReview` do usuário, necessário para a Home renderizar último deck estudado e o gráfico de estatísticas.

### Modified Capabilities
(nenhuma — `sprint-2-decks-cards` nunca foi arquivada em `openspec/specs/`, então não há capability canônica pra alterar; `review-history-api` entra como capability nova, mesmo residindo no backend)

## Impact

- `frontend/`: deixa de ser só um placeholder — recebe o scaffold completo da SPA.
- **Correção em implementação**: a Sprint 2 persistia `CardReview` mas não expunha nenhum endpoint de leitura — a Home precisa de histórico de revisões (último deck estudado, gráfico de estatísticas) que não existia via API. Adicionado `GET /api/v1/reviews/` (Generic `ListAPIView` reaproveitando `CardReviewRepository`, + novo método `find_by_owner`) — impacto mínimo e contido no backend, não o "zero impacto" originalmente previsto.
- `design_system/design-system.html` e `refs/Ashley_files/` passam a ser referenciados ativamente pelo código (antes eram só documentação estática).
