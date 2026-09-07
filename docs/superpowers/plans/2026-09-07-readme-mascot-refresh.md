# Readme Mascot Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernizar o mascote do Anki Generator em um banner horizontal e um favicon coerente, ambos versionados e integrados ao projeto.

**Architecture:** A imagem atual serve como referência de identidade, enquanto duas gerações raster produzem entregáveis especializados: um banner legível no GitHub e um ícone simplificado para tamanhos pequenos. O README referencia o banner local sem altura forçada, e o frontend continua consumindo o favicon no caminho existente.

**Tech Stack:** built-in image generation, PNG, Markdown/HTML do GitHub, comandos Unix de inspeção e Git.

## Global Constraints

- Banner PNG de `1536 × 640 px` em `docs/assets/anki-generator-banner.png`.
- Favicon PNG de `192 × 192 px` em `frontend/public/favicon.png`.
- Paleta principal: preto `#000000`, branco `#ffffff`, cinza-claro `#f2f2f2` e laranja `#ff9800`.
- Texto exato do banner: `Anki Generator`.
- Tagline exata: `Flashcards inteligentes. Aprendizado que evolui.`
- Preservar pilha de flashcards, cérebro com circuitos, olhos e sorriso.
- Não usar azul/turquesa como cores principais; não incluir balões, usuários, badges, mockups ou nomes de tecnologias.
- Não depender de anexos externos do GitHub.

---

### Task 1: Produzir e validar os assets do mascote

**Files:**
- Create: `docs/assets/anki-generator-banner.png`
- Modify: `frontend/public/favicon.png`

**Interfaces:**
- Consumes: imagem atual do README como referência visual e os tokens de `frontend/src/tokens/tokens.css`.
- Produces: banner PNG horizontal e favicon PNG quadrado prontos para consumo estático.

- [x] **Step 1: Gerar o banner a partir da referência atual**

Usar a ferramenta integrada de geração de imagem com a arte atual carregada como
referência e esta especificação:

```text
Use case: stylized-concept
Asset type: banner principal de README para um projeto de portfólio técnico
Primary request: modernizar o mascote atual do Anki Generator e reorganizá-lo em um hero horizontal profissional e simpático
Input image: imagem atual do README; referência de identidade do mascote
Scene/backdrop: fundo preto ou carvão quase preto, limpo e sóbrio
Subject: à esquerda, pilha de flashcards com cérebro de circuitos, olhos e sorriso; formas simplificadas, contornos uniformes e acabamento contemporâneo; um único arco discreto envolvendo os cards representa repetição espaçada
Style/medium: ilustração digital vetorial polida, tecnológica e acolhedora, apropriada para portfólio profissional
Composition/framing: canvas horizontal 1536 × 640; mascote no terço esquerdo; nome e tagline no lado direito; margens amplas e equilíbrio visual
Color palette: preto #000000, branco #ffffff, cinza-claro #f2f2f2 e laranja #ff9800; variações tonais apenas para volume e antialiasing
Text (verbatim): "Anki Generator"
Secondary text (verbatim): "Flashcards inteligentes. Aprendizado que evolui."
Typography: sans-serif geométrica semelhante a Outfit; nome grande; tagline menor; acentuação perfeita e alta legibilidade
Constraints: preservar a identidade da pilha de cards, cérebro com circuitos, olhos e sorriso; aparência profissional e simpática; texto exatamente como fornecido
Avoid: azul ou turquesa como cores principais, aparência infantil, excesso de partículas, balões ABC/Context, ícones de usuários, badges, mockups, nomes de tecnologias, texto adicional, watermark
```

Salvar o resultado escolhido em `docs/assets/anki-generator-banner.png` sem
sobrescrever qualquer outro asset.

- [x] **Step 2: Inspecionar e corrigir o banner**

Abrir o PNG em resolução original e conferir composição, identidade, paleta e
texto. Se houver erro textual, distorção ou elemento proibido, fazer uma única
iteração dirigida que altere somente o defeito e preserve todo o restante.

Executar:

```bash
file docs/assets/anki-generator-banner.png
```

Esperado: `PNG image data, 1536 x 640`.

- [x] **Step 3: Gerar o favicon a partir do mascote aprovado**

Usar o banner aprovado como referência e esta especificação:

```text
Use case: stylized-concept
Asset type: favicon quadrado de aplicação web
Primary request: extrair e simplificar exatamente o mesmo mascote aprovado no banner
Input image: banner aprovado; referência obrigatória de identidade, formas e paleta
Scene/backdrop: fundo preto sólido
Subject: pilha de flashcards com cérebro de circuitos, olhos e sorriso, centralizada e preenchendo o quadro
Style/medium: mesma ilustração digital vetorial do banner, simplificada para permanecer reconhecível em 32 × 32 px
Composition/framing: canvas quadrado 192 × 192; margens pequenas e uniformes; alto contraste
Color palette: preto #000000, branco #ffffff, cinza-claro #f2f2f2 e laranja #ff9800
Constraints: preservar exatamente a identidade visual do mascote do banner; poucos detalhes; silhueta clara
Avoid: qualquer texto, tagline, arco cortado, objetos extras, gradientes pastéis, azul, turquesa, watermark
```

Substituir `frontend/public/favicon.png` pelo resultado final.

- [x] **Step 4: Validar o favicon nos tamanhos de consumo**

Abrir o favicon em resolução original e conferir uma prévia reduzida a `32 × 32`
para confirmar silhueta, contraste, olhos, sorriso e cérebro.

Executar:

```bash
file frontend/public/favicon.png
```

Esperado: `PNG image data, 192 x 192`.

- [x] **Step 5: Commitar os assets aprovados**

```bash
git add docs/assets/anki-generator-banner.png frontend/public/favicon.png
git commit -m "docs: refresh Anki Generator mascot artwork"
```

### Task 2: Integrar o banner ao README

**Files:**
- Modify: `README.md:1-3`
- Test: `README.md`

**Interfaces:**
- Consumes: `docs/assets/anki-generator-banner.png` produzido na Task 1.
- Produces: cabeçalho do README sem dependência externa nem distorção de proporção.

- [x] **Step 1: Atualizar a referência da imagem**

Substituir o bloco inicial por:

```html
<div align="center">
    <img width="800" alt="Anki Generator — Flashcards inteligentes. Aprendizado que evolui." src="./docs/assets/anki-generator-banner.png" />
</div>
```

Não adicionar `height`; manter o título Markdown e os badges existentes abaixo.

- [x] **Step 2: Validar caminho, proporção declarada e diff**

Executar:

```bash
test -f docs/assets/anki-generator-banner.png
rg -n 'docs/assets/anki-generator-banner.png|width="800"|height=' README.md
git diff --check
```

Esperado: caminho local e `width="800"` presentes no topo; nenhuma ocorrência
de `height=` no bloco da imagem; `git diff --check` sem saída.

- [x] **Step 3: Revisar o cabeçalho renderizado**

Visualizar o README ou seu HTML renderizado e confirmar que o banner está
centralizado, mantém a proporção, permanece legível em largura reduzida e não
colide com o título ou os badges.

- [x] **Step 4: Commitar a integração**

```bash
git add README.md
git commit -m "docs: use local mascot banner in readme"
```

- [x] **Step 5: Executar a verificação final do escopo**

```bash
file docs/assets/anki-generator-banner.png frontend/public/favicon.png
git diff HEAD~2..HEAD --check
git status --short --branch
```

Esperado: dimensões corretas dos dois PNGs, nenhum erro de whitespace e árvore
de trabalho limpa na branch `readme-badges-tooling`.
