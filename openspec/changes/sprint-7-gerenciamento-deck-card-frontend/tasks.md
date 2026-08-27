## 1. API client — mutations

- [ ] 1.1 `api/decks.js`: `createDeck`, `updateDeck`, `deleteDeck`
- [ ] 1.2 `api/cards.js`: `createCard`, `updateCard`, `deleteCard`
- [ ] 1.3 `api/categories.js` (novo): `fetchCategories`, `createCategory`

## 2. Componentes compartilhados

- [ ] 2.1 `ConfirmDialog` (`components/ui/`) — confirmação reutilizável com mensagem de aviso da janela de retenção de 7 dias, construído com `Card`/`Button` já existentes (ver D3 em design.md)

## 3. Tela de listagem e criação de Deck

- [ ] 3.1 Rota `/decks` substitui `<PlaceholderPage>` — lista os decks do usuário (`fetchDecks`), com estado vazio
- [ ] 3.2 Rota `/decks/novo` — formulário de criação (título, descrição, categoria, `daily_review_goal`), usando o seletor de categoria (grupo 5)
- [ ] 3.3 Após criação bem-sucedida, navega pro deck recém-criado ou de volta pra lista

## 4. Tela de detalhe do Deck — edição, exclusão, cards

- [ ] 4.1 Rota `/decks/:deckId` — exibe dados do deck com edição inline (toggle, ver D1 em design.md)
- [ ] 4.2 Botão de excluir deck, usando `ConfirmDialog` — `DELETE /api/v1/decks/{deck_id}/`
- [ ] 4.3 Lista de cards do deck (`GET /api/v1/cards/?deck_id=`), com estado vazio
- [ ] 4.4 Formulário de criação de card (word/translation/example/tags) dentro da tela de detalhe
- [ ] 4.5 Edição inline de card existente (mesmo padrão do deck)
- [ ] 4.6 Botão de excluir card, usando `ConfirmDialog`

## 5. Categoria — seletor e criação inline

- [ ] 5.1 Seletor de categoria no formulário de deck, populado via `fetchCategories`
- [ ] 5.2 Opção "+ nova categoria" no seletor, revelando um `Input` inline que cria via `createCategory` e seleciona o resultado automaticamente

## 6. Testes automatizados

- [ ] 6.1 Criação de deck: formulário válido cria e navega corretamente
- [ ] 6.2 Edição de deck: alterações são persistidas e refletidas na UI
- [ ] 6.3 Exclusão de deck: `ConfirmDialog` aparece, confirmação remove o deck da lista
- [ ] 6.4 Criação/edição/exclusão de card, mesmo padrão dos testes de deck
- [ ] 6.5 Categoria: seletor lista categorias existentes; criação inline seleciona a categoria nova automaticamente
- [ ] 6.6 Estados vazios (sem decks, sem cards) renderizam a mensagem correta, não uma lista vazia silenciosa

## 7. Documentação

- [ ] 7.1 Atualizar `PRD.md` (Sprint 7) marcando as tarefas concluídas
- [ ] 7.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 7]`
