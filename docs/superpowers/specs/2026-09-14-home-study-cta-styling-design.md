# Design — CTAs de estudo da Home

## Contexto

A Home já possui dois caminhos de descoberta implementados na Sprint 9:

- “Estudar”, dentro do card “Último deck estudado”, abre diretamente a sessão do último deck válido.
- “Ver meus decks”, abaixo dos cards de resumo, leva à listagem para o usuário escolher outro deck.

Os dois destinos e suas regras condicionais estão corretos, mas a apresentação visual ainda não comunica com clareza que a primeira ação é imediata e primária enquanto a segunda é exploratória. O design aprovado em mockup foi a direção **B — Contraste expressivo**.

## Objetivos

- Criar hierarquia inequívoca entre a ação primária e a secundária.
- Dar personalidade aos CTAs usando a identidade preta, branca e laranja do Anki Generator.
- Manter os botões claros, acessíveis e confortáveis em desktop, tablet e celular.
- Preservar integralmente navegação, carregamento, estados de erro e regras de renderização existentes.

## Fora de escopo

- Alterar a estrutura dos cards, gráfico, sidebar ou demais botões do produto.
- Modificar o componente global `Button` ou seus variants.
- Criar ícones como arquivos, instalar biblioteca de ícones ou adicionar tokens globais.
- Alterar o texto condicional que acompanha “Ver meus decks”.
- Mudar os destinos `/decks/{deckId}/estudar` e `/decks`.

## Direção visual aprovada

### Ação primária — “Continuar estudando”

O botão contextual do último deck passa de “Estudar” para **“Continuar estudando”**, reforçando que a pessoa retomará o deck exibido no card. Ele ocupa toda a largura disponível, usa fundo laranja, texto preto, cantos de `var(--radius-card)` e uma sombra preta sólida deslocada. Um pequeno símbolo de play decorativo antecede o texto sem entrar no nome acessível do link.

A composição deve parecer energética e acionável, sem aumentar a altura do card de forma desproporcional.

### Ação secundária — “Ver meus decks”

O botão mantém o texto **“Ver meus decks”**, com fundo preto, texto branco, os mesmos cantos de card e uma sombra laranja deslocada. Um ícone de olho aberto decorativo sucede o texto e comunica visualização/exploração.

Apesar do contraste alto, sua área menor e sua posição fora do card preservam a prioridade visual de “Continuar estudando”. O texto condicional atual ao lado do botão não muda.

### Faixa de descoberta

O bloco que acompanha “Ver meus decks” ganha presença própria com fundo laranja, borda preta de `2px`, cantos de `var(--radius-card)` e sombra preta deslocada. Sua frase usa peso forte, tamanho médio e cor preta para funcionar como uma faixa de orientação visual, enquanto o botão e o olho aberto preservam integralmente seu visual e comportamento atuais.

## Interação e acessibilidade

- `:hover`: o botão se desloca na direção da sombra e a sombra diminui, produzindo feedback físico curto.
- `:active`: o deslocamento aumenta e a sombra se aproxima de zero.
- `:focus-visible`: outline preto no botão laranja e outline laranja no botão preto, ambos com distância suficiente para não se confundirem com a sombra.
- `prefers-reduced-motion: reduce`: remove transições e transformações dos dois CTAs.
- O símbolo de play continua sendo um pseudo-elemento CSS. O olho aberto é um SVG inline decorativo, com `aria-hidden="true"` e `focusable="false"`; nenhum dos dois altera os nomes acessíveis usados nos testes ou por leitores de tela.
- O contraste de texto permanece alto: preto sobre laranja e branco sobre preto.

## Responsividade

Em desktop, “Continuar estudando” ocupa a largura do conteúdo do card. “Ver meus decks” permanece ao lado do texto condicional.

Em telas de até `640px`, o bloco secundário empilha texto e botão; “Ver meus decks” passa a ocupar 100% da largura. O botão primário já é fluido por definição. Nenhum conteúdo pode provocar overflow horizontal a partir de 320 px.

## Arquitetura e componentes

O ajuste fica isolado nos seletores locais de `HomePage.css`. O `Button` global continua fornecendo semântica, tipografia básica e comportamento de link; as classes específicas da Home definem apenas a linguagem visual destes dois CTAs.

`HomePage.jsx` muda o rótulo da ação primária e inclui o SVG inline decorativo do olho. O play continua sendo pseudo-elemento CSS; o SVG é oculto da árvore acessível. Não há mudança no fluxo de dados:

1. A Home carrega revisões e resolve o último deck acessível.
2. Se houver deck válido, renderiza “Continuar estudando” com o mesmo destino atual.
3. Após o carregamento de revisões, renderiza “Ver meus decks” com o mesmo texto condicional e destino atual.
4. Erros e estados vazios continuam seguindo os branches existentes.

## Testes e verificação

- Atualizar os testes da Home para buscar “Continuar estudando” e confirmar o mesmo `href` do deck.
- Manter a cobertura atual: ausência da ação primária sem último deck válido, CTA secundário presente e textos condicionais corretos.
- Verificar que os pseudo-elementos não alteram os nomes acessíveis.
- Executar Vitest focado na Home, ESLint e a suíte completa do frontend.
- Inspecionar desktop e viewport de 320 px para confirmar hierarquia, foco visível, ausência de overflow e comportamento com redução de movimento.

## Arquivos previstos

- `frontend/src/pages/HomePage.jsx`
- `frontend/src/pages/HomePage.css`
- `frontend/src/pages/HomePage.test.jsx`

Nenhum outro arquivo de produção deve ser alterado.
