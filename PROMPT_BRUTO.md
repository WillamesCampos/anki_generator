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

# TAREFA

Gere o PRD desse projeto (Product Requirement Document), em formato de arquivo
markdown. O PRD será usado como guia do projeto posteriormente no
desenvolvimento do sistema. Coloque todos os detalhes necessários para o
desenvolvimento tanto técnico quanto de planejamento.
Adicione no PRD uma sessão com as sprints de implementações/desenvolvimento
do sistema, com tarefas pequenas e bem detalhadas, seguindo uma ordem lógica
de desenvolvimento. As sprints e tarefas devem ter o espaço " " para marcação
de "X" quando concluídas, em forma de checklist/to-do.
