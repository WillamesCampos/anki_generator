## Context

Hoje `Deck`/`Card` não têm nenhum conceito de exclusão — os repositórios (`apps/decks/infrastructure/repositories/`) não implementam `delete()` nenhum sobre essas entidades (só existe a menção a cascade em `DeckRepository.delete()` cascateando pra `Card`, citada no gap de `CardReview` órfã do `PRD.md` §7.1 — mas hoje isso é sobre delete físico, que este design substitui por soft delete). `Card.deck_id` é um `Optional[uuid.UUID]` único (confirmado lendo `apps/decks/domain/entities/card.py`) — hoje é sempre 1 card = no máximo 1 deck, nunca N:N.

Decisões fechadas via `backend-mentor` antes desta sprint: soft delete por timestamp (não booleano), sem introduzir N:N entre Card e Deck agora (custo de retrofit em toda query existente não se justifica sem um requisito de produto real de card compartilhado entre decks), meta de estudo promovida de client-side/global (Sprint 3) pra persistida/por-deck.

## Goals / Non-Goals

**Goals:**
- Soft delete com janela de retenção de 7 dias pra Deck, Card e Category, com purge automático depois.
- Cascade determinístico Deck→Card na exclusão (sem ambiguidade, já que não existe N:N); desvínculo (não cascade) Category→Deck.
- `CardReview` preservada como histórico, nunca apagada.
- Meta de estudo por deck, persistida no backend, alimentando a Sprint 8.
- Edição completa de Deck/Card via PATCH.

**Non-Goals:**
- Relação N:N entre Card e Deck (cards compartilhados entre múltiplos decks) — decisão explícita de não fazer agora; ver D2.
- Tela de restauração manual dentro da janela de 7 dias — não foi pedido; se vier a ser necessário, é uma decisão de produto separada, não implícita nesta sprint.
- Exclusão de `CardReview` — nunca é apagada, nem soft nem físico (ver D3).

## Decisions

### D1 — `deleted_at: Optional[datetime]`, filtro centralizado, não repetido em cada query
Timestamp em vez de booleano: permite calcular `hoje - deleted_at > 7 dias` diretamente pro purge, sem precisar de um segundo campo. Todo repositório (`DeckRepository`, `CardRepository`, `CategoryRepository`, e a agregação de estatísticas da Sprint 8) precisa filtrar `deleted_at: None` — em vez de repetir esse filtro em cada método (risco real de esquecer numa das ~10 queries existentes), um helper único de construção de filtro (`base_filter(owner_id, **kwargs)` retornando sempre `{"owner_id": ..., "deleted_at": None, **kwargs}`) é usado por todo método de leitura. Buscar incluindo deletados (se algum caso de uso futuro precisar) exige passar um parâmetro explícito, nunca o comportamento default.

### D2 — Sem N:N entre Card e Deck: cascade sempre determinístico
Levantado durante o design desta sprint: "e se um card pertencer a mais de um deck?" — não pode, hoje (`Card.deck_id` é um valor único). Decisão explícita: **não** introduzir N:N agora — mudaria `Card.deck_id` pra uma lista/coleção de vínculo, exigiria redesenhar toda query "cards de um deck" existente (incluindo a agregação já planejada da Sprint 8), sem nenhum requisito de produto real pedindo cards compartilhados entre decks. Com 1:1, o cascade de exclusão é sempre determinístico: apagar um deck sempre soft-deleta todos os seus cards, sem caso de "desvincular".
- **Alternativa descartada**: N:N com "desvincula do deck excluído, mantém se vinculado a outro". Rejeitada — não é uma proteção necessária hoje (o soft delete de 7 dias já protege contra exclusão acidental) e custaria uma migração de schema bem maior que o resto desta sprint somado.

### D3 — `CardReview` nunca é apagada, é histórico "congelado"
Resolve de vez o gap de `PRD.md` §7.1 (cascade delete de `CardReview`, aberto desde a Sprint 3). Apagar (soft ou fisicamente) o `CardReview` destruiria histórico de estudo real do usuário sem necessidade — a revisão aconteceu, independente do card/deck ainda existir. Em vez disso, `CardReview` permanece intacta; a Sprint 8 (estatísticas) é responsável por excluí-la dos cálculos quando o `card_id`/`deck_id` associado está soft-deletado (join lógico no momento da agregação, não uma exclusão física).

