## Context

Levantamento feito via `backend-mentor` (branch `sprint_11`, a partir do `main` com a Sprint 10 mergeada) confirmou, por leitura direta do código, que a Sprint 5 já entrega toda a infraestrutura de autenticação service-to-service (`django/core/service_auth.py::mint_service_token`, `django/core/service_clients.py::call_document_generator`) e que o `document-generator` já gera `.apkg` de ponta a ponta (`app/routes/decks.py::export_deck`, protegido por `require_service_jwt`) — nunca chamado pelo Django. O volume `document_generator_audio` no `docker-compose.yml` só está montado no container `document-generator`; nem `web` nem `celery-worker` conseguem ler esse disco, então o resultado da geração só pode chegar ao Django via o corpo da resposta HTTP que o endpoint já devolve hoje.

**Revisão pré-implementação** (mesma sessão, antes de qualquer código): uma revisão do trabalho contra o código real encontrou lacunas na versão inicial desta change, decididas com o usuário e incorporadas abaixo — (a) o estado `pending` não permitia checar posse (D5/D6 reescritos), (b) a regeneração do `.apkg` a cada pedido é o custo real a evitar, não o acesso ao S3 (D7, novo), (c) IDs de deck/model do Anki eram aleatórios a cada exportação, duplicando o deck ao reimportar (D8, novo), (d) sem limite de tamanho a geração via gTTS é lenta e imprevisível (D9, novo) e (e) o `document-generator` tinha uma colisão de arquivo entre tenants e bloqueava o event loop (D10, novo).

## Goals / Non-Goals

**Goals:**
- Disparar a geração do `.apkg` de forma assíncrona (critério de aceite 2), com o Django respondendo rápido e o Celery worker fazendo o trabalho pesado.
- Proteger a chamada Django → `document-generator` com circuit breaker + retry exponencial, testável simulando indisponibilidade (critério de aceite 9).
- Persistir o artefato gerado em armazenamento durável (S3), sobrevivendo a reinícios de container.
- Não regenerar um `.apkg` cujo conteúdo não mudou: cache por hash do conteúdo, com deduplicação de exportações em andamento (D7).
- Reexportar um deck editado e reimportar no Anki atualiza o deck existente em vez de duplicá-lo (D8).
- Reaproveitar a geração de PDF genérico no mesmo microsserviço para a Sprint 15, sem acoplar lógica de relatório a esta sprint.

**Non-Goals:**
- Webhook do `document-generator` de volta pro Django — decisão explícita via `backend-mentor` (ver D4). Revisitado na Sprint 14 (Evolution API), onde o webhook resolve um problema real (evento de status de mensagem que o Django não controla), não aqui.
- **UI de exportação no frontend** (botão, loading, polling, notificação in-app) — decisão do usuário: **Sprint 12**, imediatamente depois desta (registrada em `PRD.md`, com o roadmap renumerado). Esta sprint entrega só os endpoints, com um contrato de polling suficiente pra essa sprint futura (estados terminais claros, `404` pra id desconhecido/expirado — ver D5).
- Persistência de histórico de exportações no Mongo (ex.: "últimas exportações do usuário") — fora de escopo; o registro Redis (D5) expira. Se isso virar requisito de produto real, é um gap novo pra registrar.
- Dedupe de exportação **entre tenants** (dois usuários com deck idêntico compartilhando o mesmo objeto) — o cache é sempre por `owner_id` (D7); compartilhar entre tenants vazaria a existência de conteúdo igual.
- Migração de infraestrutura pra IaC (Terraform) — o bucket é criado manualmente; a trilha de aprendizado paralela de Terraform (seção 8 do `PRD.md`) segue independente.
- Lógica de negócio do relatório semanal em PDF (Sprint 15) — esta sprint só entrega a capacidade genérica de gerar PDF (biblioteca decidida: `reportlab`, ver "Open Questions").

## Decisions

### D1 — O upload pro S3 é feito pelo Celery worker, nunca pelo `document-generator`

