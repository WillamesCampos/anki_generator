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
