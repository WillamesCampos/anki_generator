# Design — Padronização global de cards e gráficos de classificação

Data: 2026-09-16
Status: aprovado

## Objetivo

Transformar o estilo visual já validado na Home em uma fundação reutilizável para toda a aplicação. Todos os componentes `Card` devem compartilhar a mesma superfície branca, contorno preto e sombra preta; os gráficos de classificação da Home e do detalhe do deck devem compartilhar estrutura, configuração, acessibilidade e responsividade.

Não há mudança de API, regra de negócio, navegação, persistência, carregamento, tratamento de erro ou ações existentes.

## Decisão de arquitetura

A padronização será feita em duas unidades globais:

1. `Card` continuará sendo o componente de superfície genérico, mas `Card.css` passará a conter o padrão visual oficial.
2. Um novo `RatingDistributionChart` concentrará toda a apresentação dos quatro resultados de revisão e será consumido pela Home e por `DeckDetailPage`.

Estilos locais permanecerão somente quando expressarem composição específica de uma tela. Não serão criadas variantes de card nesta etapa, porque o usuário aprovou o mesmo padrão para listas, formulários, estados vazios, diálogos, resumo da Home, detalhe do deck e sessão de estudo.

## Card global

Todo `.ui-card` terá:

- fundo `var(--color-white)`;
- borda `2px solid var(--color-text-primary)`;
- sombra sólida `4px 4px 0 var(--color-text-primary)`;
- raio `var(--radius-card)`;
- padding `var(--space-md)` em telas regulares;
- padding `var(--space-sm)` em até `640px`.

Todo `.ui-card__title` terá:

- layout flexível para alinhar marcador e texto;
- marcador circular laranja de `10px` via `::before`;
- cor primária, tamanho `var(--font-size-lg)` e peso `700`;
- quebra de texto permitida sem comprimir ou deformar o marcador.

O card não terá hover, transformação ou animação global. Essa ausência é intencional: o mesmo componente envolve conteúdo informativo, formulários e diálogos, portanto não deve sugerir clique quando não é interativo.

O corpo mantém `var(--color-text-secondary)` como padrão. Telas que precisam de conteúdo primário ou alinhamento central continuam podendo sobrescrever apenas essas propriedades localmente.

## Migração dos cards existentes

O novo estilo global alcança automaticamente:

- cards de resumo e estatísticas da Home;
- cards da listagem, criação, detalhe e gerenciamento de decks/cards;
- estados vazios;
- formulário dentro do detalhe do deck;
- `ConfirmDialog`;
- `ErrorBoundary`;
- sessão de estudo.

Regras locais duplicadas de fundo, borda, sombra, título e marcador serão removidas da Home e da sessão de estudo. Regras estruturais permanecem, por exemplo:

- altura igual dos cards no grid de resumo da Home;
- conteúdo centralizado na sessão de estudo;
- sombra e cores próprias dos botões de avaliação;
- tamanhos e espaçamentos específicos de cada página.

A sombra laranja externa da sessão de estudo deixa de existir. O laranja permanece nos elementos internos de destaque e as quatro cores semânticas permanecem nos botões `again`, `hard`, `good` e `easy`.

## Componente `RatingDistributionChart`

Será criado em `frontend/src/components/charts/RatingDistributionChart.jsx`, com CSS dedicado no mesmo diretório. O componente terá a seguinte interface:

- `distribution`: objeto com as chaves opcionais `again`, `hard`, `good` e `easy`; valores ausentes viram zero;
- `ariaLabel`: nome acessível do gráfico;
- `summaryId`: identificador único da lista textual associada;
- `datasetLabel`: rótulo interno do dataset para o Chart.js;
- `chartRef`: referência opcional usada pela Home na exportação PDF.

O componente fixa a ordem e os rótulos:

| Chave | Rótulo |
|---|---|
| `again` | Errou |
| `hard` | Difícil |
| `good` | Bom |
| `easy` | Fácil |

Ele também concentra o registro do Chart.js e a configuração visual:

- fundo laranja;
- borda preta de 2 px;
- hover escuro com borda laranja;
- cantos com o raio de card tokenizado;
- espessura máxima consistente;
- eixo X sem grade;
- eixo Y iniciado em zero e limitado a valores inteiros;
- tooltip escuro, borda laranja e tipografia do produto;
- legenda visual do Chart.js ocultada;
- animação desabilitada quando `prefers-reduced-motion: reduce` estiver ativo.

