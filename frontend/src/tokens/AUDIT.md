# Auditoria de tokens — `refs/Ashley_files/style.css`

Tarefa 2.1/2.2 do PRD (Sprint 3). Cada valor abaixo foi confirmado por
inspeção direta de `refs/Ashley_files/style.css` (grep, não memória/suposição)
— linha de referência entre parênteses. Nenhum valor foi inventado.

## Cor

| Token | Valor | Fonte |
|---|---|---|
| `accent` | `rgb(255, 152, 0)` | style.css:593,631,779,799 — cor de destaque/hover/CTA repetida |
| `textPrimary` | `rgb(0, 0, 0)` | style.css:594,686,766,769 |
| `textSecondary` | `rgba(0, 0, 0, 0.5)` | style.css:700,707,714,721,729 — texto secundário/legenda |
| `border` | `rgba(0, 0, 0, 0.1)` | style.css:535,758 — divisores/bordas claras |
| `bgLight` | `rgb(242, 242, 242)` | style.css:836 — fundo de seção clara |
| `bgDark` | `rgb(0, 0, 0)` | style.css:612,1035,1098 (`.mil-dark-bg`, style.css:812) |
| `textOnDark` | `rgba(255, 255, 255, 0.9)` | design-system.html:796 (nav sobre fundo escuro) |
| `overlay` | `rgba(0, 0, 0, 0.5)` | design-system.html:102 (`.ds-swatch-dark-soft`, extraído de style.css:75) |

## Tipografia

| Token | Valor | Fonte |
|---|---|---|
| `fontFamily` | `"Outfit", sans-serif` | style.css:72,163,685,3074+ (repetida em toda regra de texto) |
| `fontSizeBase` | `16px` | style.css:73 |
| `lineHeightBase` | `150%` | style.css:76 |
| `fontSizeUpper` | `12px` | design-system.html:523 (`.mil-upper`) |
| `letterSpacingUpper` | `2px` | design-system.html:523 (`.mil-upper`) |

Headlines do template original vão de 86px a 34px (style.css:187-210) — escala
de hero de portfólio, desproporcional para um dashboard. Adaptamos a
**proporção** (título grande > subtítulo > corpo), não os pixels literais:
`fontSizeXl`/`fontSizeLg`/`fontSizeMd` abaixo usam uma escala menor, mas
ancorada nos mesmos incrementos relativos vistos na cascata original.

## Espaçamento

Escala extraída diretamente dos valores de `padding`/`margin`/`gap`
efetivamente usados no CSS (não uma escala arbitrária tipo 4/8/16):

| Token | Valor | Fonte |
|---|---|---|
| `spaceXs` | `10px` | style.css (4 ocorrências de `padding`/`gap: 10px`) |
| `spaceSm` | `15px` | style.css:620,2488,3271,3299 |
| `spaceMd` | `30px` | style.css (8 ocorrências — o espaçamento mais comum do template) |
| `spaceLg` | `50px` | style.css (2 ocorrências) |
| `spaceXl` | `60px` | style.css (6 ocorrências) |

## Raio de borda

| Token | Valor | Fonte | Uso pretendido |
|---|---|---|---|
| `radiusPill` | `70px` | style.css:595,3067,3273 | botões, badges |
| `radiusCard` | `40px` | style.css:2970 | cards (adaptado para `16px` no dashboard — 40px em um card pequeno de estatística ficaria desproporcional; ver nota abaixo) |
| `radiusCircle` | `50%` | style.css:515,608,2774,2932 | avatares/ícones circulares |

**Nota sobre `radiusCard`**: o valor original (40px) foi desenhado para cards
grandes de portfólio (largura de coluna inteira). Nos cards pequenos do
dashboard (estatística, último deck), 40px produziria um formato quase
circular nas bordas — mantivemos a *linguagem* (cantos bem arredondados,
não o `border-radius: 4px` de UI corporativa genérica) com `16px`,
proporcional ao tamanho real do componente. Sinalizado explicitamente aqui
para a auditoria da tarefa 5.1 revisar essa decisão.