O `document-generator` continua devolvendo o `.apkg` como binário puro via `FileResponse`. É o Celery worker (lado Django) quem recebe esses bytes e faz o `put_object` no S3. (O **payload** de `/decks/export` ganha `deck_id`/`id` por card por causa do D8 — o formato da resposta não muda.)

Motivo: blast radius. O `document-generator` é o serviço com a porta publicada pro host (`8001:8001`) — a superfície mais exposta do sistema. Dar credencial de escrita em S3 pra esse container aumentaria o que um atacante ganha se ele for comprometido. O Django/Celery já concentra as outras credenciais sensíveis do projeto (Postgres, Mongo, `DJANGO_SECRET_KEY`); manter as credenciais AWS no mesmo perímetro de confiança evita espalhar segredos por mais um serviço.

- **Alternativa descartada**: `document-generator` sobe pro S3 diretamente e devolve só a chave do objeto. Rejeitada — exigiria dar credencial AWS ao serviço mais exposto sem ganho real.

### D2 — Bucket S3 privado, chave determinística por conteúdo, presigned URL, IAM dedicado

- **Decisão do usuário, na revisão pré-implementação: manter o S3** — isso exige revisar a `regra_obrigatoria` `s3-frontend-confirmado` de `PROMPT_REFINADO.md` (que dizia ser o S3 do frontend o único uso de AWS), feito junto com esta change (tarefa 1.8). A dependência de uma conta AWS real adianta-se da Sprint 16 para a 11.
  - **Alternativa considerada**: volume Docker compartilhado montado em `web`/`celery-worker` + download via Django autenticado, sem AWS. Não escolhida.
- **Dev e CI sem AWS (decisão do usuário: os dois)**: `moto` nos testes automatizados (pytest local e CI — sem credencial, sem serviço extra no CI) **e** um S3 local no `docker-compose.yml` para desenvolvimento local e validação manual offline — decidido como MinIO, **implementado como o `moto` em modo servidor** (`motoserver/moto`) porque as imagens oficiais do MinIO foram retiradas do Docker Hub e do quay.io (verificado em 2026-09-26); reversível, sujeito ao veto do usuário. O código lê `AWS_S3_ENDPOINT_URL` (vazio em produção → AWS real). Como a presigned URL assina o host, o cliente que **assina** precisa usar o endpoint que o **navegador** alcança (ex.: `localhost:9000`), diferente do endpoint interno do container (`s3-local:5000`) usado pra `put_object` — por isso duas variáveis de endpoint. O S3 local fica atrás de um perfil do compose (`s3-local`) (só dev), pra não vazar pro compose de produção da Sprint 16, e roda como usuário não-root (critério de aceite 10). A validação real do critério 7 (7.1) usa o bucket AWS de qualquer forma.
- Bucket **privado** (sem acesso público); download sempre via presigned URL (GET), TTL curto (15 min), **assinada sob demanda pelo Django a cada consulta de status** — assinatura é local (HMAC, sem chamada de rede ao S3), então não há ganho em cachear a URL; nunca é armazenada nem logada (quem tem a URL baixa por 15 min sem autenticar).
- **Usuário IAM dedicado** (não a chave root da conta), policy restrita a esse bucket específico e só às ações `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`. Credencial de longa duração, então a validade da URL é exatamente o TTL pedido (com credencial temporária STS, ela morreria junto com a credencial — não se aplica aqui).
- **Lifecycle rule** expirando objetos após 7 dias — mesmo número da retenção de soft-delete da Sprint 6; o artefato é regenerável.
- **Chave do objeto: `exports/{owner_id}/{deck_id}/{content_hash}.apkg`** — escopada por dono e deck, e o hash (D7) faz do próprio nome do objeto o identificador do conteúdo.
- Região `us-east-1` (N. Virginia) — **decisão do usuário: a mais barata** (S3 Standard US$ 0,023/GB-mês; São Paulo custa bem mais). O ganho é de centavos e a latência a partir do Brasil não pesa (exportação assíncrona, download direto do navegador para o S3). Nota: `us-east-1` é a única região cujo `create-bucket` NÃO aceita `LocationConstraint`. Substitui a escolha inicial `sa-east-1`.
- **Alternativa descartada**: bucket público com URL direta — decks exportados são dado de usuário.

