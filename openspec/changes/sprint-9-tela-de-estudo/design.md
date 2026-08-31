## Context

Confirmado por leitura direta do código: `POST /api/v1/cards/{card_id}/review/` (`CardReviewView`) já dispara o agendamento FSRS (`scheduling_service.review_card`) e persiste o evento em `CardReview` desde a Sprint 2, sem alteração necessária. `GET /api/v1/cards/?due=true` (`CardListCreateView.get_queryset`) já devolve os cards devidos do usuário (`CardRepository.find_due`), mas é global — a view hoje trata `due=true` e `deck_id=X` como filtros mutuamente exclusivos, nunca combinados. Nenhuma tela do frontend cria uma revisão nova; a Home só lê histórico.

## Goals / Non-Goals

**Goals:**
- Estudar os cards devidos de um deck específico, do card à avaliação, ponta a ponta.
- Reaproveitar 100% do backend de revisão já existente (Sprint 2) — só estender a busca de cards devidos com um filtro novo.

**Non-Goals:**
- Estudo global (todos os decks numa sessão só) — decisão explícita via `backend-mentor`: estudo é sempre por deck específico, entrado a partir da tela de detalhe do deck (Sprint 7).
- Sessão retomável (estado persistido de "onde o usuário parou") — decisão explícita: a sessão sempre recomeça buscando os cards ainda devidos: mais simples, sem conceito novo de "sessão" no backend.
- Requeue de cards avaliados como "again" dentro da mesma sessão — consequência direta do Non-Goal anterior: sem estado de sessão, não há como saber "ainda estou nesta sessão" pra revalidar `due_at`. O card só reaparece numa sessão futura (reabrir a tela).

## Decisions

### D1 — `find_due` ganha `deck_id` opcional, em vez de um método novo
`CardRepository.find_due(owner_id, deck_id=None, due_before=None)` — o parâmetro novo é opcional e `None` por padrão, preservando o comportamento atual (busca global) pra quem já chama sem ele. `GET /api/v1/cards/?due=true&deck_id=X` para de tratar os dois query params como mutuamente exclusivos.
- **Alternativa descartada**: método novo dedicado (`find_due_by_deck_id`). Rejeitada — duplicaria a lógica de filtro/ordenação do `find_due` existente pra uma diferença de uma linha (um `deck_id` a mais no filtro).

### D2 — Sessão sem estado persistido, sem requeue de "again"
A tela busca os cards devidos do deck **uma vez**, ao entrar, guarda a lista em memória (estado local do componente) e itera sobre ela. Não há um `POST /api/v1/decks/{id}/study-session/` nem qualquer conceito de sessão no backend. Motivo: decisão explícita do usuário (`backend-mentor`) de manter isso simples nesta primeira versão — o custo de uma sessão persistida/retomável (novo modelo, novo endpoint, lógica de expiração) não se justifica sem um requisito de produto real pedindo isso.

Consequência aceita conscientemente: um card avaliado como "again" (que o FSRS costuma reagendar pra poucos minutos à frente, não pro dia seguinte) **não** volta a aparecer na mesma sessão — só a próxima vez que o usuário abrir a tela de estudo daquele deck. Diferente do Anki "de verdade" (que reinjeta cards de aprendizado na fila da sessão atual). Aceito como trade-off da v1; se incomodar na prática, é o sinal concreto de que vale revisitar com sessão persistida.
- **Alternativa descartada**: reconsultar `find_due` a cada avaliação, ao invés de usar a lista buscada no início. Rejeitada — geraria uma chamada de API extra por card revisado sem benefício para esta v1; o rate limit atual é 10 req/s.

### D3 — Reaproveita o endpoint de revisão existente sem alteração
`POST /api/v1/cards/{card_id}/review/` não muda. A tela de estudo é só um novo consumidor desse endpoint — nenhuma mudança de contrato, nenhuma migração.

## Risks / Trade-offs

- **[Risco]** Sem sessão persistida, se o usuário fechar a aba no meio do estudo, perde a noção de progresso da sessão (mas não perde nenhuma revisão já feita — cada avaliação já foi persistida via `POST /review/` no momento em que aconteceu). → **Mitigação**: nenhuma nesta sprint, aceito como trade-off da v1.
- **[Risco]** Cards "again" não reaparecerem na mesma sessão pode frustrar quem espera o comportamento clássico do Anki. → **Mitigação**: nenhuma nesta sprint — registrar como ponto a reconsiderar se virar reclamação recorrente de uso real (não de suposição).

## Migration Plan

Sem migração — `find_due` ganha um parâmetro opcional (retrocompatível), sem mudança de schema. Só código novo de frontend consumindo endpoints que já existem (Sprint 2) ou que ganham um filtro a mais (este change).
