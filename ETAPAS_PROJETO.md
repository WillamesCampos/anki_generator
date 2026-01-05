# Etapas do Projeto - Anki Generator

## 📋 Visão Geral

Este documento descreve todas as etapas necessárias para implementar o sistema de geração de baralhos Anki usando IA, seguindo os princípios de **Clean Architecture**.

**Objetivo**: Criar uma API Flask que recebe um contexto, utiliza IA para gerar palavras relevantes, cria cards Anki com áudio e armazena tudo no MongoDB.

---

## 🎯 Requisitos Funcionais Identificados

### RF01 - Geração de Cards via IA
- **Descrição**: Sistema deve receber um contexto (texto) e gerar palavras relevantes usando IA
- **Entrada**: Contexto (string), quantidade de cards desejada (opcional, padrão: 10)
- **Saída**: Lista de cards com palavra, tradução, exemplo e tradução do exemplo
- **Regras**:
  - Evitar duplicatas (verificar palavras já existentes no deck)
  - Garantir qualidade mínima dos cards gerados
  - Cada card deve ter contexto associado

### RF02 - Geração de Áudio
- **Descrição**: Gerar arquivo de áudio para pronúncia de cada palavra
- **Entrada**: Palavra em inglês
- **Saída**: Arquivo de áudio (.mp3) e caminho armazenado
- **Regras**:
  - Usar gTTS (já implementado parcialmente)
  - Armazenar caminho do arquivo no card
  - Evitar gerar áudio duplicado para mesma palavra

### RF03 - Persistência em MongoDB
- **Descrição**: Armazenar decks, cards e sessões de geração
- **Entidades**: Deck, Card, GenerationSession
- **Regras**:
  - Cards devem ser associados a um deck
  - Sessões de geração devem rastrear o processo
  - Índices otimizados para buscas frequentes

### RF04 - API REST com Flask
- **Descrição**: Expor endpoints para interação com o sistema
- **Endpoints principais**:
  - `POST /decks` - Criar novo deck
  - `GET /decks/{id}` - Buscar deck por ID
  - `POST /decks/{id}/generate` - Gerar cards para um deck
  - `GET /decks/{id}/cards` - Listar cards de um deck
  - `GET /sessions/{id}` - Consultar status de sessão de geração
  - `POST /decks/{id}/export` - Exportar deck como arquivo .apkg do Anki

### RF05 - Validação e Qualidade
- **Descrição**: Garantir qualidade dos cards gerados
- **Regras**:
  - Detectar duplicatas antes de salvar
  - Validar formato e conteúdo dos cards
  - Verificar similaridade entre cards

---

## 🏗️ Requisitos Não-Funcionais

### RNF01 - Arquitetura
- **Clean Architecture** com separação clara de camadas:
  - **Domain**: Entidades, Value Objects, Interfaces de Repositórios, Domain Services
  - **Application**: Use Cases, DTOs, Application Services
  - **Infrastructure**: Implementações de Repositórios, MongoDB, Serviços Externos (IA, Áudio)
  - **Presentation**: FastAPI, API, Controllers, Serializers

### RNF02 - Tecnologias
- **Backend**: Python 3.11+, FastAPI
- **Banco de Dados**: MongoDB (Motor para async)
- **IA**: OpenAI API (ou alternativa)
- **Áudio**: gTTS
- **Anki**: genanki library

### RNF03 - Qualidade de Código
- Código testável e desacoplado
- Type hints em todas as funções
- Tratamento de erros adequado
- Logging para debugging e observabilidade

---

## 📐 Estrutura de Camadas (Clean Architecture)

