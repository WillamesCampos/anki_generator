> **Metodologia (a partir desta sprint): TDD.** Cada tarefa de comportamento começa por um teste que falha — visto falhar pelo motivo certo —, depois o código mínimo e o refactor. A seção 6 lista o que precisa ficar coberto; os testes são escritos junto de cada tarefa, não depois. Arquivos de configuração/infra (compose, env, Dockerfile) são exceção da skill.

## 1. Infraestrutura — bucket S3 e revisão de regra

- [ ] 1.1 Criar bucket S3 privado (`sa-east-1`), sem acesso público
- [ ] 1.2 Criar usuário IAM dedicado com policy restrita ao bucket (`s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`)
- [ ] 1.3 Configurar lifecycle rule expirando objetos sob `exports/` após 7 dias
- [x] 1.4 Adicionar credenciais/nome do bucket/região/`EXPORT_MAX_CARDS` como variáveis de ambiente (`.env`, `config.example.env`, `docker-compose.yml` do `web`/`celery-worker`)
- [x] 1.5 Adicionar `boto3` como dependência do Django (`pyproject.toml`)
- [x] 1.6 S3 nos testes: `moto` como dependência de dev do Django, fixture pytest que sobe um S3 falso com o bucket criado — usada localmente e no CI (sem credencial AWS nem serviço extra no CI)
- [x] 1.7 S3 em desenvolvimento local: serviço `s3-local` (`moto` em modo servidor — o MinIO decidido antes ficou indisponível, imagens oficiais retiradas) no `docker-compose.yml` atrás do perfil `s3-local`, só dev, usuário não-root (critério 10), bucket criado na subida pelo `s3-local-init`, `AWS_S3_ENDPOINT_URL` (interno, `put_object`) e endpoint público separado pra assinar presigned URLs alcançáveis pelo navegador; vazio em produção → AWS real
- [x] 1.8 Revisar a regra `s3-frontend-confirmado` e as menções de "AWS só pro frontend" em `PROMPT_REFINADO.md`, `PRD.md` e `README.md`

## 2. Resiliência reutilizável (circuit breaker + retry)

- [ ] 2.1 Adicionar `pybreaker` e `tenacity` como dependências do Django
- [ ] 2.2 Wrapper reutilizável em `django/core/` envolvendo chamadas de serviço: `tenacity` por dentro (retry com backoff exponencial, tentativas limitadas, **só** timeout/erro de conexão/5xx), `pybreaker` por fora (trata a operação de retry inteira como uma falha só; 4xx não é retentado nem conta pro breaker — ver D3 em `design.md`). **Decidido: 2 tentativas (retentando timeout de leitura, conexão e 5xx), estado do breaker compartilhado via `CircuitRedisStorage`, um breaker por serviço-alvo. Valores propostos na Open Question 2 (`fail_max=3`, `reset_timeout=120 s`, backoff exponencial com jitter 5–30 s) — confirmar com o usuário antes de codar; o wrapper nasce com política por chamada (D3)**
- [ ] 2.3 Aplicar o wrapper em `call_document_generator` (`django/core/service_clients.py`), sem alterar a assinatura pública da função
- [x] 2.4 Timeout explícito por call-site (hoje `requests` sem timeout pode pendurar indefinidamente): a exportação Anki usa um timeout **próprio e maior** que o das demais chamadas, lido de setting nomeada (`DOCUMENT_GENERATOR_EXPORT_TIMEOUT` ou similar), sem mudar a assinatura de `call_document_generator`. Medição de 100 cards com gTTS real já feita (81 s típico, 114 s no pior caso de texto — ver Open Question 2); valor decidido: **300 s de leitura** (5 s de conexão proposto), 2 tentativas

## 3. `document-generator` — exportação Anki endurecida

- [x] 3.1 Contrato de `POST /decks/export`: `deck_id` (UUID do deck) e `id` (UUID) por card obrigatórios; atualizar `test_card_model_contract.py` (D8)
- [x] 3.2 IDs estáveis em `generator.py`: `deck_id` do genanki derivado deterministicamente do UUID do deck, `model_id` constante fixa junto de `EXPORT_FORMAT_VERSION`, `guid` da nota via `genanki.guid_for(card_id)` (D8)
- [x] 3.3 Nome de arquivo de áudio determinístico (hash do `front`), sem duplicar mídia na lista do pacote (D8)
- [x] 3.4 Diretório de trabalho único por requisição para áudio e `.apkg`, removido após a resposta ser enviada (`BackgroundTask`) — corrige colisão entre tenants e acúmulo no volume (D10)
- [x] 3.5 Rota `/decks/export` fora do event loop (rota `def` ou `run_in_threadpool`) (D10)
- [x] 3.6 Teto de 100 cards no serviço (defesa em profundidade) e remoção/alinhamento do `max_cards_per_generation = 10` morto em `app/config.py` (D9)

## 4. Endpoint de exportação, cache e status (Django)