### D3 — Circuit breaker envolve a operação de retry inteira, como uma unidade

A chamada `call_document_generator` (Sprint 5) passa a ser envolvida por duas camadas compostas nesta ordem: `pybreaker.CircuitBreaker` por fora, `tenacity` (retry com backoff exponencial) por dentro.

```python
breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

@breaker
@tenacity.retry(wait=tenacity.wait_exponential(), stop=tenacity.stop_after_attempt(3))
def export_via_document_generator(...):
    ...
```

(Valores acima são ilustrativos — ver "Open Questions".)

Motivo: se a ordem fosse invertida (breaker contando cada tentativa individual do retry), uma única chamada de usuário com 3 tentativas internas já consumiria 3 do `fail_max=5` — o breaker abriria rápido demais por causa de uma falha lógica só. Com o breaker por fora, ele só vê "essa operação, no fim das contas, falhou" como um evento único.

**Classificação de erros**: só falha transitória (timeout, erro de conexão, 5xx) é retentada e conta para o breaker. Erro de cliente (4xx — ex.: `400` de deck vazio, `401` de JWT inválido) falha imediatamente, sem retry e sem contar pro breaker: não é indisponibilidade do serviço, e retentar não muda o resultado.

**Política por chamada, não global (decisão do usuário)**: timeout — e, se preciso, número de tentativas — não é um valor único do wrapper. Cada call-site declara a sua política. A exportação Anki usa um timeout **próprio e bem maior** que o das demais chamadas (até 100 cards de gTTS em sequência, D9); o PDF e as integrações futuras (Sprints 13/14) terão os seus. Na prática: o wrapper recebe a política por chamada, `call_document_generator` já repassa `timeout` via `**kwargs` (sem mudar a assinatura pública) e cada uso lê de uma setting nomeada (ex.: `DOCUMENT_GENERATOR_EXPORT_TIMEOUT`), em vez de uma constante compartilhada. O pior caso de uma exportação passa a ser `tentativas × timeout + backoff`, e esse número dimensiona o TTL de segurança do `pending` (D5) e o `time_limit`/`soft_time_limit` da task Celery (senão o worker mataria a task antes do retry terminar).

**Estado compartilhado (decisão do usuário)**: os contadores e o estado do breaker vivem no Redis (`pybreaker.CircuitRedisStorage`), não na memória de cada processo — um breaker por **serviço-alvo** (namespace do serviço), compartilhado entre os call-sites do mesmo serviço, porque o que ele mede é a saúde do serviço, não da operação.

- **Alternativa descartada**: implementar o circuit breaker na mão — `pybreaker` já resolve thread-safety do contador e o timer de cooldown.

### D4 — Sem webhook do `document-generator` de volta pro Django

Webhook (backend→backend) e "o frontend sabe que terminou" são problemas diferentes — um webhook não entrega nada ao frontend sozinho. Como a chamada ao `document-generator` já acontece dentro de uma task Celery (que já satisfaz o critério de aceite 2), não há necessidade de tornar o `document-generator` assíncrono por dentro também — isso duplicaria a fronteira assíncrona que o Celery já garante, ao custo de: um par de chaves JWT novo (direção inversa), tratamento de idempotência (webhook duplicado ou perdido) e uma fila/worker próprios pro FastAPI (`BackgroundTasks` não sobrevive a um restart).

- **Alternativa descartada**: `document-generator` responde `202` na hora e chama o Django de volta via webhook. Rejeitada por desproporção. Revisitar na Sprint 14 (Evolution API), onde a notificação é genuinamente de fora do controle do Django.

### D5 — Estado da exportação vive num registro Redis próprio, não no result backend do Celery

*(Reescrito na revisão pré-implementação — a versão original usava `AsyncResult(task_id)` como fonte de status.)*

