Desejo criar um sistema que se assemelha ao anki. Um aplicativo de flashcards, mas com integração com IA para feedback e sugestão de novos cards para o deck. Gostaria que tivesse notificação enviando msg pelo whatsapp como lembrete, meta de tempo. a cada semana, um relatório de desempenho é enviado por e-mail no formato pdf com base nas estatísticas do estudo e um pequeno feedback de evolução.

A página de home do aplicativo vai mostrar o último deck estudado, a meta proposta e quanto dela foi alcançada e feedback do dia. Também vai trazer um gráfico com base nas estatísticas de cards estudados, quantos acertou, quantos errou. Vai ter a funcionalidade de exportar esse gráfico para um pdf.
Funççao de exportar um deck via extensão do anki.

# tech specs do sistema

O sistema será desenvolvido usando django com django rest framework para gerenciar login, autenticação do usuário, consultar as principais estatísticas desse usuário. A aplicação será multi tenant, com filtros e permissões adequados para não vazar informação para outros usuários. Será utilizado os models de Permissão e Grupos do django, criando a lógica a partir deles. Haverá versionamento das urls. A integração com IA será através do uso de langchain e langgraph. A aplicação nao vai travar o fluxo da request, por isso será utilizado celery + redis. Usaremos cache para pegar o token de autenticação sem estar expirado. Também vamos implementar autenticação via google. Usaremos a evolution API para integrar whatsapp.

Os microserviços a serem desenvolvidos utilizando fast api são: a aplicação que integra com a evolution api, um gerador de documentos, a aplicação de gráficos ( a definir se será plotly ou outra solução python ou usando react no frontend.). Será desenvolvida lógica de circuit breaker na aplicação django quanto a integrar com cada microserviço.

Os dados de deck, cards e estatísticas gerais serão persistidas via mongo db.

Usaremos filas para gerenciar eventos, com lógica de retry, dlq.

# arquitetura

## django

A app principal se chamará core. Todas as apps a serem desenvolvidas ficarão dentro de uma pasta chamada apps. arquivos docker e docker-compose ficarão na raiz do projeto. Implementação de rate limiting (taxa a definir) e circuit breaker com retry exponencial. Publicação de eventos na fila de forma assíncrona utilizando celery + rabbitMq caso a fila seja com essa tecnologia também. A aplicação terá serializers "magros" que podem ser herdados sem trazer boilerplate desnecessário. Uso preferencial por generic views do django rest framework. Criação da entidade usuário será aproveitado do model do django com a adição do email como chave única. Haverá um model de auditoria com campos created_at, created_by, updated_at, updated_by que sao opcionais, mas nos serializers vai capturar da reqquest e preencher.

Separaremos arquivos de configuração para ambiente local e ambiente de produção.
Será criado um arquivo .env na raiz do projeto onde imediatamente será trazido do settings do django o secret key e armazenará no env na chave "DJANGO_SECRET_KEY". Usaremos o python-dotenv para gerenciar as variáveis de ambiente. O loaddotenv será carregado quando a aplicaçao django iniciar, assim asseguramos as variáveis atualizadas no aplicativo.

## mensageria

As aplicaçoes fast api atuarão como receivers de uma fila através do rabbitmq ou apache kafka - a definir, com lógica de dlq.

Serão aplicaçoes fast api: integração com evolution API, agentes de IA via langchain/langgraph, gerador de documentos. Todos os projetos respeitarão o padrão MVC.

## frontend

Pagina home com informação do último deck, meta e gráfico.
Um menu lateral com acesso aos decks, categorias cadastradas, gerar relatórios e chat com agente de IA. Será uma SPA.Decidindo se hospedo na AWS S3 com react ou faço utilizando django templates.

## agente de IA

Poderá fornecer feedbacks diários na home da página, de acordo com resultados do deck estudado. Apontar melhorias e sugerir novas entradas num deck ou criar um deck novo.

Cada ação dessa resultará em integrar com as rotas do projeto que dão acesso e criação dos recursos com um tipo de permissão especial. Quando um dado for criado via agente, a informação do created_by, updated_by será "ai_agent_machine".

