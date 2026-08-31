# Auditoria de consistência visual (tarefas 5.1/5.2)

Checklist executado contra o código real (`grep`, não leitura por
amostragem) antes de considerar a Sprint 3 concluída.

## Método

```bash
# cores fora dos arquivos de token
grep -rn "rgb(\|#[0-9a-fA-F]\{3,6\}" --include="*.css" --include="*.jsx" src/ \
  | grep -v "tokens/tokens.css\|tokens/tokens.js\|tokens/AUDIT.md"

# px hardcoded em CSS fora de tokens.css
grep -rn "[0-9]px" --include="*.css" src/ | grep -v "tokens/tokens.css"

# spacing/cor inline em JSX fora de tokens.js
grep -n "style={{" src/pages/*.jsx src/components/**/*.jsx
```

## Resultado

- **Cor**: nenhuma cor hardcoded encontrada fora de `tokens/tokens.css`/`tokens/tokens.js` — todos os componentes (`Card`, `Button`, `Sidebar`, `AppShell`) consomem `var(--color-*)` ou `colors.*`.
- **Espaçamento inline em JSX**: encontrados 2 desvios em `HomePage.jsx` (`gap: 30` e `marginTop: 16`, valores literais em vez de tokens) — **corrigidos** para `spacing.md`/`spacing.sm` importados de `tokens/tokens.js`.
- **Espaçamento em CSS**: `Sidebar.css` tem `width: 240px` fora da escala de tokens — **revisado e aceito**: é uma medida estrutural de layout (largura fixa da sidebar), não um valor de cor/tipografia/espaçamento repetível — fora do escopo do que `AUDIT.md` define como token.
- **Tipografia**: `font-family`/tamanhos usados só via `var(--font-*)`/`typography.*` — nenhuma fonte fora de "Outfit" encontrada.
- **Raio de borda**: `Card`/`Button` usam `var(--radius-card)`/`var(--radius-pill)` — nenhum `border-radius` hardcoded fora de `tokens.css`.

Reexecutar este checklist sempre que uma tela nova for adicionada (Sprint 4+).

## Revalidação — Sprint 4

- `LoginPage.jsx` e `HomePage.jsx` não contêm mais `style={{...}}`; todos os estilos visuais foram movidos para CSS dedicado.
- Nenhuma cor literal foi introduzida no CSS/JSX fora de `tokens.css`/`tokens.js`; o favicon é um asset de marca derivado diretamente da imagem do mascote exibida no `README.md`.
- O breakpoint estrutural único é `1024px`, conforme o PRD; espaçamento continua usando `var(--space-*)`.
- Inspeção real em Chrome headless a 1024×768 confirmou Login centralizado, Home com sidebar colapsada, grid em duas colunas e ausência de overflow horizontal (`scrollWidth = viewportWidth = 1024`).
- Auditoria automatizada executada junto de `npm test`, `npm run lint` e `npm run build` antes do fechamento da sprint.

## Revalidação — Sprint 7

- As telas de lista, criação, detalhe e cards dedicados reutilizam `Card`, `Button` e `Input`; a contagem mínima e o diálogo de confirmação também são compostos exclusivamente desses componentes.
- Formulários, grids, estados vazios e ações usam apenas `var(--space-*)`, `var(--font-*)`, `var(--radius-*)` e `var(--color-*)` extraídos do design system.
- O backdrop do `ConfirmDialog` usa o novo token semântico `--color-overlay`, cujo valor exato (`rgba(0, 0, 0, 0.5)`) está documentado em `design-system.html` e rastreado em `AUDIT.md`.
- O overline das páginas usa o padrão `.mil-upper` documentado: uppercase, tamanho pequeno e `letter-spacing` de `2px`, agora exposto como `--letter-spacing-upper`.
- Nenhuma cor literal ou estilo inline foi introduzido nas novas telas/componentes.
