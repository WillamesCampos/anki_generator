## ADDED Requirements

### Requirement: Home oferece um caminho direto pro último deck estudado
O sistema SHALL exibir, dentro do card "Último deck estudado" da Home, um botão "Continuar estudando" que navega pra `/decks/{deckId}/estudar` do deck mais recentemente estudado, apenas quando esse deck existe e está acessível.

#### Scenario: Usuário com histórico de estudo vê o botão
- **WHEN** um usuário autenticado com pelo menos uma revisão registrada acessa a Home, e o deck da revisão mais recente ainda existe e pertence a ele
- **THEN** o card "Último deck estudado" mostra um botão "Continuar estudando" que navega pra `/decks/{deckId}/estudar` daquele deck

#### Scenario: Usuário sem nenhuma revisão não vê o botão
- **WHEN** um usuário autenticado sem nenhuma revisão registrada acessa a Home
- **THEN** o card "Último deck estudado" não mostra o botão "Continuar estudando" (mantém a mensagem de estado vazio já existente)

#### Scenario: Deck da revisão mais recente não está mais acessível
- **WHEN** o deck da revisão mais recente do usuário foi soft-deletado ou não pode ser carregado
- **THEN** o card "Último deck estudado" não mostra o botão "Continuar estudando"

### Requirement: Home sempre oferece um caminho pra escolher outro deck
O sistema SHALL exibir, na Home, um CTA secundário que navega pra `/decks`, independentemente de existir ou não um "último deck estudado" — com textos distintos para cada caso.

#### Scenario: CTA com deck recente existente
- **WHEN** a Home tem um "último deck estudado" válido
- **THEN** o CTA secundário mostra o texto "Não é o deck que deseja estudar agora? Escolha o seu deck!" e navega pra `/decks`

#### Scenario: CTA sem deck recente (usuário novo ou deck indisponível)
- **WHEN** a Home não tem um "último deck estudado" válido (zero revisões, ou deck soft-deletado/inacessível)
- **THEN** o CTA secundário mostra o texto "Escolha um deck pra começar a estudar!" e navega pra `/decks`

### Requirement: Listagem de decks permite estudar cada deck diretamente
O sistema SHALL exibir, em cada item de `/decks`, um botão "Estudar" que navega pra `/decks/{deckId}/estudar` daquele deck específico, ao lado do botão "Abrir deck" já existente — sem checar previamente se o deck tem cards devidos.

#### Scenario: Botão "Estudar" presente em todo deck da listagem
- **WHEN** um usuário autenticado acessa `/decks` e tem pelo menos um deck
- **THEN** cada item da listagem mostra um botão "Estudar" que navega pra `/decks/{deckId}/estudar` daquele deck, sem nenhuma requisição adicional pra verificar cards devidos antes de navegar

### Requirement: Menu lateral não duplica o caminho até os decks
O sistema SHALL NOT adicionar um item de menu lateral cujo destino seja idêntico ao item "Decks" já existente.

#### Scenario: Nenhum item novo de menu lateral para estudo
- **WHEN** um usuário autenticado visualiza o menu lateral
- **THEN** a lista de itens de navegação permanece a mesma de antes desta mudança (sem um item "Estudar" separado apontando pra `/decks`)
