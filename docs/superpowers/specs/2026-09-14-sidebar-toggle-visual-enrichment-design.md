# Design — Enriquecimento visual do toggle da Sidebar

## Contexto

A Sidebar já controla corretamente o estado expandido/recolhido, persiste a preferência manual em `localStorage` e recolhe por padrão em viewports de até `1024px` quando não há preferência salva. O toggle atual, porém, é um círculo de `28px` com os glifos tipográficos `«` e `»`; ele tem pouca presença visual na superfície preta e não expõe programaticamente qual região controla nem se ela está expandida.

A direção aprovada é **Contraste expressivo**: transformar somente esse controle em um elemento tátil, claramente reconhecível e coerente com a identidade preta, branca e laranja do Anki Generator.

## Objetivos

- Dar ao toggle hierarquia e legibilidade sobre a Sidebar preta.
- Tornar expansão, recolhimento, foco e acionamento perceptíveis visualmente e por tecnologia assistiva.
- Preservar toda a lógica atual de estado, persistência e resposta ao breakpoint.
- Manter o ajuste estritamente local a `Sidebar.jsx`, `Sidebar.css` e seus testes.

## Fora de escopo

- Alterar links, rótulos de navegação, rotas, logout ou autenticação.
- Alterar `COLLAPSED_KEY`, `TABLET_MEDIA_QUERY`, `getInitialCollapsed`, o listener de viewport ou `toggleCollapsed`.
- Mudar a largura expandida de `240px` ou a largura colapsada de `72px`.
- Criar componente ou arquivo de ícone, instalar biblioteca ou adicionar/modificar tokens globais.
- Redesenhar marca, itens da lista, estado ativo dos links ou comportamento responsivo.

## Direção visual aprovada

O toggle passa a ser um botão quadrado de `44px × 44px`, com `box-sizing: border-box`, fundo `var(--color-accent)`, ícone em `var(--color-text-primary)`, borda preta sólida de `2px` e cantos em `var(--radius-card)`. O controle não possui sombra, mantendo sua geometria contida na Sidebar preta.

Os glifos `«` e `»` são substituídos por um único SVG inline de chevron duplo apontando para a esquerda no estado expandido. O mesmo SVG recebe rotação de `180deg` quando a Sidebar está colapsada, apontando para a direção da expansão. O SVG é puramente decorativo: `aria-hidden="true"` e `focusable="false"`; os nomes acessíveis continuam vindo dos `aria-label` atuais, `Recolher menu` e `Expandir menu`.

## Interação e acessibilidade

- O botão expõe `aria-expanded="true"` enquanto a Sidebar está expandida e `aria-expanded="false"` enquanto está colapsada.
- `aria-controls="sidebar-navigation-list"` referencia o `id="sidebar-navigation-list"` aplicado à lista `<ul>` existente.
- `:hover` desloca o botão em `2px` nos dois eixos, criando resposta tátil sem sombra.
- `:active` desloca o botão em `4px`, simulando pressão sem sombra.
- `:focus-visible` usa outline branco de `3px` com `3px` de afastamento, visível sobre o fundo preto e distinto da borda.
- O SVG acompanha a cor preta via `currentColor`, não recebe eventos do ponteiro e não cria nome ou parada de foco adicional.
- Em `prefers-reduced-motion: reduce`, as transições da largura da Sidebar, do botão e do ícone são removidas, assim como os transforms de hover/active. A orientação de estado do ícone permanece, mas muda instantaneamente, sem animação; largura, conteúdo da marca, nome acessível dinâmico e `aria-expanded` também comunicam o estado sem movimento.

## Encaixe na Sidebar colapsada

Com `72px` de largura total e o padding horizontal atual de `15px`, a área interna desktop tem apenas `42px`, insuficiente para o novo botão. A variante `.sidebar--collapsed` passa a usar `var(--space-xs)` (`10px`) em cada lateral, resultando em `52px` úteis. O header colapsado remove seu padding horizontal próprio, acomodando os `44px` do botão sem alterar a largura da Sidebar.

O header expandido, a ordem marca/toggle e o empilhamento atual do header colapsado permanecem os mesmos. O media query de `1024px` continua válido e não muda o comportamento funcional.

## Arquitetura e fluxo de estado

`Sidebar.jsx` continua sendo o único responsável pelo estado `collapsed`. O clique percorre o fluxo existente sem novas abstrações:

1. `toggleCollapsed` inverte o estado e persiste o novo booleano em `anki_generator_sidebar_collapsed`.
2. O modificador `sidebar--collapsed` continua representando o estado visual no `<nav>`.
3. `aria-expanded`, o rótulo/título dinâmico e a rotação do SVG derivam do mesmo `collapsed`.
4. A lista existente recebe apenas um `id` estável para estabelecer a relação de `aria-controls`.

Não há novo fluxo assíncrono nem tratamento de erro. A falha tolerada do logout, a navegação e a limpeza de listeners permanecem intactas.

## Testes e verificação

`Sidebar.test.jsx` mantém os cenários atuais de recolhimento automático e reação ao breakpoint. O cenário de preferência manual será enriquecido para verificar, antes e depois do clique:

- nomes acessíveis dinâmicos `Recolher menu` e `Expandir menu`;
- `aria-expanded` coerente com o estado;
- `aria-controls` apontando para uma lista existente com o id esperado;
- SVG inline com `aria-hidden="true"` e `focusable="false"`;
- classe colapsada e persistência de `true` em `localStorage` após o toggle.

As regras visuais não serão validadas por busca de texto CSS. A verificação será feita por teste comportamental focado, ESLint, suíte Vitest, build Vite e inspeção manual/headless em estado expandido, colapsado, foco por teclado, viewport estreita e preferência de redução de movimento.

## Arquivos previstos

- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/layout/Sidebar.css`
- `frontend/src/components/layout/Sidebar.test.jsx`

Nenhum outro arquivo de produção deve ser alterado.