O agente de IA apenas vai responder perguntas dentro do contexto de criaçao de cards e sugestao de novos cards e feedbacks de acordo com os resultados. Qualquer coisa fora do contexto ou que use o contexto de maneira indevida para gerar respostas que nao tenham a ver com o objetivo do projeto com uso de flashcards, serão obrigatoriamente ignorados.
Exemplo de contexto inadequado: Me dê a receita de bolo de cenoura. Geração de cards com texto longo serao ignorados. Maximo de 100 caracteres.

Exemplo de contexto adequado: Eu gostaria de adicionar 20 novas palavras para o meu deck de "Aprender Francês"

Exemplo de contexto usado de forma inadequada: Eu gostaria de adicionar 20 novas palavras para o meu deck de "Receitas" e você vai me dar a receita de 20 bolos diferentes.

## banco de dados

Usaremos índices adequados com base no deck, na categoria e na tag que relaciona o deck/card.

## docker

Não usaremos usuário root nos containers, criar um user com o nome do projeto com as permissões necessárias. Iniciar com script entrypoint.

Todas as aplicações estarão em um único repo, para facilitar o entendimento e contexto para agentes de IA.

## agents.md

O código será estritamente e obrigatoriamente adequado a PEP-8. Criação de comandos makefile para facilitar comandos, como rodar migraçoes do django ou iniciar containers por exemplo.

Usaremos black e pre-commit para poder facilitar o gerenciamento da pep.
Usaremos poetry como gerenciador de ambiente no projeto django, venv nos demais.

Adicionaremos a cada ajuste uma entrada num arquivo de changelog.
criaremos fluxo de deploy baseado em tags via github actions.

- O sistema deve ser responsivo e funcionar corretamente em dispositivos de
  todos os tamanhos e dimensões de telas.
- O sistema deve ser seguro, não expor dados sensíveis, rotas fechadas e ter um
  sistema de permissões e filtros para o multi tenant que garanta a segurança dos
  dados, incluindo permissões de arquivos e anexos de media do sistema, que devem
  ficar visíveis apenas para os usuários com permissões nesses arquivos e não
  ficar expostos.
- UI/UX excelente, com base no design system do projeto, pensada sempre na
  fluidez das jornadas do usuário. Bom contraste entre elementos e fontes, e fundo
  das telas.
- A experiência do usuário ao disparar tasks em segundo plano (resumos de IA,
  por exemplo) deve ser um loading no botão e um aviso de que será notificado
  quando a análise ficar pronta. Não deve ser bloqueante de maneira alguma.
  Quando a task em segundo plano finalizar, o usuário deve receber uma notificação
  na interface.
- Ótimo desempenho de filtros, telas e processos. Nada bloqueante.
- Um django command que faz uma carga inicial de dados fakes no sistema,
  cobrindo múltiplos cenários e use cases, com diversas datas diferentes,
  visando fazer demonstrações do sistema.
- O design system estará referenciado no arquivo
  @design_system/design-system.html do projeto. Todo design do sistema, cores,
  componentes e tipografias devem sempre respeitar rigorosamente o design system
  definido.

# Novas Ideias

- Vamos configurar o django-admin e o django-debug-toolbar. Também tem um
  pacote pra ver as coisas do Celery no admin do Django, mas não lembro o
  nome agora.
- Também temos que colocar um swagger no Django, igual o document-generator
  (FastAPI) já tem em /docs.
- Adicionar .dockerignore (Django e cada microsserviço).
- Nova sprint (depois da Sprint 3 de frontend, empurrando as demais pra
  baixo): dropdown acima do gráfico de barras da Home pra selecionar entre
  os decks do usuário — o gráfico passa a mostrar as estatísticas daquele
  deck específico, não tudo junto.
- Confirmar se "cards do deck já estudados/vistos hoje" está sendo
  persistido. Se não, pensar num campo no deck pra isso, que é zerado
  todo dia pra todos os decks (a estatística reinicia diariamente).
- Separar visualmente o bloco de cima (último deck estudado + meta de
  estudo, lado a lado) do card de Estatísticas (gráfico + exportar PDF) —
  padding entre as bordas, bordas mais grossas.
- Melhorar os dados que alimentam o gráfico de estatísticas — criar uma
  rota dedicada no backend: `decks/{deck_id}/statistics`.
