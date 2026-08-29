## 1. Backend — filtro de deck em cards devidos

- [ ] 1.1 `ICardRepository`/`CardRepository.find_due(owner_id, deck_id=None, due_before=None)` — filtro opcional por deck (ver D1 em design.md)
- [ ] 1.2 `CardListCreateView.get_queryset` — aceita `due=true` e `deck_id` combinados, não mais mutuamente exclusivos
- [ ] 1.3 Testes automatizados (pytest): due cards filtrados por deck, due cards sem filtro continuam globais, isolamento multi-tenant (deck de outro usuário não vaza)

## 2. Frontend — API client

- [ ] 2.1 `api/cards.js`: `fetchDueCards` ganha parâmetro opcional `deckId`

## 3. Tela de estudo

- [ ] 3.1 Botão "Estudar" na tela de detalhe do deck (Sprint 7), navegando pra `/decks/{deckId}/estudar`
- [ ] 3.2 Rota `/decks/{deckId}/estudar` — busca os cards devidos do deck uma vez ao montar, guarda em estado local (sem sessão persistida, ver D2 em design.md)
- [ ] 3.3 Exibe a frente do card (`word`); revela o verso (`translation` + `example`) sob interação do usuário
- [ ] 3.4 4 botões de avaliação (`again`/`hard`/`good`/`easy`) — `POST /api/v1/cards/{card_id}/review/`, avança pro próximo card da lista local
- [ ] 3.5 Progresso "X de Y" durante a sessão
- [ ] 3.6 Estado vazio ("nenhum card devido agora") quando o deck não tem cards devidos
- [ ] 3.7 Tela de fim de sessão (resumo + voltar pro deck) ao avaliar o último card

## 4. Testes automatizados (frontend)

- [ ] 4.1 Fluxo completo: revelar resposta, avaliar, avançar pro próximo card
- [ ] 4.2 Estado vazio renderiza a mensagem correta, não uma sessão vazia silenciosa
- [ ] 4.3 Avaliar o último card mostra a tela de fim de sessão

## 5. Documentação

- [ ] 5.1 Atualizar `PRD.md` (Sprint 8) marcando as tarefas concluídas
- [ ] 5.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 8]`
