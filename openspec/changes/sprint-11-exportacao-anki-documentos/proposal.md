## Why

O microsserviço `document-generator` já gera `.apkg` compatível com o Anki (`POST /document-generator/v1/decks/export`, protegido por JWT de serviço desde a Sprint 5) mas nunca foi ligado ao Django — nenhuma view, nenhuma task Celery, nenhum caminho dispara essa geração hoje. Fecha o ciclo do microsserviço de documentos já reclassificado na Sprint 0, cumprindo o critério de aceite 2 (toda chamada externa assíncrona via Celery) e o critério 9 (circuit breaker + retry exponencial ativos e testáveis) pela primeira vez no projeto. Uma revisão pré-implementação contra o código real (ver "Revisão pré-implementação" em `design.md`) também ampliou o escopo pra incluir cache por conteúdo, IDs estáveis no `.apkg` e o endurecimento do `document-generator`.

## What Changes

- Endpoint Django `POST /api/v1/decks/{deck_id}/export/` que valida posse e tamanho (1 a 100 cards ativos), calcula o **hash do conteúdo** exportável e: em cache miss enfileira uma task Celery e responde `202`; em cache hit responde `200` já concluído, sem gerar nada; se a mesma exportação já está em andamento responde `202` com o `export_id` existente. Nunca chama o microsserviço na mesma request (critério de aceite 2).
- **Cache de exportação por hash de conteúdo** (D7): chave S3 `exports/{owner_id}/{deck_id}/{content_hash}.apkg` + índice/lock no Redis por `owner_id` — reexportar um deck inalterado não chama o `document-generator`. Revisões de estudo (estado FSRS) não invalidam o cache.
- Task Celery que chama `call_document_generator` (Sprint 5) envolta em circuit breaker (`pybreaker`) + retry exponencial (`tenacity`) — o breaker envolve a operação de retry inteira, e erros 4xx não são retentados nem contam pro breaker (D3).
- Upload do `.apkg` pra um bucket S3 privado, feito pelo Celery worker (nunca pelo `document-generator`) — D1/D2. Mantém o S3 por decisão do usuário, o que **revisa** a regra `s3-frontend-confirmado` de `PROMPT_REFINADO.md`.
- Endpoint Django `GET /api/v1/decks/export/{export_id}/status/`: status (`pending`/`completed`/`failed`) lido de um **registro Redis criado no disparo** (posse checável mesmo em `pending`; `404` indistinguível pra id desconhecido, expirado ou de outro tenant) e, se concluído, presigned URL de 15 min assinada a cada consulta (D5/D6). Sem webhook (D4).
- **`document-generator`**: `/decks/export` ganha `deck_id`/`id` de card no contrato e passa a gerar **IDs estáveis** (deck, modelo, notas) pra reimportar atualizar o deck no Anki em vez de duplicar (D8); teto de 100 cards; diretório de trabalho único por requisição (corrige colisão entre tenants) e geração fora do event loop (D9/D10).
- Geração de PDF genérico no `document-generator` (`POST /document-generator/v1/documents/pdf`), reaproveitada na Sprint 15 — mesma proteção JWT, sem lógica de relatório nesta sprint.
- Contrato de payload/resposta entre Django e `document-generator` documentado nos specs, incluindo o header de autenticação existente.
- Validação manual (critério de aceite 7): abrir um `.apkg` gerado pelo fluxo completo no Anki real, **e** reexportar após editar um card e reimportar pra confirmar que atualiza em vez de duplicar. Não é código, é checklist.

## Capabilities

### New Capabilities
- `deck-anki-export`: endpoints assíncronos de exportação e status, task Celery, cache por hash de conteúdo, armazenamento em S3 e isolamento multi-tenant.
- `document-generator-anki-export`: geração de `.apkg` no microsserviço com IDs estáveis, teto de 100 cards, isolamento de arquivos por requisição e geração fora do event loop.
- `microservice-call-resilience`: circuit breaker + retry exponencial reutilizável em chamadas Django → microsserviços (primeira aplicação: `call_document_generator`), testável simulando indisponibilidade.
- `document-generator-pdf-export`: geração de PDF genérico no `document-generator`, sem consumidor Django nesta sprint (consumida na Sprint 15).

### Modified Capabilities
(nenhuma — nenhum spec de sprint anterior foi arquivado em `openspec/specs/`, então não há capability canônica pra alterar via delta; o comportamento novo é aditivo)

## Impact

- Backend Django: nova view + serializer + urls em `apps/decks/`, builder de payload + hash, helpers do registro Redis, nova task Celery (`apps/decks/tasks.py`), dependências novas (`pybreaker`, `tenacity`, `boto3`), variáveis de ambiente novas (credenciais AWS do usuário IAM dedicado, nome/região do bucket, `EXPORT_MAX_CARDS`, TTLs).
- `document-generator`: contrato de `/decks/export` muda (campos novos obrigatórios; Django é o único chamador), `generator.py` reescrito em IDs/paths, nova rota `POST /documents/pdf` com o mesmo `require_service_jwt`.
- Infra: bucket S3 privado novo (usuário IAM com policy restrita, lifecycle de 7 dias). **AWS antecipada da Sprint 16 pra Sprint 11** — `PROMPT_REFINADO.md`, `PRD.md` e `README.md` atualizados.
- Dev/CI sem AWS: `moto` nos testes (pytest e CI) e o `moto` em modo servidor no `docker-compose.yml` (perfil `s3-local`, só em dev), pra desenvolvimento local e validação manual offline — no lugar do MinIO decidido antes, cujas imagens oficiais foram retiradas do Docker Hub/quay.io.
- Redis: passa a guardar registros de exportação (chaves `export:*`, com TTL) além do result backend/cache já existentes.
- Nenhuma mudança de schema em `Deck`/`Card` (o hash substitui um contador de versão — ver D7).
- Fora de escopo, registrado em `PRD.md` §7.1: **UI de exportação no frontend** (**Sprint 12**, imediatamente depois desta).
