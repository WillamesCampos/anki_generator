## 1. API client — mutations

- [x] 1.1 `api/decks.js`: `createDeck`, `updateDeck`, `deleteDeck`
- [x] 1.2 `api/cards.js`: `createCard`, `updateCard`, `deleteCard`
- [x] 1.3 `api/categories.js` (novo): `fetchCategories`, `createCategory`

## 2. Componentes compartilhados

- [x] 2.1 `ConfirmDialog` (`components/ui/`) — confirmação reutilizável com mensagem de aviso da janela de retenção de 7 dias, construído com `Card`/`Button` já existentes (ver D3 em design.md)

## 3. Tela de listagem e criação de Deck

- [x] 3.1 Rota `/decks` substitui `<PlaceholderPage>` — lista os decks do usuário (`fetchDecks`), com estado vazio
- [x] 3.2 Rota `/decks/novo` — formulário de criação (título, descrição, categoria, `daily_review_goal`), usando o seletor de categoria (grupo 5)
- [x] 3.3 Após criação bem-sucedida, navega pro deck recém-criado ou de volta pra lista

## 4. Tela de detalhe do Deck — edição, exclusão e resumo de cards

- [x] 4.1 Rota `/decks/:deckId` — exibe dados do deck com edição inline (toggle, ver D1 em design.md)
- [x] 4.2 Botão de excluir deck, usando `ConfirmDialog` — `DELETE /api/v1/decks/{deck_id}/`
- [x] 4.3 Exibir somente a quantidade via `GET /api/v1/cards/count/?deck_id=`, sem buscar a lista
- [x] 4.4 Botão "Ver todos os cards" navega para `/decks/:deckId/cards`
- [x] 4.5 Página dedicada lista os cards e oferece criação/edição/exclusão

## 5. Categoria — seletor e criação inline

- [x] 5.1 Seletor de categoria no formulário de deck, populado via `fetchCategories`
- [x] 5.2 Opção "+ nova categoria" no seletor, revelando um `Input` inline que cria via `createCategory` e seleciona o resultado automaticamente

## 6. Testes automatizados

- [x] 6.1 Criação de deck: formulário válido cria e navega corretamente
- [x] 6.2 Edição de deck: alterações são persistidas e refletidas na UI
- [x] 6.3 Exclusão de deck: `ConfirmDialog` aparece, confirmação remove o deck da lista
- [x] 6.4 Criação/edição/exclusão de card, mesmo padrão dos testes de deck
- [x] 6.5 Categoria: seletor lista categorias existentes; criação inline seleciona a categoria nova automaticamente
- [x] 6.6 Estados vazios (sem decks, sem cards) renderizam a mensagem correta, não uma lista vazia silenciosa

## 7. Documentação

- [x] 7.1 Atualizar `PRD.md` (Sprint 7) marcando as tarefas concluídas
- [x] 7.2 Atualizar `CHANGELOG.md` com a entrada `[Sprint 7]`

## 8. Correções de integração backend

- [x] 8.1 Alterar os throttles `user` e `anon` para `10/second`, atualizando os testes de limite
- [x] 8.2 Executar chamadas Motor das views/serializers síncronos em event loop persistente e proteger a conexão inicial concorrente
- [x] 8.3 Cobrir detalhe + contagem concorrentes sem `500` e validar chamadas HTTP reais

## 9. Contrato de Card e contagem mínima

- [x] 9.1 Renomear `word` → `front`, `translation` → `back`, `example_original` → `front_description` e `example_translated` → `back_description` no domínio, Mongo e API Django
- [x] 9.2 Aplicar os mesmos nomes em inglês no frontend interno, document-generator, seed, serviços auxiliares e testes, mantendo apenas os rótulos visíveis em português
- [x] 9.3 Tornar o comando idempotente compatível com documentos legados e com a versão intermediária `frente`/`verso`/`descricao_frente`/`descricao_verso`, e executá-lo no ambiente local
- [x] 9.4 Criar `GET /api/v1/cards/count/?deck_id=`, retornando apenas `{ "count": N }` e usando `count_documents`
- [x] 9.5 Cobrir autorização/soft delete/shape mínimo do endpoint de contagem e rejeição dos nomes legados e intermediários no contrato

## 10. Testes frontend da navegação de cards

- [x] 10.1 Detalhe do deck consulta a contagem, não a listagem, e renderiza singular/plural/erro
- [x] 10.2 Botão "Ver todos os cards" aponta para a página dedicada
- [x] 10.3 Página dedicada cobre lista, estado vazio e criação/edição/exclusão com os quatro identificadores internos em inglês e rótulos em português

## 11. Formulário prioritário e paginação de cards

- [x] 11.1 Especificar e testar paginação dedicada de 10 itens em `GET /api/v1/cards/?deck_id=&page=` sem alterar o tamanho global
- [x] 11.2 Mover o formulário de criação para antes da lista em `/decks/:deckId/cards`
- [x] 11.3 Consumir `count`/`next`/`previous`, renderizar “Anterior”/“Próxima” e “Página X de Y” e recarregar página válida após mutations
- [x] 11.4 Cobrir no frontend ordem do formulário, duas páginas, estados dos controles, criação e exclusão na última página

## 12. Estatísticas históricas no detalhe do deck

- [x] 12.1 Antecipar, sem duplicar, o endpoint agregado `GET /api/v1/decks/{deck_id}/statistics/` especificado em `sprint-9-estatisticas-por-deck`
- [x] 12.2 Adicionar cliente API e gráfico Chart.js no detalhe com `Errou`/`Difícil`/`Bom`/`Fácil`
- [x] 12.3 Cobrir distribuição histórica, valores zerados, erro isolado e ausência de download de revisões cruas
- [x] 12.4 Fazer a Home usar `rating_distribution` do último deck estudado pelo mesmo endpoint do detalhe, sem somar revisões paginadas de outros decks