## Resumo textual e acessibilidade

O canvas recebe `aria-describedby={summaryId}`. A lista correspondente usa `id={summaryId}` e `aria-label="Resumo das classificações"`.

Cada item mostra rótulo e valor em um bloco branco com borda neutra e destaque lateral laranja. O layout usa quatro colunas em largura regular e duas colunas em até `640px`. A lista torna os dados disponíveis sem depender do canvas, cor ou tooltip.

`ariaLabel` e `summaryId` são obrigatórios para impedir nomes duplicados quando mais de um gráfico existir no mesmo documento. `chartRef` é opcional porque somente a Home exporta PDF.

## Integração com as páginas

### Home

A Home continua buscando a estatística do último deck e mantendo seus estados de carregamento e erro. Ela passa `rating_distribution`, `ariaLabel="Distribuição das classificações da Home"`, `summaryId="home-rating-summary"`, seu rótulo de dataset e `chartRef` ao componente compartilhado.

O botão “Exportar PDF” e `exportChartToPdf` não mudam.

### Detalhe do deck

O detalhe continua buscando `fetchDeckStatistics(deckId)` e mantendo o erro isolado das demais informações do deck. Ele passa `ratingDistribution`, `ariaLabel="Distribuição das classificações do deck"`, `summaryId="deck-rating-summary"` e seu rótulo de dataset.

Não haverá botão de exportação no detalhe.

## CSS e remoção de duplicação

`HomePage.css` deixará de definir borda, sombra, tipografia e marcador do `Card`, mantendo somente grid, composição da meta, CTA e ações da Home.

`StudySessionPage.css` deixará de definir fundo, borda e sombra do card. Permanecem centralização, hierarquia da resposta, progresso e botões semânticos.

`DeckDetailPage.css` deixará de possuir estrutura própria para o gráfico e a lista de valores; essas regras serão substituídas pelas classes de `RatingDistributionChart.css`.

Não serão usados seletores globais fora de `Card.css`, nem cores literais fora dos arquivos de tokens.

## Estados e erros

O componente compartilhado recebe somente dados já resolvidos e não executa requests. Por isso:

- loading continua sob responsabilidade da página;
- erros continuam sob responsabilidade da página;
- distribuições ausentes ou parciais são normalizadas para zero;
- uma distribuição totalmente zerada ainda renderiza gráfico e resumo com quatro zeros;
- falha nas estatísticas do detalhe não bloqueia informações, edição ou navegação do deck;
- falha nas estatísticas da Home não remove o card do último deck nem o CTA.

## Responsividade e movimento

- Cards reduzem o padding global em até `640px`.
- O gráfico mantém altura fluida definida pelo componente: maior no desktop e menor em tablet/celular.
- O resumo usa quatro colunas no desktop e duas no celular, sem overflow a partir de 320px.
- Títulos podem quebrar linha sem deslocar o marcador.
- A configuração do Chart.js desabilita animação sob movimento reduzido.
- Nenhuma nova transição será adicionada ao `Card`.

## Testes e verificação

### Card

- teste de contrato do CSS global para fundo, borda e sombra;
- teste do título e do marcador global;
- teste do padding móvel;
- remoção ou adaptação do teste da Home que hoje exige a sombra dentro de `HomePage.css`.

### Gráfico compartilhado

- normalização e ordem de `again`, `hard`, `good`, `easy`;
- configuração tokenizada observável do dataset, eixos e tooltip;
- associação entre canvas e resumo textual;
- encaminhamento opcional de `chartRef`;
- movimento reduzido;
- distribuição parcial e totalmente zerada.

### Páginas

- Home mantém dados, exportação, loading e erro;
- detalhe mantém dados, loading, erro isolado e demais ações;
- nenhuma chamada de API ou contrato de rota muda.

### Gates

- testes focados dos componentes e páginas;
- suíte completa do frontend;
- ESLint;
- build Vite;
- `git diff --check`;
- auditoria de cores hardcoded;
- inspeção visual em 320px, 1024px e desktop.

## Fora de escopo

- criar variantes interativas, elevadas ou sem sombra para `Card`;
- redesenhar `Button`, `Input`, formulários ou diálogos além do efeito herdado do card global;
- alterar dados, APIs, endpoints ou regras de revisão;
- adicionar exportação PDF ao detalhe do deck;
- introduzir outra biblioteca de gráficos.