```
anki_generator/
├── domain/                    # Camada de Domínio (já existe parcialmente)
│   ├── entities/             # Entidades de negócio (Card, Deck, GenerationSession)
│   ├── value_objects/         # Objetos de valor (Word, Translation, Example, AudioPath)
│   ├── repositories/         # Interfaces de repositórios (ICardRepository, etc.)
│   └── services/             # Serviços de domínio (CardQualityService, DuplicateDetectionService)
│
├── application/              # Camada de Aplicação (PRECISA SER IMPLEMENTADA)
│   ├── use_cases/           # Casos de uso (GenerateCardsUseCase, CreateDeckUseCase, etc.)
│   ├── dto/                 # Data Transfer Objects (CreateDeckDTO, GenerateCardsDTO, etc.)
│   └── services/            # Serviços de aplicação (AIService, AudioService wrapper)
│
├── infrastructure/           # Camada de Infraestrutura (parcialmente implementada)
│   ├── database/            # MongoDB connection, schemas
│   ├── repositories/        # Implementações concretas dos repositórios
│   └── external_services/   # Integrações externas (OpenAI, gTTS)
│
└── presentation/            # Camada de Apresentação (PRECISA SER IMPLEMENTADA)
    └── api/                 # Flask routes, controllers, serializers
        ├── routes/          # Definição de rotas
        ├── controllers/     # Lógica de controle HTTP
        └── serializers/     # Serialização de requests/responses
```

---

## 🚀 Etapas de Implementação

### **FASE 1: Preparação e Estrutura Base** ⚙️

#### Etapa 1.1: Revisar e Completar Domain Layer
**Objetivo**: Garantir que todas as entidades, value objects e interfaces estão completas.

**Tarefas**:
- [ ] Revisar entidades existentes (Card, Deck, GenerationSession)
- [ ] Verificar se todos os value objects estão implementados corretamente
- [ ] Validar interfaces de repositórios (ICardRepository, IDeckRepository, IGenerationSessionRepository)
- [ ] Garantir que domain services (CardQualityService, DuplicateDetectionService) estão funcionais

**Perguntas para reflexão**:
- As validações de negócio estão nas entidades corretas?
- Os value objects são imutáveis?
- As interfaces de repositório cobrem todos os casos de uso necessários?

---

#### Etapa 1.2: Configurar Dependências e Ambiente
**Objetivo**: Garantir que todas as dependências necessárias estão configuradas.

**Tarefas**:
- [ ] Adicionar FAST API ao `pyproject.toml`
- [ ] Adicionar biblioteca de IA (openai ou alternativa)
- [ ] Configurar variáveis de ambiente (`.env`)
- [ ] Validar conexão MongoDB
- [ ] Criar script de inicialização do projeto

**Dependências sugeridas**:
```toml
flask = "^3.0.0"
flask-cors = "^4.0.0"  # Para CORS se necessário
openai = "^1.0.0"      # Para integração com OpenAI
pydantic = "^2.0.0"     # Para validação de DTOs (opcional, mas recomendado)
```

---

### **FASE 2: Infrastructure Layer - Serviços Externos** 🔌

#### Etapa 2.1: Implementar Serviço de IA
**Objetivo**: Criar abstração para integração com IA (OpenAI).

**Localização**: `infrastructure/external_services/ai_service.py`

**Tarefas**:
- [ ] Criar interface/abstração para serviço de IA (pode ser uma classe abstrata)
- [ ] Implementar `OpenAIService` que:
  - Recebe contexto e quantidade de cards
  - Gera prompt estruturado
  - Chama API da OpenAI
  - Parseia resposta e retorna lista de palavras com traduções e exemplos
- [ ] Tratar erros de API (rate limit, timeout, etc.)
- [ ] Adicionar retry logic com backoff exponencial
- [ ] Implementar logging

**Estrutura sugerida**:
```python
# infrastructure/external_services/ai_service.py
class AIService:
    async def generate_words_from_context(
        self, 
        context: str, 
        max_words: int = 10
    ) -> List[Dict[str, str]]:
        """
        Gera palavras baseadas em contexto.
        Retorna lista de dicionários com: word, translation, example, example_translation
        """
        pass
```

**Perguntas para reflexão**:
- Como estruturar o prompt para obter respostas consistentes?
- Como tratar casos onde a IA retorna menos palavras que o solicitado?
- Como validar a qualidade das respostas da IA?

---

#### Etapa 2.2: Completar Serviço de Áudio
**Objetivo**: Finalizar implementação do gerador de áudio.

