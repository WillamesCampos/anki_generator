// Script de inicialização do banco de dados MongoDB
// Este script é executado automaticamente quando o container MongoDB é criado

// Conecta ao banco de dados anki_generator
db = db.getSiblingDB('anki_generator');

// Cria usuário específico para a aplicação
db.createUser({
  user: 'anki_user',
  pwd: 'anki_password',
  roles: [
    {
      role: 'readWrite',
      db: 'anki_generator'
    }
  ]
});

// Cria as collections principais
db.createCollection('cards');
db.createCollection('decks');
db.createCollection('generation_sessions');

// Cria índices para otimização de consultas

// Índices para collection cards
db.cards.createIndex({ "deck_id": 1 });
db.cards.createIndex({ "word.normalized": 1 });
db.cards.createIndex({ "created_at": 1 });
db.cards.createIndex({ "updated_at": 1 });
db.cards.createIndex({ "context": 1 });
db.cards.createIndex({ "deck_id": 1, "word.normalized": 1 }, { unique: true });
db.cards.createIndex({ "deck_id": 1, "created_at": 1 });

// Índices para collection decks
db.decks.createIndex({ "title": 1 });
db.decks.createIndex({ "created_at": 1 });
db.decks.createIndex({ "updated_at": 1 });
db.decks.createIndex({ "card_count": 1 });

// Índices para collection generation_sessions
db.generation_sessions.createIndex({ "deck_id": 1 });
db.generation_sessions.createIndex({ "status": 1 });
db.generation_sessions.createIndex({ "created_at": 1 });
db.generation_sessions.createIndex({ "updated_at": 1 });
db.generation_sessions.createIndex({ "completed_at": 1 });
db.generation_sessions.createIndex({ "deck_id": 1, "status": 1 });
db.generation_sessions.createIndex({ "deck_id": 1, "created_at": -1 });

print('✅ Banco de dados anki_generator inicializado com sucesso!');
print('✅ Usuário anki_user criado');
print('✅ Collections criadas: cards, decks, generation_sessions');
print('✅ Índices criados para otimização');
