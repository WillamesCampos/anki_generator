## ADDED Requirements

### Requirement: Acesso síncrono ao MongoDB via pymongo
O sistema SHALL persistir e consultar decks, cards, categories, card reviews e generation sessions usando `pymongo.MongoClient` (driver síncrono), sem depender de nenhum event loop `asyncio` nem de qualquer camada de ponte sync↔async.

#### Scenario: Repositório executa uma consulta a partir de uma view síncrona do Django
- **WHEN** uma view síncrona do Django (WSGI) chama um método de um repositório de `apps/decks` (ex.: `DeckRepository.find_by_id`)
- **THEN** a operação MongoDB SHALL ser executada diretamente, de forma bloqueante, na mesma thread da requisição, sem passar por nenhuma ponte de execução assíncrona

#### Scenario: Repositório executa uma consulta a partir de uma task Celery
- **WHEN** uma task Celery (ex.: `purge_soft_deleted`) chama um método de repositório
- **THEN** a operação MongoDB SHALL ser executada diretamente, sem nenhuma ponte de execução assíncrona, no mesmo processo/thread do worker Celery

### Requirement: Conexão única e thread-safe por processo
O sistema SHALL manter um único `pymongo.MongoClient` por processo, criado de forma lazy (na primeira operação que precisar dele) e protegido por uma trava de concorrência baseada em `threading`, garantindo que requisições concorrentes não criem múltiplos clients simultaneamente.

#### Scenario: Múltiplas requisições concorrentes chegam antes de qualquer conexão existir
- **WHEN** duas ou mais threads de requisição chamam `ensure_mongodb_connection()` (ou equivalente) simultaneamente, sem nenhuma conexão MongoDB estabelecida ainda no processo
- **THEN** exatamente um `pymongo.MongoClient` SHALL ser criado, e todas as threads SHALL reutilizar essa mesma instância após ela existir

### Requirement: Isolamento por dono nas queries MongoDB
O sistema SHALL continuar embutindo o filtro por `owner_id` diretamente em cada query MongoDB, nunca buscando um documento sem esse filtro e checando o dono depois em memória — esse requisito é preservado da implementação assíncrona anterior, não uma mudança de comportamento.

#### Scenario: Busca de um recurso que pertence a outro usuário
- **WHEN** um usuário autenticado solicita um deck/card/category cujo `owner_id` não é o dele
- **THEN** a query MongoDB SHALL retornar nenhum documento (não encontra, não retorna e depois filtra), preservando o comportamento de 404 já existente na view

### Requirement: Criação de índices via API síncrona do pymongo
O sistema SHALL criar os índices definidos em `IndexDefinitions` usando os métodos síncronos do pymongo (`collection.create_index(...)`), preservando o mesmo conjunto de índices e opções hoje criados via Motor.

#### Scenario: Inicialização de índices em ambiente novo
- **WHEN** o comando/rotina de criação de índices é executado contra uma instância MongoDB sem os índices do sistema
- **THEN** todos os índices declarados em `IndexDefinitions.get_all_indexes()` SHALL ser criados, com as mesmas chaves e opções da implementação anterior

### Requirement: Seed e migração de dados em lote, sem paralelismo assíncrono
Os management commands `seed_decks` e `migrate_card_fields` SHALL usar operações em lote síncronas do pymongo (ex.: `insert_many`/`bulk_write`) para inserir/atualizar múltiplos documentos, sem depender de `asyncio.gather` ou qualquer concorrência baseada em corrotinas.

#### Scenario: Seed de um usuário com múltiplos decks e cards
- **WHEN** o comando `seed_decks` popula decks e cards para um usuário
- **THEN** as inserções SHALL ser feitas via operação(ões) em lote do pymongo, produzindo o mesmo conjunto final de documentos que a versão anterior baseada em `asyncio.gather`