**Localização**: `infrastructure/external_services/audio_service.py` (ou refatorar o existente)

**Tarefas**:
- [ ] Refatorar `AudioGenerator` existente para seguir Clean Architecture
- [ ] Mover para `infrastructure/external_services/`
- [ ] Implementar método para gerar áudio de uma palavra
- [ ] Implementar método batch para gerar múltiplos áudios
- [ ] Gerenciar armazenamento de arquivos (pasta de áudios)
- [ ] Retornar `AudioPath` value object
- [ ] Tratar erros (falha na geração, espaço em disco, etc.)

**Considerações**:
- Onde armazenar os arquivos de áudio? (local, S3, etc.)
- Como nomear arquivos para evitar conflitos?
- Como limpar áudios antigos/não utilizados?

---

#### Etapa 2.3: Validar Repositórios MongoDB
**Objetivo**: Garantir que implementações de repositórios estão completas e funcionais.

**Tarefas**:
- [ ] Revisar `CardRepository` em `infrastructure/repositories/card_repository.py`
- [ ] Revisar `DeckRepository` em `infrastructure/repositories/deck_repository.py`
- [ ] Revisar `GenerationSessionRepository` em `infrastructure/repositories/generation_session_repository.py`
- [ ] Testar operações CRUD básicas
- [ ] Validar mapeamento entre entidades de domínio e documentos MongoDB
- [ ] Garantir que índices estão sendo criados corretamente

---

### **FASE 3: Application Layer - Use Cases e DTOs** 🎯

#### Etapa 3.1: Criar DTOs (Data Transfer Objects)
**Objetivo**: Definir estruturas de dados para comunicação entre camadas.

**Localização**: `application/dto/`

**DTOs necessários**:
- [ ] `CreateDeckDTO`: `title`, `description` (opcional)
- [ ] `GenerateCardsDTO`: `context`, `max_cards` (opcional), `deck_id`
- [ ] `CardResponseDTO`: Representação de card para resposta da API
- [ ] `DeckResponseDTO`: Representação de deck para resposta da API
- [ ] `GenerationSessionResponseDTO`: Status e informações da sessão

**Estrutura sugerida**:
```python
# application/dto/create_deck_dto.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class CreateDeckDTO:
    title: str
    description: Optional[str] = None
```

**Perguntas para reflexão**:
- DTOs devem ter validação? (usar Pydantic ou dataclasses com validação manual?)
- Como mapear entidades de domínio para DTOs?
- Onde colocar a lógica de mapeamento?

---

#### Etapa 3.2: Implementar Use Cases
**Objetivo**: Implementar a lógica de negócio de alto nível (orquestração).

**Localização**: `application/use_cases/`

**Use Cases necessários**:

1. **CreateDeckUseCase**
   - [ ] Recebe `CreateDeckDTO`
   - [ ] Cria entidade `Deck`
   - [ ] Salva via `IDeckRepository`
   - [ ] Retorna `DeckResponseDTO`

2. **GenerateCardsUseCase** (O MAIS COMPLEXO)
   - [ ] Recebe `GenerateCardsDTO` (context, deck_id, max_cards)
   - [ ] Valida se deck existe
   - [ ] Cria `GenerationSession` com status PENDING
   - [ ] Chama `AIService` para gerar palavras
   - [ ] Para cada palavra gerada:
     - [ ] Cria entidade `Card` com value objects
     - [ ] Verifica duplicatas usando `DuplicateDetectionService`
     - [ ] Gera áudio usando `AudioService`
     - [ ] Valida qualidade usando `CardQualityService`
     - [ ] Adiciona card à sessão
   - [ ] Salva cards no repositório
   - [ ] Atualiza deck com novos cards
   - [ ] Marca sessão como COMPLETED ou FAILED
   - [ ] Retorna `GenerationSessionResponseDTO`

3. **GetDeckUseCase**
   - [ ] Recebe deck_id
   - [ ] Busca deck via repositório
   - [ ] Busca cards do deck
   - [ ] Retorna `DeckResponseDTO`

