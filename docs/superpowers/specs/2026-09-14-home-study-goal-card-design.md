# Design — Card branco de meta de estudo

Data: 2026-09-14
Status: aprovado

## Objetivo

Transformar o card simples “Meta de estudo” da Home em um painel de progresso branco, legível e coerente com a identidade laranja/preto do produto, sem mudar como a meta ou as revisões são calculadas.

## Direção visual

- Aplicar aos dois cards da grade superior da Home a mesma borda preta de `2px` usada no card de estatísticas. A regra fica limitada a `.home-page__summary-grid` e não altera o componente global `Card`.
- Manter o fundo branco escolhido pelo usuário.
- Dar presença ao card com borda preta de `2px`, cantos existentes de card e sombra sólida laranja deslocada.
- Destacar o título com um pequeno marcador circular laranja, sem alterar o texto “Meta de estudo”.
- Exibir a quantidade revisada e a meta no formato visual `0 / 20`, com o primeiro número maior e mais forte.
- Manter “cards hoje” como legenda curta.
- Exibir o percentual em um badge laranja com texto preto e borda preta.
- Adicionar uma barra horizontal: trilho cinza-claro com borda preta e preenchimento laranja proporcional ao percentual.
- Exibir abaixo da barra uma mensagem curta: `N cards para concluir sua meta` enquanto estiver incompleta; ao atingir 100%, `Meta concluída hoje!`.

## Estrutura e isolamento

`HomePage.jsx` envolve apenas o segundo `Card` da grade com `.home-page__goal-card`. O componente global `Card` não recebe novas props nem alterações. A borda compartilhada usa `.home-page__summary-grid .ui-card`, alcançando somente os dois cards superiores. O conteúdo interno usa classes locais:

- `.home-page__goal-overview` para número e percentual;
- `.home-page__goal-count` e `.home-page__goal-label` para a leitura principal;
- `.home-page__goal-percent` para o badge;
- `.home-page__goal-progress` e `.home-page__goal-progress-fill` para a barra;
- `.home-page__goal-helper` para a mensagem final.

O preenchimento recebe a custom property inline `--goal-progress`, formada a partir de `goalProgress.percentage`, que já é limitado entre `0` e `100` por `computeGoalProgress`.

## Acessibilidade

A barra expõe `role="progressbar"`, `aria-valuemin="0"`, `aria-valuemax="100"`, `aria-valuenow={goalProgress.percentage}` e um `aria-valuetext` no formato `0 de 20 cards revisados hoje`. A barra é apenas informativa e não entra na ordem de foco.

O badge repete visualmente o percentual, mas não substitui os valores textuais. Cores não são a única forma de comunicar progresso.

## Responsividade e movimento

- Número e badge podem quebrar linha sem sobreposição.
- Em até `640px`, o padding interno e os tamanhos permanecem dentro da largura disponível a partir de 320px.
- A barra usa largura fluida e não cria overflow horizontal.
- A mudança do preenchimento respeita `prefers-reduced-motion: reduce`, removendo sua transição.

## Estados e limites

- Com zero revisões, mostra `0 / meta`, `0%` e a meta inteira como restante.
- Com progresso parcial, mostra o restante calculado por `Math.max(goal - reviewedToday, 0)`.
- Com meta atingida ou superada, mostra `100%` e a mensagem de conclusão.
- Meta, histórico, `localStorage`, APIs, conteúdo do card de último deck, CTAs e gráfico permanecem inalterados.
- Nenhum token ou componente global será criado ou modificado.

## Verificação

- Teste inicial: `0 / 20`, `0%`, restante 20 e atributos ARIA da barra.
- Teste parcial: números, percentual e restante usam o resultado real de `computeGoalProgress`.
- Teste concluído: percentual limitado a 100 e mensagem de conclusão.
- Executar testes focados da Home, suíte frontend, lint, build, diff check e inspeção responsiva.
