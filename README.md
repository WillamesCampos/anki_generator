<div align="center">
    <img width="800" height="450" alt="Anki Generator Logo" src="https://github.com/user-attachments/assets/560c81d7-849d-41b8-a348-4dc08706628e" />
</div>

# 🎴 Anki Generator

Sistema de geração automática de baralhos Anki utilizando Inteligência Artificial. O projeto recebe um contexto (texto) e gera automaticamente cards de vocabulário em inglês com traduções, exemplos e áudio de pronúncia, prontos para importação no Anki.

## 📋 Sobre o Projeto

O **Anki Generator** é uma API REST desenvolvida em Python que automatiza a criação de baralhos de estudo para o Anki. Utilizando IA para gerar palavras relevantes baseadas em um contexto fornecido, o sistema cria cards completos com:

- **Palavra em inglês** (termo principal)
- **Tradução em português**
- **Exemplo de uso** (frase contextualizada)
- **Tradução do exemplo**
- **Áudio de pronúncia** (gerado automaticamente)

Tudo isso é armazenado em MongoDB e pode ser exportado como arquivo `.apkg` para importação direta no Anki.

## ✨ Funcionalidades

- 🤖 **Geração via IA**: Gera palavras relevantes baseadas em contexto usando OpenAI
- 🔊 **Áudio Automático**: Gera pronúncia de cada palavra usando gTTS
- 🗄️ **Persistência**: Armazena decks, cards e sessões de geração no MongoDB
- 🔍 **Detecção de Duplicatas**: Evita criar cards repetidos
- ✅ **Validação de Qualidade**: Garante qualidade mínima dos cards gerados
- 📦 **Exportação Anki**: Gera arquivo `.apkg` pronto para importação
- 🎯 **Sessões de Geração**: Rastreia o processo de geração com status e histórico

## 🏗️ Arquitetura

O projeto segue os princípios de **Clean Architecture**, organizando o código em camadas bem definidas:

```
anki_generator/
├── domain/              # Camada de Domínio
│   ├── entities/        # Entidades de negócio (Card, Deck, GenerationSession)
│   ├── value_objects/   # Objetos de valor (Word, Translation, Example, AudioPath)
│   ├── repositories/    # Interfaces de repositórios
│   └── services/        # Serviços de domínio (qualidade, duplicatas)
│
├── application/         # Camada de Aplicação
│   ├── use_cases/      # Casos de uso (orquestração de lógica)
│   ├── dto/            # Data Transfer Objects
│   └── services/       # Serviços de aplicação
│
├── infrastructure/      # Camada de Infraestrutura
│   ├── database/       # MongoDB connection e schemas
│   ├── repositories/   # Implementações concretas dos repositórios
│   └── external_services/  # Integrações (OpenAI, gTTS)
│
└── presentation/       # Camada de Apresentação
    └── api/            # Flask API (routes, controllers, serializers)
```

### Princípios Aplicados

- **Dependency Rule**: Camadas externas dependem de camadas internas
- **Separation of Concerns**: Cada camada tem responsabilidade específica
- **Dependency Inversion**: Dependências apontam para abstrações (interfaces)
- **Single Responsibility**: Cada classe tem uma única responsabilidade

## 🛠️ Tecnologias

### Backend
- **Python 3.11+**: Linguagem principal
- **Flask**: Framework web para API REST
- **Motor**: Driver assíncrono para MongoDB
- **genanki**: Biblioteca para criação de arquivos Anki (.apkg)

### Banco de Dados
- **MongoDB**: Banco NoSQL para persistência

### Serviços Externos
- **OpenAI API**: Geração de palavras e conteúdo via IA
- **gTTS (Google Text-to-Speech)**: Geração de áudio de pronúncia

### Gerenciamento
- **Poetry**: Gerenciamento de dependências

## 🚀 Como Começar

### Pré-requisitos

- Python 3.11 ou superior
- MongoDB (local ou remoto)
- Conta OpenAI com API key
- Poetry instalado

### Instalação

1. **Clone o repositório**
   ```bash
   git clone <repository-url>
   cd anki_generator
   ```

2. **Instale as dependências**
   ```bash
   poetry install
   ```