4. **GetDeckCardsUseCase**
   - [ ] Recebe deck_id
   - [ ] Busca cards do deck
   - [ ] Retorna lista de `CardResponseDTO`

5. **GetGenerationSessionUseCase**
   - [ ] Recebe session_id
   - [ ] Busca sessão via repositório
   - [ ] Retorna `GenerationSessionResponseDTO`

6. **ExportDeckUseCase**
   - [ ] Recebe deck_id
   - [ ] Busca deck e cards
   - [ ] Usa `genanki` para criar arquivo .apkg
   - [ ] Retorna caminho do arquivo ou bytes

**Estrutura sugerida**:
```python
# application/use_cases/generate_cards_use_case.py
class GenerateCardsUseCase:
    def __init__(
        self,
        deck_repository: IDeckRepository,
        card_repository: ICardRepository,
        session_repository: IGenerationSessionRepository,
        ai_service: AIService,
        audio_service: AudioService,
        duplicate_service: DuplicateDetectionService,
        quality_service: CardQualityService
    ):
        # Injeção de dependências
        pass
    
    async def execute(self, dto: GenerateCardsDTO) -> GenerationSessionResponseDTO:
        # Lógica do use case
        pass
```

**Perguntas para reflexão**:
- Como tratar erros parciais? (ex: 8 de 10 cards gerados com sucesso)
- Devo usar transações? (MongoDB suporta, mas é necessário?)
- Como tornar o processo assíncrono se necessário? (background jobs)

---

#### Etapa 3.3: Criar Application Services (se necessário)
**Objetivo**: Serviços de aplicação que orquestram múltiplos use cases ou fornecem funcionalidades transversais.

**Tarefas**:
- [ ] Avaliar se precisa de services além dos use cases
- [ ] Implementar serviços de mapeamento (Entity → DTO)
- [ ] Implementar serviços de validação de entrada

---

### **FASE 4: Presentation Layer - Flask API** 🌐

#### Etapa 4.1: Configurar Flask App
**Objetivo**: Estruturar aplicação Flask seguindo boas práticas.

**Localização**: `presentation/api/`

**Tarefas**:
- [ ] Criar `app.py` ou `__init__.py` com factory pattern do Flask
- [ ] Configurar CORS (se necessário)
- [ ] Configurar error handlers globais
- [ ] Configurar logging
- [ ] Criar blueprint para organização de rotas

**Estrutura sugerida**:
```python
# presentation/api/app.py
from flask import Flask
from flask_cors import CORS

def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)  # Se necessário
    
    # Registrar blueprints
    from presentation.api.routes import decks_bp
    app.register_blueprint(decks_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404
    
    return app
```

---

#### Etapa 4.2: Criar Serializers
**Objetivo**: Converter entre DTOs e JSON (requests/responses).

**Localização**: `presentation/api/serializers/`

**Tarefas**:
- [ ] Criar serializers para cada DTO
- [ ] Implementar validação de entrada (usar Pydantic ou validação manual)
- [ ] Tratar erros de serialização

**Exemplo**:
```python
# presentation/api/serializers/deck_serializer.py
def serialize_deck_response(dto: DeckResponseDTO) -> dict:
    return {
        "id": str(dto.id),
        "title": dto.title,
        "description": dto.description,
        "card_count": dto.card_count,
        "created_at": dto.created_at.isoformat()
    }
```

---

#### Etapa 4.3: Criar Controllers
**Objetivo**: Implementar lógica de controle HTTP (chamar use cases).

**Localização**: `presentation/api/controllers/`

**Tarefas**:
- [ ] Criar `DeckController`:
  - [ ] `create_deck()` - POST /decks
  - [ ] `get_deck()` - GET /decks/{id}
  - [ ] `get_deck_cards()` - GET /decks/{id}/cards
  - [ ] `export_deck()` - POST /decks/{id}/export
- [ ] Criar `GenerationController`:
  - [ ] `generate_cards()` - POST /decks/{id}/generate
  - [ ] `get_session()` - GET /sessions/{id}
- [ ] Implementar tratamento de erros HTTP
- [ ] Retornar status codes apropriados
- [ ] Validar entrada antes de chamar use cases