O status **não** é lido do result backend do Celery. Motivos, ambos verificados: (1) o `owner_id` só existiria no resultado da task, então enquanto a task está `PENDING` não há como checar posse; (2) `AsyncResult` de um id inexistente ou expirado devolve `PENDING` pra sempre — o frontend faria polling infinito sem distinguir "em andamento" de "nunca existiu".

Em vez disso, o Django grava, **no momento do disparo** (dentro do `POST`, antes de enfileirar), dois tipos de chave no Redis (mesmo Redis já usado como result backend/cache, DB de cache):

- `export:by-id:{export_id}` → `{owner_id, deck_id, content_hash, status, s3_key?}` onde `status ∈ {pending, completed, failed}`. É a fonte do endpoint de status.
- `export:by-content:{owner_id}:{deck_id}:{content_hash}` → `export_id`. É o índice do cache e o lock de deduplicação (D7).

`export_id` é um UUID gerado no primeiro disparo; num cache hit ou numa exportação em andamento é o mesmo `export_id` já existente que volta pro cliente.

TTLs (derivados, não escolhidos arbitrariamente):
- registro `completed` e ponteiro de conteúdo: **6 dias, contados da conclusão** — margem de 1 dia abaixo dos 7 dias da lifecycle do S3, pra que um ponteiro vivo nunca aponte pra objeto já expirado (a lifecycle do S3 arredonda pra cima, nunca expira antes).
- registro `failed`: curto (ordem de 1 hora), só pro cliente descobrir a falha; o ponteiro de conteúdo é apagado no mesmo momento, liberando nova tentativa.
- registro/ponteiro `pending`: **900 s (confirmado pelo usuário)**, aplicado no disparo (cobre a espera na fila do RabbitMQ) e **renovado no início da task** (cobre a execução) — sem a renovação, uma task que esperasse na fila mais que o TTL acordaria sem registro. Se ao iniciar o registro já não existir, a task encerra sem gerar nada. Também é a rede de proteção se o worker morrer no meio da task (sem ele, o ponteiro ficaria travado em `pending`). O valor deriva do pior caso de resiliência (Open Question 2).

`CELERY_RESULT_EXPIRES` deixa de importar pro status de exportação (o status não vem mais do result backend).

- **Alternativa descartada**: `AsyncResult` do Celery como fonte de status (versão original desta change) — pelos dois motivos acima.
- **Alternativa descartada**: entidade `ExportSession` persistida no Mongo, análoga à `GenerationSession`. Rejeitada por ora — o registro Redis com TTL resolve posse + cache sem coleção nova, e não há requisito de histórico de exportações. Se "ver minhas últimas exportações" virar requisito, é o sinal pra revisitar.
- **Trade-off aceito**: perda do Redis (restart sem persistência) apaga registros — as exportações em andamento viram `404` e as concluídas viram cache miss (o objeto no S3 continua lá até a lifecycle). O `.apkg` é regenerável; nenhum dado de produto se perde.

### D6 — Isolamento multi-tenant via o registro Redis

`GET /api/v1/decks/export/{export_id}/status/` busca `export:by-id:{export_id}` e compara `owner_id` do registro com `request.user.id`. **`404` em três casos indistinguíveis pro cliente**: id inexistente, id expirado, id de outro tenant — sem vazar existência (critério de aceite 1) e dando ao frontend um estado terminal claro em vez de polling infinito. Como o `owner_id` é gravado no disparo, a checagem funciona também em `pending`.

O cache (D7) é escopado por `owner_id` na própria chave — nunca há reaproveitamento de objeto entre tenants.

### D7 — Cache de exportação por hash do conteúdo

Regra: **não regenerar (nem chamar o `document-generator`) um `.apkg` cujo conteúdo não mudou.**

