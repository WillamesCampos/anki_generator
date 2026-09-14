# Design — Navegação da Sidebar com Lucide

Data: 2026-09-14
Status: aprovado

## Objetivo

Substituir letras e SVGs manuais da Sidebar por um sistema coerente de ícones, mantendo texto no menu aberto e exibindo somente ícones no estado recolhido. Cada item recolhido apresenta seu nome em tooltip no hover e no foco por teclado.

## Biblioteca escolhida

Usar `lucide-react`, escolhida por sua linguagem visual de traço consistente, suporte a `currentColor`, componentes SVG e imports individuais tree-shakable. A dependência será instalada e registrada em `package.json`/`package-lock.json`; somente ícones nomeados serão importados.

Não usar import curinga, fonte de ícones, SVG copiado nem uma segunda biblioteca.

## Mapeamento

- `Home` → `House`
- `Decks` → `Layers3`
- `Categorias` → `Tags`
- `Relatórios` → `ChartColumn`
- `Chat com IA` → `Bot`
- `Sair` → `LogOut`
- `Recolher menu` → `ChevronsLeft`
- `Expandir menu` → `ChevronsRight`

Antes de editar `Sidebar.jsx`, a implementação deve instalar o pacote e confirmar esses exports exatos. Um export ausente bloqueia a implementação até esta especificação ser alterada explicitamente; não é permitido substituir um ícone silenciosamente.

## Estrutura do item

Cada `NAV_ITEM` passa a carregar a referência do componente de ícone. O link renderiza sempre:

1. ícone decorativo com `.sidebar__item-icon`, `aria-hidden="true"` e `strokeWidth={2}`;
2. texto em `.sidebar__link-label`;
3. tooltip visual em `.sidebar__tooltip`, oculto da árvore acessível.

No menu aberto, ícone e texto ficam lado a lado e o tooltip não aparece. No recolhido, o texto visual é ocultado, o ícone fica centralizado e o link recebe `aria-label` com o nome completo.

O botão de logout segue a mesma composição. Rotas, link ativo, autenticação e chamada de logout não mudam.

## Tooltip

- Só aparece com a Sidebar recolhida.
- Abre à direita do item em `:hover` e `:focus-visible`.
- Usa fundo laranja, texto preto, borda preta, cantos de card e tipografia pequena forte.
- Não intercepta ponteiro e não cria foco próprio.
- Fica acima do conteúdo por `z-index`, sem alterar a largura da Sidebar.
- É visual; o nome acessível vem de `aria-label`, portanto o tooltip usa `aria-hidden="true"` para evitar repetição.

## Toggle

O controle mantém `44px × 44px`, fundo laranja, borda preta, cantos de card e ausência de sombra. O SVG manual é substituído pelos componentes `ChevronsLeft`/`ChevronsRight`, de acordo com `collapsed`. Labels, `aria-expanded`, `aria-controls`, persistência e comportamento responsivo permanecem iguais.

## Interação e acessibilidade

- Ícones herdam `currentColor`; item ativo/hover continua laranja.
- Todos os ícones são decorativos e não alteram o nome dos links/botões.
- Em estado recolhido, cada item e o logout continuam localizáveis pelo nome completo via `aria-label`.
- Tooltip também aparece no foco por teclado.
- `:focus-visible` permanece perceptível sobre a Sidebar preta.
- `prefers-reduced-motion: reduce` remove transições do tooltip sem remover conteúdo ou estado.

## Responsividade e limites

- Larguras continuam `240px` e `72px`; breakpoint continua `1024px`.
- Ícones usam `20px`; toggle usa `22px`.
- Tooltips devem caber em viewport de 320px sem criar overflow horizontal.
- Não alterar marca, ordem dos itens, labels, rotas, logout, `localStorage`, listener de viewport, AppShell ou conteúdo da Home.
- Não criar componente global de ícone nesta etapa; a composição é local à Sidebar.

## Verificação

- Testar ícone e label de cada item no menu aberto.
- Testar somente ícones visíveis e nomes acessíveis completos no menu recolhido.
- Testar ícones do toggle antes/depois do clique, ARIA e persistência.
- Testar logout com ícone sem mudar o fluxo.
- Executar suíte focada, suíte frontend, lint, build, diff check e inspeção em estados aberto/recolhido, hover, foco, 320px e reduced motion.

## Referências

- [Lucide — documentação oficial](https://lucide.dev/)
- [Lucide — catálogo e personalização](https://v0.lucide.dev/)