**Estrutura sugerida**:
```python
# presentation/api/controllers/deck_controller.py
class DeckController:
    def __init__(self, create_deck_use_case, get_deck_use_case, ...):
        # Injeção de dependências
        pass
    
    def create_deck(self, request_data: dict):
        # Validar request_data
        # Criar DTO
        # Chamar use case
        # Serializar resposta
        # Retornar JSON response
        pass
```

---

#### Etapa 4.4: Criar Rotas
**Objetivo**: Definir endpoints da API.

**Localização**: `presentation/api/routes/`

**Tarefas**:
- [ ] Criar blueprint `decks_bp` com rotas:
  - [ ] `POST /decks`
  - [ ] `GET /decks/<deck_id>`
  - [ ] `GET /decks/<deck_id>/cards`
  - [ ] `POST /decks/<deck_id>/generate`
  - [ ] `POST /decks/<deck_id>/export`
- [ ] Criar blueprint `sessions_bp` com rotas:
  - [ ] `GET /sessions/<session_id>`
- [ ] Implementar validação de parâmetros de rota
- [ ] Adicionar documentação básica (docstrings)

**Estrutura sugerida**:
```python
# presentation/api/routes/decks.py
from flask import Blueprint, request, jsonify
from presentation.api.controllers.deck_controller import DeckController

decks_bp = Blueprint('decks', __name__, url_prefix='/decks')

@decks_bp.route('', methods=['POST'])
def create_deck():
    # Lógica do endpoint
    pass
```

---

#### Etapa 4.5: Configurar Dependency Injection
**Objetivo**: Conectar todas as camadas (instanciar repositórios, use cases, controllers).

**Localização**: `presentation/api/dependencies.py` ou `main.py`

**Tarefas**:
- [ ] Criar função que instancia todos os repositórios
- [ ] Criar função que instancia todos os use cases
- [ ] Criar função que instancia todos os controllers
- [ ] Configurar injeção de dependências (pode ser manual ou usar biblioteca)

**Exemplo**:
```python
# presentation/api/dependencies.py
from infrastructure.repositories.card_repository import CardRepository
from infrastructure.external_services.ai_service import AIService
from application.use_cases.generate_cards_use_case import GenerateCardsUseCase

def setup_dependencies():
    # Repositórios
    card_repo = CardRepository(mongodb_manager)
    deck_repo = DeckRepository(mongodb_manager)
    
    # Serviços externos
    ai_service = AIService(openai_api_key)
    audio_service = AudioService()
    
    # Use cases
    generate_cards_uc = GenerateCardsUseCase(
        deck_repo, card_repo, session_repo,
        ai_service, audio_service, ...
    )
    
    # Controllers
    deck_controller = DeckController(...)
    
    return {
        'deck_controller': deck_controller,
        ...
    }
```

---

### **FASE 5: Integração e Testes** 🧪

#### Etapa 5.1: Criar Script de Inicialização
**Objetivo**: Facilitar inicialização do projeto.

**Tarefas**:
- [ ] Criar `main.py` na raiz que:
  - [ ] Conecta ao MongoDB
  - [ ] Cria índices
  - [ ] Inicializa Flask app
  - [ ] Roda servidor
- [ ] Criar script de setup (instalar dependências, configurar .env)

---

#### Etapa 5.2: Testes de Integração
**Objetivo**: Validar fluxo completo end-to-end.

**Tarefas**:
- [ ] Testar criação de deck via API
- [ ] Testar geração de cards via API
- [ ] Testar exportação de deck
- [ ] Validar persistência no MongoDB
- [ ] Testar tratamento de erros

---

#### Etapa 5.3: Documentação da API
**Objetivo**: Documentar endpoints para uso.

**Tarefas**:
- [ ] Criar documentação básica (README atualizado ou arquivo separado)
- [ ] Documentar todos os endpoints
- [ ] Incluir exemplos de requests/responses
- [ ] Documentar códigos de erro

---

## 🔄 Fluxo Completo de Geração de Cards