- **Versão do conteúdo = hash, não contador.** `content_hash = sha256` de um JSON canônico (`sort_keys`, separadores fixos, `ensure_ascii=False`) contendo: `EXPORT_FORMAT_VERSION` (constante no código — muda quando o template/gerador muda, invalidando exportações antigas), `deck_title`, e a lista de cards **ativos** (sem `deleted_at`) em ordem determinística (ex.: `created_at`, depois `id`), cada um com `id`, `front`, `back`, `front_description`, `back_description` (o domínio `Card` não tem `notes`, então não é enviado).
  - O estado FSRS **não** entra no hash — uma revisão de estudo (`POST /cards/{id}/review/`, que reescreve o card via o mesmo `card_repo.update` do `PATCH`) não invalida o cache.
  - Um contador de versão no `Deck` foi **descartado**: exigiria que todo caminho de escrita (insert/replace/update/cascade/purge de card, `migrate_card_fields`, `seed_decks`, o agente de IA da Sprint 13) lembrasse de incrementar — um caminho esquecido gera exportação desatualizada sem erro visível — e um bump ingênuo em `CardRepository.update` seria disparado por toda revisão de estudo. O hash é derivado do que de fato vai no arquivo, então não pode divergir dele. Sem mudança de schema em `Deck`/`Card`.
- **`POST /api/v1/decks/{deck_id}/export/`** (fluxo, nesta ordem):
  1. valida posse do deck (`404` se não for do usuário);
  2. carrega os cards ativos; `0` cards ou mais que `EXPORT_MAX_CARDS` (100, D9) → `400`;
  3. monta o payload e calcula `content_hash`;
  4. cria `export:by-id:{novo_uuid}` (`pending`) e tenta `SET NX` em `export:by-content:{owner}:{deck}:{hash}` → `novo_uuid`;
     - **`SET NX` conseguiu (miss)** → enfileira a task e responde **`202`** com `export_id`;
     - **já existe e o registro está `completed` (hit)** → apaga o `by-id` órfão e responde **`200`** com o `export_id` existente (já `completed`) — sem task, sem chamada ao `document-generator`;
     - **já existe e está `pending` (em andamento)** → responde **`202`** com o mesmo `export_id` existente — dois cliques seguidos não geram duas gerações.
- **A task recebe o snapshot** — `(export_id, owner_id, deck_id, content_hash, payload)` como argumentos da mensagem (≤100 cards, tamanho seguro pro broker). Ela **não relê o Mongo**: se o deck fosse editado entre o `POST` e a execução, reler faria o arquivo gerado divergir do hash sob o qual é guardado. O snapshot garante que "o que está no S3 sob esse hash é exatamente o que o hash descreve".
- A task, ao concluir: `put_object` na chave `exports/{owner}/{deck}/{hash}.apkg`, marca o registro `completed` com `s3_key` e (re)aplica os TTLs de 6 dias. Na falha: marca `failed` e apaga o ponteiro de conteúdo.
- **Cache hit não faz nenhuma chamada ao S3** nem ao `document-generator`; só lê Redis e (no status) assina a URL localmente.

### D8 — IDs estáveis no `.apkg` (deck, modelo, notas) — decisão do usuário

Hoje `generator.py` gera `model_id`/`deck_id` com `uuid4` a cada chamada, então cada exportação cria um deck e um note type novos no Anki — reimportar depois de editar duplica tudo. Decidido: IDs estáveis.

- O `POST /decks/export` do `document-generator` passa a receber `deck_id` (UUID do deck) e `id` (UUID) por card — **mudança de contrato**, com Django como único chamador (campos obrigatórios; o teste `test_card_model_contract.py` é atualizado).
- `genanki` `deck_id`: inteiro derivado deterministicamente do UUID do deck (ex.: 63 bits de um sha256). `model_id`: **constante fixa no código** (o template é fixo); muda junto com `EXPORT_FORMAT_VERSION` se o template/campos mudarem. `guid` da nota: `genanki.guid_for(card_id)`.
- Resultado: qualquer versão do mesmo deck (qualquer `content_hash`) reimporta **atualizando** o deck e as notas existentes no Anki. O hash é só a chave de cache; **não** entra nos IDs do Anki.
- Nome do arquivo de áudio determinístico (hash do texto do `front`, com deduplicação na lista de mídia) em vez de `uuid4` — reimportar não empilha arquivos de mídia órfãos.

