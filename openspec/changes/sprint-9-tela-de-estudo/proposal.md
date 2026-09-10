## Why

Gap mais fundamental do produto, registrado em `PRD.md` §7.1 desde a auditoria pré-Sprint 6 e formalizado agora via `backend-mentor`: nenhuma sprint do roadmap jamais construiu a tela que mostra um card e permite avaliá-lo (`again`/`hard`/`good`/`easy`) — a Home só lê histórico de revisão (`GET /api/v1/reviews/`), nunca cria um novo. O backend já tem a maior parte do necessário desde a Sprint 2 (`POST /api/v1/cards/{card_id}/review/`, FSRS); falta a UI e um ajuste pontual de backend (a busca de cards devidos não filtra por deck hoje).

## What Changes

- `CardRepository.find_due(owner_id, deck_id=None, due_before=None)` ganha filtro opcional por deck.
- `GET /api/v1/cards/?due=true&deck_id=X` passa a aceitar os dois parâmetros juntos — hoje são mutuamente exclusivos na view.
- Botão "Estudar" na tela de detalhe do deck (Sprint 7), navegando pra `/decks/{deckId}/estudar`.
- Tela de estudo: busca os cards devidos do deck uma vez ao entrar (sessão não persistida — decisão explícita via `backend-mentor`, sempre recomeça), mostra a frente do card, revela o verso sob interação, e 4 botões de avaliação que chamam o endpoint de revisão já existente.
- Progresso "X de Y", estado vazio, e tela de fim de sessão.
- E-mail de recuperação do allauth customizado em texto + HTML com a identidade “Dark premium” do Anki Generator; token, URL da SPA e transporte Resend permanecem inalterados.

## Capabilities

### New Capabilities
- `deck-scoped-due-cards`: filtro por deck na busca de cards devidos (`find_due`), endpoint `GET /api/v1/cards/?due=true&deck_id=X`.
- `study-session-ui`: tela de estudo em si — frente/verso do card, avaliação, progresso, estado vazio, fim de sessão.
- `branded-password-reset-email`: override nativo dos templates de recuperação do allauth, com assunto, fallback textual e HTML responsivo próprios.

### Modified Capabilities
(nenhuma — não há capability canônica de "cards devidos" arquivada em `openspec/specs/`; o item acima entra como capability nova mesmo estendendo comportamento já existente desde a Sprint 2)

## Impact

- Backend: `apps/decks/infrastructure/repositories/card_repository.py` (`find_due`), `apps/decks/domain/repositories/icard_repository.py` (interface), `apps/decks/views.py` (`CardListCreateView.get_queryset`).
- Frontend: nova rota `/decks/{deckId}/estudar`, botão "Estudar" na tela de detalhe do deck (Sprint 7), consumindo `POST /api/v1/cards/{card_id}/review/` já existente desde a Sprint 2 — sem mudança de contrato nesse endpoint.
- **Depende da Sprint 7** (tela de detalhe do deck, de onde "Estudar" é acionado).
- Fora de escopo, por decisão explícita: estudo global (todos os decks numa sessão só) e sessão retomável (estado persistido) — ver `design.md`.
- Backend de autenticação: diretório de templates do projeto, três templates `account/email/password_reset_key_*` e teste de renderização multipart; nenhum impacto no React.