```
1. Cliente faz POST /decks/{id}/generate
   └─> { "context": "backend development", "max_cards": 10 }

2. Controller valida entrada e cria GenerateCardsDTO

3. GenerateCardsUseCase.execute():
   a. Busca deck no repositório
   b. Cria GenerationSession (status: PENDING)
   c. Chama AIService.generate_words_from_context()
   d. Para cada palavra retornada:
      - Cria Card com value objects
      - Verifica duplicatas (DuplicateDetectionService)
      - Gera áudio (AudioService)
      - Valida qualidade (CardQualityService)
      - Adiciona à sessão
   e. Salva cards no repositório
   f. Atualiza deck
   g. Marca sessão como COMPLETED
   h. Retorna DTO da sessão

4. Controller serializa resposta e retorna JSON

5. Cliente pode consultar status em GET /sessions/{id}
```

---

## 🎓 Conceitos de Clean Architecture a Aplicar

### 1. **Dependency Rule**
- Camadas externas dependem de camadas internas
- Domain não depende de nada
- Application depende apenas de Domain
- Infrastructure e Presentation dependem de Application e Domain

### 2. **Separation of Concerns**
- Domain: Regras de negócio puras
- Application: Orquestração e casos de uso
- Infrastructure: Detalhes técnicos (banco, APIs externas)
- Presentation: Interface com usuário (HTTP)

### 3. **Dependency Inversion**
- Use interfaces (repositórios) no domain
- Implemente interfaces na infrastructure
- Injetar dependências nos use cases

### 4. **Single Responsibility**
- Cada classe tem uma responsabilidade clara
- Use cases são específicos e focados
- Controllers apenas coordenam, não contêm lógica de negócio

---

## ⚠️ Pontos de Atenção

1. **Assíncrono vs Síncrono**
   - MongoDB usa Motor (async), mas Flask é síncrono por padrão
   - Decisão: Usar Flask com async/await ou wrapper síncrono?
   - Recomendação: Usar `flask[async]` ou biblioteca compatível

2. **Geração de Áudio**
   - Pode ser lento para muitos cards
   - Considerar processamento assíncrono/background jobs
   - Gerenciar espaço em disco

3. **Rate Limiting da IA**
   - OpenAI tem limites de requisições
   - Implementar retry com backoff
   - Considerar cache de palavras geradas

4. **Validação de Entrada**
   - Validar DTOs antes de passar para use cases
   - Retornar erros HTTP apropriados (400, 404, 500)

5. **Tratamento de Erros**
   - Erros de domínio vs erros de infraestrutura
   - Mapear exceções de domínio para HTTP status codes
   - Logging adequado

---

## 📝 Checklist Final

Antes de considerar o projeto completo, verificar:

- [ ] Todas as entidades de domínio estão implementadas e validadas
- [ ] Todos os repositórios estão implementados e testados
- [ ] Serviços externos (IA, Áudio) estão funcionais
- [ ] Todos os use cases estão implementados
- [ ] API Flask está completa e funcional
- [ ] Tratamento de erros está adequado
- [ ] Logging está configurado
- [ ] Documentação está atualizada
- [ ] Testes básicos de integração passam
- [ ] Projeto segue princípios de Clean Architecture

---

## 🚦 Próximos Passos Imediatos

1. **Começar pela Fase 1**: Revisar e completar Domain Layer
2. **Depois Fase 2**: Implementar serviços externos (IA e Áudio)
3. **Em seguida Fase 3**: Criar DTOs e Use Cases
4. **Por fim Fase 4**: Implementar API Flask

**Lembre-se**: Não implemente tudo de uma vez. Faça incrementalmente, testando cada etapa antes de avançar.

---

## 💡 Dicas de Arquitetura

- **Sempre pense**: "O que acontece se esse serviço falhar?"
- **Sempre pergunte**: "Como testar isso de forma isolada?"
- **Sempre considere**: "Isso viola a Dependency Rule?"
- **Sempre valide**: "Essa lógica está na camada correta?"

---

**Documento criado por**: Morgan Cursor  
**Data**: 2024  
**Versão**: 1.0