### D9 — Limite de 100 cards por exportação — decisão do usuário

`EXPORT_MAX_CARDS = 100`, validado no `POST` (D7 passo 2) contando só cards ativos, `400` com mensagem clara acima disso ou com deck vazio (recusar cedo, antes do `202`, em vez de descobrir dentro da task). O `document-generator` reforça o mesmo teto (defesa em profundidade) e o `max_cards_per_generation = 10` morto de `app/config.py` — nunca usado, enganoso — é removido/alinhado.

Motivo: cada card é uma chamada de rede sequencial ao gTTS; sem teto a duração é ilimitada, estourando timeout de HTTP, o TTL do lock `pending` e multiplicando o custo de cada retry. Um deck com mais de 100 cards não é exportável nesta sprint — se virar demanda, é um gap novo (ex.: exportação em lotes ou áudio cacheado).

### D10 — Endurecimento do `document-generator` (bug de isolamento + bloqueio)

Duas correções necessárias ao fluxo, encontradas lendo `generator.py`/`routes/decks.py` — incluídas nesta sprint por serem pré-requisito de exportar com segurança, não escopo novo de produto:

- **Colisão entre tenants (critério de aceite 1)**: o `.apkg` é gravado em `{titulo}_{data}.apkg` num diretório compartilhado. Dois usuários com decks de mesmo título, exportando ao mesmo tempo, sobrescrevem o arquivo um do outro — um deles poderia receber o deck do outro. Passa a usar um diretório de trabalho único por requisição, apagado após a resposta ser enviada (o que também elimina o acúmulo indefinido de áudios/`.apkg` no volume `document_generator_audio`).
- **Event loop bloqueado**: a rota é `async def` chamando código síncrono (gTTS + genanki), travando o processo inteiro (inclusive `/health`) durante a geração. Passa a rodar fora do event loop (rota `def` ou `run_in_threadpool`).

## Risks / Trade-offs

- **Vazamento de credencial AWS**: se o `.env` do Django/Celery vazar, a policy restrita (D2) limita o dano a esse bucket específico → least privilege já embutido, reforçado pela rotina de segredos fora do git.
- **Worker morrer no meio da task**: o registro `pending` fica órfão até o TTL de segurança (D5), então o cliente vê `pending` por um tempo e depois `404`; o frontend futuro precisa de timeout no polling → aceito, registrado como requisito da sprint de UI.
- **Perda do Redis**: ver trade-off em D5 — aceito, `.apkg` é regenerável.
- **Estado do breaker compartilhado no Redis**: decidido usar `CircuitRedisStorage` (o worker Celery é prefork e o tráfego esporádico — contadores por processo dificilmente chegariam a `fail_max` em algum deles, então o breaker praticamente nunca abriria). Consequência: o breaker passa a depender do Redis; se o Redis cair, o `pybreaker` precisa de um estado de fallback definido (`fallback_circuit_state`) — a confirmar no teste 6.5, junto do requisito do cliente Redis (`decode_responses`) da versão instalada.
- **AWS antecipada**: a sprint passa a depender de uma conta AWS e um bucket reais (inclusive pra validar o critério de aceite 7) → aceito pelo usuário (D2); estratégia de dev/CI sem AWS decidida (`moto` nos testes + S3 local no compose, ver D2).
- **Regressão de cache silenciosa**: se alguém adicionar um campo exportável ao payload e esquecer de incluí-lo no hash, exportações antigas ficam desatualizadas sem erro → mitigação: o hash é calculado sobre o **mesmo objeto de payload** enviado ao `document-generator` (um único builder), coberto por teste que compara os campos do payload com os do hash.

## Open Questions