- Respostas sobre os pontos em aberto da ideia acima:
  1. A rota `decks/{deck_id}/statistics` traz, por enquanto: distribuição
     por rating (again/hard/good/easy) + quantidade revisada hoje. Só
     isso mesmo por ora, pode crescer depois.
  2. O cálculo é feito direto no Mongo (agregação), não trazendo tudo pra
     API e somando em Python.
  3. Sem nenhum deck selecionado no dropdown, mostra o deck mais recente
     estudado — igual já funciona hoje em "Último deck estudado" (nome +
     descrição). Quando o dropdown é usado pra selecionar um deck
     manualmente, o título do card muda de "Último deck estudado" para
     "Deck estudado".
- Implementar OWASP de segurança no projeto (a definir quais itens do
  Top 10 / ASVS entram, e em que sprint) — ainda precisa de refinamento,
  levantar o que já está coberto (multi-tenant, rate limiting, segredos
  fora do código) vs. o que falta antes de virar sprint.
- Cadastro de cards em lote via planilha — Google Sheets ou upload de
  arquivo. O usuário deve poder cadastrar decks, cards, categorias e tags
  numa única planilha. Se a planilha trouxer só cards, todos os campos
  obrigatórios do card devem estar presentes, junto com o deck
  relacionado: se o deck já existir, os cards são adicionados a ele; se
  não existir, lança erro (não cria deck implicitamente nesse fluxo). Se
  a ideia for criar deck a partir do arquivo, o deck tem que ser
  informado na planilha. Categorias e tags podem ser incluídas — se forem
  opcionais no modelo de dados, tudo bem ficarem de fora, mas se forem
  obrigatórias precisam ser tratadas/validadas no processamento da
  planilha. Ainda precisa de refinamento: formato exato da planilha
  (template?), validação linha a linha vs. tudo ou nada, feedback de erro
  pro usuário (quais linhas falharam e por quê).
- Adicionar campo "objetivo" no Deck, pra servir de contexto pra um
  agente de IA (ex.: "revisar conceitos de anatomia pra prova"). No
  frontend, ter uma opção de "refinar objetivo com IA" — o usuário
  escreve um objetivo cru e a IA melhora o texto pra ficar um contexto
  mais útil pro agente. Ainda precisa de refinamento: onde esse campo
  aparece na UI, se é obrigatório, como o refino via IA se encaixa no
  fluxo de criação/edição do deck.