- [x] 4.1 Builder único do payload de exportação a partir do deck + cards ativos (sem `deleted_at`), e função pura `compute_content_hash(payload)` — sha256 do JSON canônico com `EXPORT_FORMAT_VERSION`, título, cards em ordem determinística; sem estado FSRS (D7)
- [x] 4.2 Helpers do registro Redis: `export:by-id:{export_id}` e `export:by-content:{owner_id}:{deck_id}:{hash}`, criação com `SET NX`, transições `pending`→`completed`/`failed`, TTLs (D5)
- [x] 4.3 `POST /api/v1/decks/{deck_id}/export/`: `404` se o deck não é do usuário; `400` com 0 ou >100 cards ativos; miss → cria registro + enfileira task + `202`; hit `completed` → `200` sem task; em andamento → `202` com `export_id` existente (D7/D9)
- [x] 4.4 Task Celery recebendo o snapshot `(export_id, owner_id, deck_id, content_hash, payload)` (não relê o Mongo): chama `call_document_generator` (com resiliência da seção 2), sobe o `.apkg` em `exports/{owner_id}/{deck_id}/{hash}.apkg`, marca `completed` com `s3_key`; ao iniciar, se o registro `by-id` já não existir (expirou na fila) encerra sem gerar e, se existir, renova o TTL do `pending`; em qualquer falha marca `failed` e apaga o ponteiro de conteúdo, sem upload
- [x] 4.5 `GET /api/v1/decks/export/{export_id}/status/`: lê o registro Redis, `404` se inexistente/expirado/de outro tenant, gera presigned URL (15 min, assinatura local a cada consulta) quando `completed`
- [x] 4.6 (valores de `pending`/limites da task PROPOSTOS, a confirmar) Configuração dos TTLs (registro/ponteiro `completed` = 6 dias; `failed` curto; `pending` = 900 s proposto, renovado no início da task) e `soft_time_limit` 660 s / `time_limit` 720 s da task Celery de exportação (propostos; acima do pior caso ≈ 606 s = 2 × 300 s + backoff — Open Question 2) como settings/variáveis, não constantes soltas

## 5. PDF genérico (document-generator)

- [ ] 5.1 Adicionar `reportlab` (decidido pelo usuário) ao `requirements.txt` do `document-generator` e **confirmar com o usuário o formato do payload de seções** (a proposta a validar: texto, tabela e imagem, pensando no relatório da Sprint 15) — ver Open Question 1 em `design.md`
- [ ] 5.2 `POST /document-generator/v1/documents/pdf`: gera PDF a partir de título + seções de conteúdo, atrás de `require_service_jwt` (mesmo padrão de `/decks/export`)
- [ ] 5.3 Sem consumidor Django nesta sprint — capability isolada, testada só no microsserviço

## 6. Testes automatizados

- [x] 6.1 Hash de conteúdo (pytest): mesmo conteúdo → mesmo hash; editar `front`/`back`/descrições/notas/título, criar ou soft-deletar card → hash muda; **revisão de estudo (FSRS) não muda o hash**; ordem estável; mudar `EXPORT_FORMAT_VERSION` muda o hash; teste que compara os campos do payload com os do hash (um builder só)
- [x] 6.2 Endpoint de exportação: enfileira a task sem chamar `document-generator` na mesma request; `404` cross-tenant sem vazar existência; `400` deck vazio e deck >100 cards; cards soft-deletados não contam nem entram no payload
- [x] 6.3 Cache: miss → `202` + task; segundo `POST` idêntico com a exportação em andamento → `202` com o mesmo `export_id` e **uma** task só; após concluída → `200` sem task e sem chamada ao `document-generator`; após editar um card → miss com hash novo; **cache nunca compartilhado entre tenants**
- [x] 6.4 Status: dono vê `pending`/`completed` (com URL fresca)/`failed`; `404` para id desconhecido, expirado e de outro tenant (mesma resposta), inclusive em `pending`
- [ ] 6.5 Wrapper de resiliência: breaker abre após falhas consecutivas simulando indisponibilidade do `document-generator`, permanece fechado em operação normal, meio-aberto testa uma chamada após o cooldown; **estado compartilhado entre processos** (falhas contadas num processo abrem o breaker pros outros; comportamento com Redis indisponível); retry só em timeout/conexão/5xx — `4xx` falha na hora e não conta pro breaker; falha após esgotar retries conta como **uma** falha pro breaker
- [x] 6.6 Task Celery: sucesso (`completed` + `s3_key`, upload na chave com hash) e falha após esgotar retry/breaker (`failed`, sem upload, ponteiro de conteúdo apagado permitindo nova tentativa) — com S3 falso via `moto` (1.6)
- [x] 6.7 `document-generator` (pytest): dois exports do mesmo `deck_id` produzem o mesmo deck id/model id/guids; duas requisições simultâneas com o mesmo título não compartilham arquivo; >100 cards recusado; sem JWT válido → `401`
- [ ] 6.8 `document-generator` (pytest): rota de PDF aceita requisição autenticada e rejeita sem JWT válido, igual ao padrão de `/decks/export`

## 7. Validação manual

- [ ] 7.1 Disparar uma exportação ponta a ponta (endpoint → task → S3 → status → download) e abrir o `.apkg` resultante no Anki real (critério de aceite 7)
- [ ] 7.2 Editar um card, reexportar e reimportar no Anki: o deck e as notas existentes são **atualizados**, não duplicados (D8)
- [x] 7.3 Exportar duas vezes sem editar nada: a segunda responde `200` sem nova geração (confirmar nos logs que o `document-generator` não foi chamado) — validado ponta a ponta com containers reais em 2026-09-26 (2 chamadas ao gerador para 4 exports, 2 deles cache hit)

## 8. Documentação

- [ ] 8.1 Atualizar `PRD.md` (Sprint 11) marcando as tarefas concluídas
- [ ] 8.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 11]`
- [ ] 8.3 Documentar o contrato de payload/resposta Django ↔ `document-generator` (header de autenticação incluso) — coberto pelos specs desta change, revisar se precisa de nota adicional fora do openspec
- [ ] 8.4 Remover comentários desatualizados em `core/service_clients.py` ("Sprint 9") e `document-generator/app/generator.py` ("Sprint 4") que apontam pra sprint errada
