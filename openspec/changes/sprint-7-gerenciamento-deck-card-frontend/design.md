## Context

Confirmado por leitura direta do código: `frontend/src/api/decks.js` e `cards.js` só têm `fetchDecks`/`fetchDeck`/`fetchCard`/`fetchDueCards` (GET) — nenhuma função de `create`/`update`/`delete`. Não existe `api/categories.js`. `useApiResource` (`api/hooks.js`) é um hook de fetch-on-mount (GET), não serve pra mutations disparadas por submit de formulário. `App.jsx` tem `/decks` e `/categorias` como `<PlaceholderPage>`. Não existem componentes de modal/dialog em `components/ui/` (só `Button`, `Card`, `Input`).

## Goals / Non-Goals

**Goals:**
- Tela `/decks` real: listar, criar, editar, excluir Deck.
- No detalhe de um Deck: mostrar apenas a quantidade de cards e navegar pelo botão "Ver todos os cards".
- Em `/decks/:deckId/cards`: listar, criar, editar e excluir Card.
- Gerenciamento mínimo de Category (listar + criar), o suficiente pra alimentar o seletor do formulário de Deck.
- Reaproveitar os componentes/tokens já existentes (`Button`, `Card`, `Input`, CSS tokens da Sprint 3/4).

**Non-Goals:**
- Tela de estudo (revisar card, avaliar) — gap separado, registrado em `PRD.md` §7.1, fora de escopo por decisão explícita.
- Tela dedicada `/categorias` — continua `PlaceholderPage`; esta sprint só precisa de um seletor/criador embutido no formulário de Deck, não uma página própria de gerenciamento de categoria.
- Restauração de itens soft-deletados dentro da janela de 7 dias — não foi pedido; se vier a ser necessário, é decisão de produto separada.
- Biblioteca de formulários (React Hook Form, Formik) ou validação de schema (Zod) — poucos formulários simples não justificam a dependência nova.

## Decisions

### D1 — Rotas: lista + criação + detalhe + cards dedicados, sem rota própria de "editar"
`/decks` (lista + link "novo deck"), `/decks/novo` (formulário de criação), `/decks/:deckId` (dados do deck, edição inline, contagem de cards e botão "Ver todos os cards") e `/decks/:deckId/cards` (lista e CRUD de cards). Edição de Deck/Card não ganha rota própria (`/decks/:deckId/editar`) — o mesmo formulário é reaproveitado em modo edição dentro da página correspondente, alternado por estado local (`isEditing`).
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

### D6 — Contagem dedicada retorna somente `count`
`GET /api/v1/cards/count/?deck_id=<uuid>` chama `CardRepository.count_by_deck_id()` e retorna somente `{ "count": N }`. A query inclui `owner_id` e `deleted_at: null`, não carrega Card, Deck nem campos de conteúdo. Um deck ausente ou pertencente a outro usuário resulta em contagem zero, sem revelar a existência do recurso.
- **Alternativa descartada**: usar `GET /cards/?deck_id=` e contar o array no frontend. Rejeitada porque transfere todos os campos de todos os cards para exibir um único número.
- **Alternativa descartada**: manter `card_count` embarcado no documento Deck. Rejeitada porque exigiria sincronização em toda criação, exclusão e restauração de Card; a contagem indexada no Mongo é a fonte correta nesta escala.

### D7 — Código e contrato em inglês; rótulos de interface em português
Os quatro campos de conteúdo passam a ser `front`, `back`, `front_description` e `back_description` na entidade, persistência Mongo, API Django, payload do document-generator, estado interno do frontend, seed e testes. Os campos estruturais do modelo Anki exportado também usam `Front`, `Back`, `FrontDescription` e `BackDescription`. A SPA e o template renderizado no Anki continuam exibindo “Frente”, “Verso”, “Descrição da frente” e “Descrição do verso” ao usuário. Métodos e variáveis derivados seguem a mesma regra (`find_by_front`, `exists_by_front`, `update_back`, `are_backs_similar`). O comando idempotente migra tanto o schema legado (`word`/`translation`/`example.*`) quanto a versão intermediária em português e substitui índices antigos; nenhum alias permanece aceito pela API.