### D4 — Purge via Celery Beat, primeira task real do projeto
Celery Beat está instalado desde a Sprint 0 sem nunca ter executado nada real. Uma task diária (`purge_soft_deleted`) varre `Deck`/`Card`/`Category` com `deleted_at` há mais de 7 dias e deleta fisicamente. Sem retry/DLQ elaborado nesta sprint — é uma tarefa idempotente por natureza (deletar algo que já foi deletado não tem efeito colateral), então o `<ponto_critico id="idempotencia-revisao">` já está satisfeito por construção pra esse caso específico, sem precisar de tratamento especial.

### D5 — `daily_review_goal` no Deck, consumido pela Sprint 8
Substitui a decisão `meta-de-estudo-client-side` da Sprint 3 (que era client-side/global por não haver spec de produto na época). Agora que existe uma definição precisa (meta por deck), o campo é persistido e sobrevive entre dispositivos. A Sprint 8 é quem calcula o progresso contra essa meta — esta sprint só cria e permite editar o campo.

### D6 — Category também vira soft delete, mas com desvínculo, não cascade (ampliado numa auditoria pré-sprint)
Achado via `backend-mentor` numa auditoria antes desta sprint começar: `Category` estava fora do desenho original apesar de ser a mesma sprint de "política de exclusão", e `CategoryRepository.delete()` era delete físico sem checar se algum `Deck` ainda referenciava a categoria via `category_id` (confirmado por leitura direta do código) — deixava uma referência dangling.

`Category` ganha `deleted_at` (soft delete), simétrico a Deck/Card, incluído no mesmo helper de filtro (D1) e no mesmo purge job (D4). Mas o comportamento de deleção diverge do cascade Deck→Card: excluir uma categoria **não** cascateia pros decks que a referenciam — em vez disso, esses decks são **desvinculados** (`category_id` volta a `None`). Motivo: `category_id` sempre foi `Optional[uuid.UUID]` (rótulo organizacional), diferente da relação obrigatória Card→Deck que motivou o cascade em D2. Cascatear a exclusão destruiria decks do usuário só porque a categoria deles sumiu — uma surpresa destrutiva sem pedido de produto real por trás.
- **Alternativa descartada**: cascatear a exclusão de categoria pros decks (mesmo padrão do D2). Rejeitada — categoria e deck não têm a mesma relação de posse que card e deck têm; um usuário reorganizando/removendo um rótulo não espera perder decks.
- **Alternativa descartada**: bloquear a exclusão de categoria enquanto houver deck vinculado (erro 409, por exemplo). Rejeitada — adiciona uma UX de "não consigo excluir isso" sem necessidade real; desvínculo automático é mais simples e não perde dado nenhum (o deck continua existindo, só sem categoria).

Também nesta auditoria: removidos `DeckRepository.find_by_user_id`/`count_by_user_id` — código morto (duplicavam `find_all`/`count`, sem nenhum call-site em view/teste/seed). Deixá-los sem uso e sem o filtro de soft delete seria uma armadilha esperando alguém chamar um dia.

## Risks / Trade-offs

- **[Risco]** Esquecer o filtro `deleted_at: None` numa query nova, futura, que não usa o helper centralizado — reintroduziria registros "excluídos" nos resultados. → **Mitigação**: o helper é a única forma "fácil" de montar o filtro base; qualquer query que monte o filtro manualmente sem ele deve ser tratada como suspeita em revisão de código.
- **[Risco]** Se o purge job falhar silenciosamente (Celery Beat não disparar), registros soft-deletados nunca são purgados — sem consequência funcional imediata (continuam filtrados das leituras), mas cresce o tamanho das collections indefinidamente. → **Mitigação**: fora de escopo monitorar isso agora (observabilidade é Sprint 15) — mas vale registrar como algo a observar quando a Sprint 15 chegar, já que essa é a primeira task Celery real do projeto e não há visibilidade nenhuma hoje se ela roda.

## Migration Plan

Sem migração de dados: `deleted_at`/`daily_review_goal` novos em dataclasses (sem schema fixo no Mongo) começam ausentes em documentos antigos — o helper de filtro trata ausência do campo como equivalente a `None` (não deletado). Task Celery Beat registrada em `CELERY_BEAT_SCHEDULE` (novo, `core/settings/base.py`).
