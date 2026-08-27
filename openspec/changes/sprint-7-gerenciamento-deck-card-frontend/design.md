## Context

Confirmado por leitura direta do código: `frontend/src/api/decks.js` e `cards.js` só têm `fetchDecks`/`fetchDeck`/`fetchCard`/`fetchDueCards` (GET) — nenhuma função de `create`/`update`/`delete`. Não existe `api/categories.js`. `useApiResource` (`api/hooks.js`) é um hook de fetch-on-mount (GET), não serve pra mutations disparadas por submit de formulário. `App.jsx` tem `/decks` e `/categorias` como `<PlaceholderPage>`. Não existem componentes de modal/dialog em `components/ui/` (só `Button`, `Card`, `Input`).

## Goals / Non-Goals

**Goals:**
- Tela `/decks` real: listar, criar, editar, excluir Deck.
- Dentro de um Deck: listar, criar, editar, excluir Card.
- Gerenciamento mínimo de Category (listar + criar), o suficiente pra alimentar o seletor do formulário de Deck.
- Reaproveitar os componentes/tokens já existentes (`Button`, `Card`, `Input`, CSS tokens da Sprint 3/4).

**Non-Goals:**
- Tela de estudo (revisar card, avaliar) — gap separado, registrado em `PRD.md` §7.1, fora de escopo por decisão explícita.
- Tela dedicada `/categorias` — continua `PlaceholderPage`; esta sprint só precisa de um seletor/criador embutido no formulário de Deck, não uma página própria de gerenciamento de categoria.
- Restauração de itens soft-deletados dentro da janela de 7 dias — não foi pedido; se vier a ser necessário, é decisão de produto separada.
- Biblioteca de formulários (React Hook Form, Formik) ou validação de schema (Zod) — poucos formulários simples não justificam a dependência nova.

## Decisions

### D1 — Rotas: lista + criação + detalhe (edição inline), sem rota própria de "editar"
`/decks` (lista + link "novo deck"), `/decks/novo` (formulário de criação), `/decks/:deckId` (detalhe: dados do deck com edição inline via toggle, lista de cards, criação/edição/exclusão de card). Edição de Deck/Card não ganha rota própria (`/decks/:deckId/editar`) — o mesmo formulário de criação é reaproveitado em modo edição dentro da tela de detalhe, alternado por estado local (`isEditing`), evitando duplicar o formulário em duas rotas.
- **Alternativa descartada**: modal de criação/edição sobre a lista, sem navegação. Rejeitada — o projeto não tem componente de modal ainda (ver D3), e a tela de detalhe do deck (pra listar os cards) precisa existir de qualquer forma; reaproveitar essa tela pra edição é mais barato que construir um modal só pra isso.

### D2 — Category sem tela própria, criada inline no formulário de Deck
O seletor de categoria no formulário de Deck é um `<select>` nativo populado por `GET /api/v1/categories/`, com uma opção "+ nova categoria" que revela um `Input` inline — cria via `POST /api/v1/categories/` e seleciona a categoria recém-criada automaticamente. `/categorias` continua `PlaceholderPage`; uma tela de gerenciamento completo de categoria (editar/excluir) fica pra quando houver necessidade real além de "alimentar o formulário de deck".
- **Alternativa descartada**: construir a tela `/categorias` completa nesta sprint. Rejeitada — não foi pedido, e o único consumidor real de categoria hoje é o formulário de deck; over-scope sem necessidade de produto confirmada.

### D3 — `ConfirmDialog`: um componente novo, não `window.confirm()` nem lib de modal
Exclusão de Deck/Card/Category precisa de confirmação com aviso da janela de 7 dias — usado em 3 lugares, o suficiente pra justificar um componente compartilhado (não é abstração prematura: 3 usos imediatos, não hipotéticos). `window.confirm()` nativo quebraria a consistência visual (`<regra_obrigatoria>` de design), e uma lib de modal (Radix, Headless UI) é dependência nova pra um caso de uso simples — `ConfirmDialog` é construído com `Card`/`Button` já existentes, sem dependência nova.

### D4 — Mutations via `apiFetch` direto no componente, sem hook genérico
Cada formulário chama `apiFetch` diretamente no `onSubmit`, gerenciando `loading`/`error` com `useState` local — mesmo espírito da decisão já registrada (`frontend-data-fetching`, D3 do design.md da Sprint 3): fetch nativo sem abstração adicional até haver dor real. Diferente de GETs (que compartilham a forma "buscar e exibir", coberta por `useApiResource`), mutations têm pouca forma compartilhada entre si — cada formulário tem campos/validação próprios — generalizar cedo aqui seria abstração sem uso real por trás.

### D5 — Novos módulos de API seguem o padrão já estabelecido (um arquivo por recurso)
`api/decks.js` e `api/cards.js` ganham `createDeck`/`updateDeck`/`deleteDeck` e `createCard`/`updateCard`/`deleteCard`; novo `api/categories.js` com `fetchCategories`/`createCategory`. Mesmo padrão de módulo-por-recurso já usado em `decks.js`/`cards.js`/`reviews.js`/`auth.js`.

## Risks / Trade-offs

- **[Risco]** Sem validação de schema client-side (Zod/Yup) — só validação HTML5 nativa (`required`, `maxLength`) e os erros que a API já devolve. Se a API devolver uma mensagem de erro pouco amigável, a UX de erro fica crua. → **Mitigação**: mapear pelo menos os campos obrigatórios com `required` nativo, reduzindo a superfície de erro que chega até a API.
- **[Risco]** Sem UI de restauração dentro da janela de 7 dias — um usuário que excluir por engano só recupera via chamada manual à API (ou suporte). → **Mitigação**: nenhuma nesta sprint (decisão explícita de não fazer); o `ConfirmDialog` deve deixar claro na mensagem que a exclusão tem uma janela de retenção, mas não que existe um jeito de desfazer pela UI.

## Migration Plan

Sem migração — só código novo de frontend, consumindo endpoints de API que já existem desde a Sprint 2/6. Nenhuma mudança de contrato de API.