- **1. PDF — RESOLVIDA: `reportlab`** (Python puro, sem libs de sistema extras no Dockerfile) **e payload de seções confirmado pelo usuário ("sua proposta será utilizada", 2026-09-26)**: `title`, `subtitle` opcional e `sections` com `type` ∈ {`heading`, `paragraph`, `bullet_list`, `table`, `bar_chart`}. Ficam **de fora nesta sprint**: `image` (PNG base64) e `line_chart` — entram quando a Sprint 15 (relatório semanal) provar que precisam; o `bar_chart` é desenhado pelo próprio `reportlab` (vetorial), então o payload leva só os números e não depende de imagem renderizada no navegador.
- **2. Calibragem de resiliência (2.2/2.4) — TODOS OS VALORES CONFIRMADOS pelo usuário em 2026-09-26.** **Decidido**: timeout de leitura da exportação de **300 s** (separado do das demais chamadas, D3); **2 tentativas** no total, retentando timeout de leitura, erro de conexão e 5xx (4xx nunca); estado do breaker **compartilhado entre processos via Redis** (`CircuitRedisStorage`). **Confirmado (proposta do modelo aceita pelo usuário)**: timeout de conexão 5 s; backoff exponencial com jitter (inicial 5 s, máx 30 s); `fail_max = 3`; `reset_timeout = 120 s`; um breaker por serviço-alvo (`document-generator`), compartilhado entre exportação e PDF, cada um com o seu timeout; task Celery com `soft_time_limit = 660 s` / `time_limit = 720 s`; TTL do `pending` de 900 s, renovado no início da task. Derivação: pior caso de uma exportação = 2 × 300 s + ~6 s de backoff ≈ **606 s**; `soft_time_limit` (660) e `time_limit` (720) ficam acima dele, e o TTL do `pending` (900) acima do `time_limit`, pra que o registro nunca expire enquanto a task ainda pode estar rodando. `fail_max` baixo porque uma falha lenta é cara (até ~10 min de um processo do worker); `reset_timeout` de 120 s porque uma tentativa de recuperação (meio-aberto) pode custar minutos se o serviço ainda estiver travado. Com 2 tentativas o backoff tem um único degrau — a natureza exponencial fica na configuração do wrapper (e é testável com mais tentativas), mas na exportação só se observa uma espera.
  - **Medição realizada (2026-09-26, máquina de desenvolvimento, sem Docker, chamando `generate_deck_package` real com gTTS de verdade, 100 cards, execução sequencial)**: com `front` médio de 53 caracteres → **81 s** no total (gTTS por card: média 0,81 s, p95 1,22 s, máx 1,28 s); com `front` de 100 caracteres (pior caso do teto do agente de IA) → **114 s** (média 1,14 s por card, p95 1,35 s, máx 1,45 s). O gTTS responde por >99,9% do tempo (o resto — genanki + empacotamento — foi ~0,1 s). O `.apkg` de 100 cards pesa 3 a 5 MB. Cada card custa ≈ 0,6–1,5 s e o custo cresce com o tamanho do texto. **Limitações**: uma máquina/rede só, sem concorrência, fora da VPS — reavaliar no deploy real (a setting é configurável, então reajustar é barato).
- **3. S3 em dev/CI — RESOLVIDA (decisão do usuário): `moto` nos testes e `moto` em modo servidor no compose (só dev; era MinIO, indisponível)**, ver D2.

**Regra de processo**: estas decisões ficaram deliberadamente em aberto (o que já foi resolvido está marcado acima; não sobra nenhuma decisão aberta) — de propósito fora da spec, porque são parâmetro/formato/infra de teste, não comportamento testável. Isso significa que **não têm default implícito**: ao retomar esta sprint (nesta sessão ou numa futura), antes de codar a tarefa 5.2 (formato do payload do PDF), ou as tarefas 2.2/2.4 (números do circuit breaker/retry/timeout), o modelo DEVE resolver a decisão pendente com o usuário primeiro — nunca escolher o formato de seções, valores de `fail_max`/`reset_timeout`/timeout silenciosamente só para destravar a implementação. Risco concreto de pular isso: entregar a Sprint 11 com uma escolha que nunca foi de fato decidida, só preenchida por conveniência — o tipo de gap que a seção "Pontos de Refinamento Futuro" do `PRD.md` existe pra evitar.