### D8 — O throttle global passa a 10 req/s
Por decisão explícita do usuário durante a Sprint 7, `user` e `anon` passam de `3/second` para `10/second`. As dez primeiras requisições dentro da janela são aceitas e a décima primeira recebe `429`.

### D9 — Um event loop persistente atende as chamadas Motor vindas do DRF síncrono
As views e serializers continuam síncronos, mas deixam de criar um event loop por chamada com `asgiref.async_to_sync`. Uma ponte por processo mantém um loop daemon e executa corrotinas via `asyncio.run_coroutine_threadsafe`. Assim, o singleton `AsyncIOMotorClient` permanece ligado ao mesmo loop mesmo com requests HTTP simultâneos. A conexão inicial também é protegida por lock assíncrono no loop persistente.
- **Motivação observada**: duas consultas de detalhe e duas de cards em paralelo reproduziram `500 RepositoryError: MongoDB not connected` e `429`; uma chamada sobrescrevia o loop do singleton enquanto a outra ainda o usava.

### D10 — Formulário antes da lista e paginação dedicada de 10 cards
`/decks/:deckId/cards` renderiza primeiro o formulário de criação e depois a lista. `CardListCreateView` usa uma paginação própria de 10 itens, sem alterar o `PAGE_SIZE` global dos demais recursos. A SPA envia `page`, usa `count`/`next`/`previous` da resposta DRF e oferece “Anterior”/“Próxima” com o indicador “Página X de Y”. Depois de criar, recarrega a página 1; depois de excluir, recarrega a página atual ou a anterior quando a página fica vazia.

### D11 — Estatísticas históricas do deck vêm da agregação já especificada na Sprint 9
O detalhe do deck e a Home consomem `GET /api/v1/decks/{deck_id}/statistics/`, capability já definida em `sprint-9-estatisticas-por-deck`, e usam `rating_distribution` para renderizar o mesmo gráfico Chart.js com `Errou`, `Difícil`, `Bom` e `Fácil`. Na Home, o `deck_id` continua vindo da revisão mais recente, mas a página paginada de `GET /reviews/` não é somada para formar o gráfico. A distribuição considera todo o histórico ativo do deck e sempre contém as quatro chaves zeradas quando não há revisões. O endpoint agrega no MongoDB, preserva isolamento por `owner_id` e não devolve documentos crus. A implementação antecipada do endpoint continua pertencendo à especificação da Sprint 9; esta change antecipa seus consumidores sem duplicar a capability.

## Risks / Trade-offs

- **[Risco]** Sem validação de schema client-side (Zod/Yup) — só validação HTML5 nativa (`required`, `maxLength`) e os erros que a API já devolve. Se a API devolver uma mensagem de erro pouco amigável, a UX de erro fica crua. → **Mitigação**: mapear pelo menos os campos obrigatórios com `required` nativo, reduzindo a superfície de erro que chega até a API.
- **[Risco]** Sem UI de restauração dentro da janela de 7 dias — um usuário que excluir por engano só recupera via chamada manual à API (ou suporte). → **Mitigação**: nenhuma nesta sprint (decisão explícita de não fazer); o `ConfirmDialog` deve deixar claro na mensagem que a exclusão tem uma janela de retenção, mas não que existe um jeito de desfazer pela UI.
- **[Risco]** Renomear campos torna documentos antigos ou intermediários ilegíveis pelo contrato novo. → **Mitigação**: comando idempotente de migração Mongo que prioriza os campos intermediários em português, usa o schema legado como fallback e remove aliases residuais antes de recriar os índices em inglês.
- **[Risco]** Um thread daemon por processo precisa sobreviver a concorrência e fork/reload. → **Mitigação**: inicialização lazy protegida por lock e recriação quando o PID muda; teste de regressão dispara detalhe e contagem em paralelo.
- **[Risco]** Criar ou excluir um card pode invalidar a composição da página atual. → **Mitigação**: mutations bem-sucedidas recarregam uma página válida a partir da resposta paginada, em vez de manter uma lista local com 11 itens ou uma página vazia.

## Migration Plan

1. Publicar o código que entende somente o contrato novo.
2. Executar o comando idempotente de migração dos documentos Mongo, renomeando os quatro campos sem alterar valores.
3. Reiniciar os processos Django para aplicar throttle e ponte assíncrona.
4. Validar detalhe e contagem concorrentes, CRUD completo e exportação com os nomes novos.
