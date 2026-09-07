# Modernização do mascote do Anki Generator

## Objetivo

Substituir a arte quadrada atualmente incorporada ao `README.md` por um banner
horizontal, profissional e simpático, alinhado à identidade visual do frontend.
O mesmo mascote modernizado deverá originar o favicon, mantendo reconhecimento
visual consistente entre o repositório e a aplicação.

## Direção visual escolhida

O banner seguirá uma composição horizontal: mascote à esquerda e bloco de texto
à direita. A linguagem visual será tecnológica, limpa e acolhedora, apropriada
para um projeto de portfólio sem parecer infantil.

A ilustração preservará os elementos que identificam o mascote atual:

- pilha de flashcards como corpo;
- cérebro com circuitos;
- olhos e sorriso amigáveis.

O redesenho simplificará as formas, uniformizará os contornos e reduzirá o ruído
visual. Os balões “ABC” e “Context”, ícones de usuários, linhas decorativas e
partículas aleatórias da arte atual serão removidos. Um arco discreto de
repetição espaçada envolverá a pilha de cards para comunicar o ciclo de
aprendizagem sem adicionar complexidade excessiva.

## Composição e texto

- Formato final do banner: PNG horizontal de `1536 × 640 px`.
- Fundo: preto ou carvão quase preto, com acabamento sóbrio.
- Mascote: concentrado no lado esquerdo, com margens seguras.
- Texto principal, exatamente: `Anki Generator`.
- Texto secundário, exatamente: `Flashcards inteligentes. Aprendizado que evolui.`
- Tipografia: sans-serif geométrica próxima de Outfit, com alta legibilidade.
- Hierarquia: nome dominante; tagline menor e visualmente secundária.
- O banner não deverá conter badges, mockups de interface nem nomes de
  tecnologias.

O `README.md` exibirá o banner centralizado com largura máxima apropriada e sem
atributo de altura fixo, preservando sua proporção original em diferentes
larguras de tela.

## Paleta

A arte usará somente a base visual do frontend, admitindo variações tonais para
volume e antialiasing:

- destaque: laranja `#ff9800`;
- fundo e contornos: preto `#000000` e carvão;
- superfícies e texto: branco `#ffffff` e cinza-claro `#f2f2f2`.

Azul, turquesa e gradientes pastéis da imagem antiga não serão usados como cores
principais.

## Favicon

O favicon será um PNG quadrado de `192 × 192 px`, derivado do mesmo redesenho.
Ele mostrará apenas a pilha de cards com o cérebro e o rosto, sem nome ou
tagline. Os traços deverão permanecer reconhecíveis a `32 × 32 px`, com alto
contraste e sem detalhes finos essenciais.

## Arquivos e integração

- Adicionar o banner como `docs/assets/anki-generator-banner.png`.
- Substituir `frontend/public/favicon.png` pela versão coerente com o banner.
- Atualizar o primeiro bloco do `README.md` para usar o banner local e não o
  anexo remoto do GitHub.
- Manter o título Markdown `# 🎴 Anki Generator` e os badges existentes abaixo
  do banner.

## Critérios de aceitação

1. O banner tem proporção horizontal e não sofre distorção no GitHub.
2. `Anki Generator` e a tagline aparecem exatamente como especificados, sem
   erros ortográficos.
3. O mascote continua reconhecível como a pilha de flashcards com cérebro,
   olhos e sorriso da arte anterior.
4. A paleta é coerente com os tokens do frontend: preto, branco e `#ff9800`.
5. A composição permanece legível na largura típica de um README e em tela
   móvel.
6. O favicon corresponde claramente ao mascote do banner e funciona em tamanhos
   reduzidos.
7. Os assets finais ficam versionados no repositório e não dependem de anexos
   externos.

## Verificação

- Conferir dimensões, formato e modo de cor dos dois PNGs.
- Inspecionar visualmente o banner em tamanho integral e reduzido.
- Inspecionar o favicon em `192 × 192 px` e em uma prévia de `32 × 32 px`.
- Renderizar ou abrir o `README.md` para confirmar proporção, caminho do asset,
  texto alternativo e convivência com título e badges.
- Confirmar que somente a documentação e os assets previstos foram alterados.
