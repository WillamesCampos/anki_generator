# Design — Enriquecimento visual da sessão de estudos

Data: 2026-09-14
Status: aprovado

## Objetivo

Dar ao card da sessão de estudos a mesma linguagem visual profissional da Home: superfície branca, borda preta, destaque laranja, conteúdo centralizado e ações de avaliação distinguíveis rapidamente por cor. O fluxo de revelar, avaliar, avançar e concluir não muda.

## Superfície e hierarquia

- Todos os cards diretamente renderizados pela sessão — card ativo, estado vazio e conclusão — recebem borda preta de `2px`, cantos existentes e sombra sólida laranja deslocada.
- O card ativo permanece branco.
- Título, resposta, descrições e ações ficam centralizados.
- O título da frente usa tamanho maior e peso forte.
- A resposta revelada ganha destaque tipográfico sem ocultar as descrições frontal e traseira.
- O indicador `Card N de total` vira um badge preto com texto branco e pequeno detalhe laranja, centralizado acima do card.
- O botão `Mostrar resposta` fica centralizado e preserva o texto e o comportamento atuais.

## Avaliações e cores

Cada botão continua enviando exatamente o mesmo valor à API:

- `Errei` → `again` → vermelho `rgb(220, 38, 38)`, texto branco;
- `Difícil` → `hard` → âmbar `rgb(245, 158, 11)`, texto preto;
- `Bom` → `good` → azul `rgb(37, 99, 235)`, texto branco;
- `Fácil` → `easy` → verde `rgb(21, 128, 61)`, texto branco.

As cores são adicionadas a `tokens.css` como `--color-rating-again`, `--color-rating-hard`, `--color-rating-good` e `--color-rating-easy`; `tokens.js` recebe os equivalentes `ratingAgain`, `ratingHard`, `ratingGood` e `ratingEasy`. Isso mantém a paridade existente entre tokens CSS e JavaScript. Nenhum valor semântico fica solto em `StudySessionPage.css`.

Os Buttons preservam `ui-button` e `ui-button--secondary`. `StudySessionPage.jsx` fornece apenas o hook local `data-rating={value}`, evitando o problema conhecido em que um `className` externo substitui as classes internas do componente global.

## Estados de interação

- Todos os quatro botões têm altura mínima de `44px`, cantos de card, borda preta e sombra preta curta.
- `:hover` reduz a sombra e desloca o controle em `2px`.
- `:active` remove a sombra e desloca em `3px`.
- `:focus-visible` usa outline preto de `3px` com afastamento suficiente da borda.
- `:disabled` mantém a cor semântica reconhecível, mas reduz opacidade e remove deslocamentos.
- Em `prefers-reduced-motion: reduce`, transições e transforms são removidos; a sombra permanece como estado estático.

## Layout responsivo

- Em desktop, as quatro avaliações formam uma grade de quatro colunas de largura equivalente.
- Em até `1024px`, a grade usa duas colunas.
- Em até `640px`, usa uma coluna para preservar legibilidade dentro da Sidebar recolhida e do padding do card.
- O card reduz padding localmente em telas estreitas, sem alterar `Card.css`.
- Nenhum texto, botão ou sombra provoca overflow horizontal a partir de 320px.

## Acessibilidade

- Texto continua sendo a fonte do nome acessível de cada botão.
- Cor não substitui os rótulos `Errei`, `Difícil`, `Bom` e `Fácil`.
- A ordem DOM e visual permanece `again`, `hard`, `good`, `easy`.
- O estado `disabled` durante submissão continua nativo.
- O indicador de progresso mantém `aria-live="polite"`.
- O erro continua com `role="alert"`.

## Limites

- Não alterar `RATINGS`, `handleRate`, `createReview`, índices, contadores, loading, erros, estados vazio/concluído ou rotas.
- Não alterar o componente global `Button` ou `Card`.
- Não adicionar ícones aos botões de avaliação nesta etapa; as cores, rótulos e hierarquia são suficientes.
- A instalação de `lucide-react` pertence à Sidebar e não é requisito do card de estudo.

## Verificação

- Testar que cada botão mantém label, classes globais, `data-rating` correto e envia o rating atual.
- Confirmar que os seletores locais alcançam os cards ativo, vazio e concluído sem alterar `Card.css`.
- Preservar testes de revelar, avançar e conclusão.
- Executar teste focado, suíte frontend, lint, build, diff check e inspeção em desktop, 1024px, 640px, 320px, foco e reduced motion.