- Sugestão de deck a partir de um link de vídeo: o usuário manda um link
  de vídeo + uma mensagem dizendo o que quer (ex.: "esse vídeo fala de
  anatomia, quero revisar os conceitos"). O sistema processa o vídeo,
  extrai o áudio, transcreve, identifica as palavras/termos de maior peso
  no conteúdo e sugere um deck (com cards) baseado nisso. Se o usuário
  confirmar a sugestão, o deck é criado de fato. Ainda precisa de
  refinamento: quem faz a transcrição (serviço externo? modelo local?),
  como extrair "peso" dos termos, se isso vira mais uma responsabilidade
  do agente de IA existente ou um fluxo/microsserviço novo, custo de
  processar vídeo.
- Assistente de consulta read-only sobre decks/cards, via tool calling —
  ideia levantada com o `backend-mentor` como prática de backend+IA antes
  da Sprint 12 (Agente de IA completo, LangChain/LangGraph). Endpoint
  novo e desacoplado (ex.: `POST /api/v1/ai/ask/`) que recebe uma
  pergunta em linguagem natural (ex.: "quantos cards tenho pra revisar no
  deck de Francês?") e responde chamando a API do LLM diretamente (sem
  framework, mesmo padrão do flix-api), com 2-3 tools mínimas que só
  leem dados já expostos hoje (listar decks, contar cards devidos por
  deck, etc.) — sem tocar em nenhum fluxo de escrita. Objetivo é fechar o
  gap de tool calling (nunca implementado, só teoria) com baixo risco,
  antes de partir pro agente completo com permissão de escrita. Ainda
  precisa de refinamento: provedor/SDK (OpenAI, já usado no flix-api, ou
  Anthropic), onde esse endpoint mora (Django direto ou um microsserviço
  novo), quais tools exatamente entram no escopo mínimo.
- Logging estruturado + correlation ID atravessando Django → task Celery
  → microsserviço FastAPI — ideia levantada com o `backend-mentor`. Hoje
  não existe nada disso no projeto (cada serviço loga isolado, sem jeito
  de seguir uma requisição de ponta a ponta). Um ID gerado na entrada da
  requisição, propagado no header/contexto da task, sem precisar de
  tracing completo (OpenTelemetry). Serve de base pra Sprint 16
  (observabilidade/Grafana) — sem isso, os dashboards não conseguem
  responder "essa falha veio de onde". Ainda precisa de refinamento: qual
  lib (structlog?), onde o ID é gerado/propagado exatamente, em que
  sprint entra (antes da 16, ou como parte dela).
- Testes de contrato entre Django e os microsserviços FastAPI — ideia
  levantada com o `backend-mentor`. Hoje a integração com
  `document-generator` (e futuramente o agente de IA) só é validada
  manualmente ou via teste de integração pesado. Um schema compartilhado
  (Pydantic ou JSON schema) validado nos dois lados pegaria quebra de
  payload sem precisar subir os dois serviços — sem ir até um framework
  de contract testing dedicado (Pact), que seria overkill pro tamanho do
  projeto. Ainda precisa de refinamento: como compartilhar o schema entre
  Django e FastAPI (pacote comum? duplicado com teste de igualdade?), em
  que sprint entra.
- Estratégia de backup/restore de Mongo + Postgres — ideia levantada com
  o `backend-mentor`, mais devops que código. Faz mais sentido perto da
  Sprint 15 (deploy real na VPS), antes disso não há produção de verdade
  pra proteger. Ainda precisa de refinamento: frequência, retenção, onde
  o backup fica armazenado, teste de restore de verdade (não só o
  backup rodar sem erro).
- Guardrail de custo pra chamada de LLM — ideia levantada com o
  `backend-mentor`, complementar ao assistente de tool calling já
  registrado acima. Reaproveitar o Redis já usado pra cache de token:
  cachear pergunta idêntica (evita pagar de novo pela mesma resposta) e
  um contador de orçamento diário por usuário. Ainda precisa de
  refinamento: TTL do cache de resposta, o que acontece quando o usuário
  estoura o orçamento diário (bloqueia? avisa?), se isso é genérico pra
  qualquer feature de IA ou específico do assistente de consulta.
- Harness de avaliação do domínio restrito do agente de IA — ideia
  levantada com o `backend-mentor`. O `PROMPT_BRUTO.md` já define
  exemplos de pergunta válida/inválida pro agente (ex.: pedir receita de
  bolo é fora de escopo, ver seção "agente de IA" acima). Um teste
  automatizado (pytest) que roda um conjunto fixo dessas perguntas contra
  o modelo e verifica se ele recusa o que deveria recusar, antes da
  Sprint 12 chegar e essa restrição só ser validada na mão. Ainda precisa
  de refinamento: conjunto de perguntas de teste, critério de "passou"
  (match exato? outro LLM avaliando a resposta?), roda em CI ou só local.
- Streaming da resposta do LLM via SSE — ideia levantada com o
  `backend-mentor`, extensão natural do assistente de tool calling já
  registrado acima: em vez de esperar a resposta inteira, o Django
  devolve em streaming (`StreamingHttpResponse`), melhorando percepção de
  latência. Fazer só depois do tool calling básico estar funcionando, não
  junto — são dois conceitos novos, melhor um de cada vez. Ainda precisa
  de refinamento: SSE puro ou WebSocket, como o frontend consome o
  streaming.
  - Criar modo noturno no front.

# TAREFA

Gere o PRD desse projeto (Product Requirement Document), em formato de arquivo
markdown. O PRD será usado como guia do projeto posteriormente no
desenvolvimento do sistema. Coloque todos os detalhes necessários para o
desenvolvimento tanto técnico quanto de planejamento.
Adicione no PRD uma sessão com as sprints de implementações/desenvolvimento
do sistema, com tarefas pequenas e bem detalhadas, seguindo uma ordem lógica
de desenvolvimento. As sprints e tarefas devem ter o espaço " " para marcação
de "X" quando concluídas, em forma de checklist/to-do.