3. **Configure as variáveis de ambiente**
   ```bash
   cp config.example.env .env
   ```
   
   Edite o arquivo `.env` com suas configurações:
   - MongoDB connection string
   - OpenAI API key
   - Configurações da aplicação

4. **Inicie o MongoDB** (se local)
   ```bash
   docker-compose up -d
   ```

5. **Execute a aplicação**
   ```bash
   poetry run python main.py
   ```

A API estará disponível em `http://localhost:8000`

## 📚 Estrutura do Projeto

### Domain Layer
Contém as regras de negócio puras, independentes de frameworks e bibliotecas:

- **Entities**: `Card`, `Deck`, `GenerationSession` - Entidades com identidade e regras de negócio
- **Value Objects**: `Word`, `Translation`, `Example`, `AudioPath` - Objetos imutáveis que representam conceitos
- **Repositories Interfaces**: Contratos para persistência (implementados na infrastructure)
- **Domain Services**: Lógica de negócio que não pertence a uma entidade específica

### Application Layer
Orquestra os casos de uso e coordena as camadas:

- **Use Cases**: Lógica de alto nível para cada funcionalidade (ex: `GenerateCardsUseCase`)
- **DTOs**: Estruturas de dados para comunicação entre camadas
- **Application Services**: Serviços que coordenam múltiplos use cases

### Infrastructure Layer
Implementa detalhes técnicos:

- **Database**: Conexão MongoDB, schemas, índices
- **Repositories**: Implementações concretas das interfaces do domain
- **External Services**: Integrações com OpenAI, gTTS, etc.

### Presentation Layer
Interface com o mundo externo:

- **API**: Endpoints Flask
- **Controllers**: Lógica de controle HTTP
- **Serializers**: Conversão entre DTOs e JSON

## 🔌 Endpoints da API

### Decks
- `POST /decks` - Criar novo deck
- `GET /decks/{id}` - Buscar deck por ID
- `GET /decks/{id}/cards` - Listar cards de um deck
- `POST /decks/{id}/generate` - Gerar cards para um deck
- `POST /decks/{id}/export` - Exportar deck como .apkg

### Sessões
- `GET /sessions/{id}` - Consultar status de sessão de geração

## 📖 Documentação Adicional

Para entender em detalhes as etapas de implementação e decisões arquiteturais, consulte:

- **[ETAPAS_PROJETO.md](./ETAPAS_PROJETO.md)**: Documento completo com todas as etapas de desenvolvimento, requisitos e guia de implementação

## 🧪 Desenvolvimento

### Estrutura de Testes
```
tests/
├── unit/           # Testes unitários por camada
├── integration/   # Testes de integração
└── e2e/           # Testes end-to-end
```

### Executar Testes
```bash
poetry run pytest
```

## 🔄 Fluxo de Geração de Cards

1. **Cliente** faz `POST /decks/{id}/generate` com contexto
2. **Controller** valida entrada e cria DTO
3. **Use Case** orquestra:
   - Busca deck no repositório
   - Cria sessão de geração
   - Chama serviço de IA para gerar palavras
   - Para cada palavra:
     - Cria card com value objects
     - Verifica duplicatas
     - Gera áudio
     - Valida qualidade
   - Salva cards no repositório
   - Atualiza deck e sessão
4. **Controller** retorna resposta serializada

## 🎯 Roadmap

- [x] Estrutura base de Clean Architecture
- [x] Entidades e Value Objects do domínio
- [x] Repositórios MongoDB
- [ ] Integração com OpenAI
- [ ] Serviço de geração de áudio
- [ ] Use Cases completos
- [ ] API Flask
- [ ] Exportação para Anki
- [ ] Testes automatizados
- [ ] Documentação da API (Swagger/OpenAPI)

## 🤝 Contribuindo

Este é um projeto de portfólio/estudo. Sinta-se à vontade para sugerir melhorias ou reportar issues.

## 📝 Licença

Este projeto é de uso pessoal/educacional.

## 👤 Autor

**Willames Campos**
- Email: willwjccampos@gmail.com

---

**Desenvolvido com foco em Clean Architecture e boas práticas de engenharia de software.**

