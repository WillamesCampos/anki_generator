## 1. Backend — filtro de deck em cards devidos

- [x] 1.1 `ICardRepository`/`CardRepository.find_due(owner_id, deck_id=None, due_before=None)` — filtro opcional por deck (ver D1 em design.md)
- [x] 1.2 `CardListCreateView.get_queryset` — aceita `due=true` e `deck_id` combinados, não mais mutuamente exclusivos
- [x] 1.3 Testes automatizados (pytest): due cards filtrados por deck, due cards sem filtro continuam globais, isolamento multi-tenant (deck de outro usuário não vaza)

## 2. Frontend — API client

- [x] 2.1 `api/cards.js`: `fetchDueCards` ganha parâmetro opcional `deckId`

## 3. Tela de estudo

- [x] 3.1 Botão "Estudar" na tela de detalhe do deck (Sprint 7), navegando pra `/decks/{deckId}/estudar`
- [x] 3.2 Rota `/decks/{deckId}/estudar` — busca os cards devidos do deck uma vez ao montar, guarda em estado local (sem sessão persistida, ver D2 em design.md)
- [x] 3.3 Exibe `front`; revela `back` + `front_description` + `back_description` sob interação do usuário, com rótulos visíveis em português
- [x] 3.4 4 botões de avaliação (`again`/`hard`/`good`/`easy`) — `POST /api/v1/cards/{card_id}/review/`, avança pro próximo card da lista local
- [x] 3.5 Progresso "X de Y" durante a sessão
- [x] 3.6 Estado vazio ("nenhum card devido agora") quando o deck não tem cards devidos
- [x] 3.7 Tela de fim de sessão (resumo + voltar pro deck) ao avaliar o último card

## 4. Testes automatizados (frontend)

- [x] 4.1 Fluxo completo: revelar resposta, avaliar, avançar pro próximo card
- [x] 4.2 Estado vazio renderiza a mensagem correta, não uma sessão vazia silenciosa
- [x] 4.3 Avaliar o último card mostra a tela de fim de sessão

## 5. Documentação

- [x] 5.1 Atualizar `PRD.md` (Sprint 9) marcando as tarefas concluídas
- [x] 5.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 9]`

## 6. E-mail customizado de recuperação de senha

- [x] 6.1 Sobrescrever assunto e corpos texto/HTML de `account/email/password_reset_key` com a identidade “Dark premium” do Anki Generator
- [x] 6.2 Manter `password_reset_url`, token assinado, proteção contra enumeração e telas React sem alterações comportamentais
- [x] 6.3 Testar mensagem multipart, assunto, CTA, fallback de URL e ausência de recursos externos

## 7. Caminhos de descoberta até a tela de estudo

- [x] 7.1 `HomePage.jsx`: botão "Continuar estudando" dentro do bloco já existente de `lastDeck` (card "Último deck estudado"), navegando pra `/decks/{deckId}/estudar`
- [x] 7.2 `HomePage.jsx`: CTA secundário sempre visível, com texto condicional ("Não é o deck que deseja estudar agora? Escolha o seu deck!" com `lastDeck`, "Escolha um deck pra começar a estudar!" sem `lastDeck`), navegando pra `/decks`
- [x] 7.3 `DeckListPage.jsx`: botão "Estudar" em cada item, ao lado de "Abrir deck", navegando pra `/decks/{deckId}/estudar` — sem checagem prévia de cards devidos
- [x] 7.4 Confirmar que `Sidebar.jsx` não é alterado (ver D6 em design.md)
- [x] 7.5 Testes automatizados (frontend): botão "Continuar estudando" da Home aparece só com `lastDeck` válido, CTA secundário troca de texto conforme o estado.
  Botão "Estudar" presente em cada item de `DeckListPage`.
- [x] 7.6 Atualizar `PRD.md`/`CHANGELOG.md` com essa extensão da Sprint 9
- [x] 7.7 HomePage.css: estilizar "Continuar estudando" e "Ver meus decks" na direção “Contraste expressivo”, com estados hover/active/focus, layout móvel e redução de movimento
- [x] 7.8 `HomePage.jsx`/`HomePage.css`: enriquecer o gráfico de estatísticas com opções e dataset tokenizados, resumo acessível associado, responsividade e redução de movimento; `HomePage.test.jsx` cobre a configuração observável e a preferência do usuário, sem alterar CTA, Sidebar, `Card` ou `Button`
- [x] 7.9 `HomePage.jsx`/`HomePage.css`: aplicar borda preta de 2 px aos dois cards superiores e transformar “Meta de estudo” em painel branco com contagem, selo percentual, barra semântica, mensagem de estado e redução de movimento, preservando cálculo, APIs e componentes globais
