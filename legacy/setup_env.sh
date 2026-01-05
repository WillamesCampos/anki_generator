#!/bin/bash

# Script para configurar variáveis de ambiente para o MongoDB Docker

echo "🔧 Configurando variáveis de ambiente..."

# Configurações do MongoDB (Docker Container)
export MONGODB_HOST=localhost
export MONGODB_PORT=27017
export MONGODB_USERNAME=anki_user
export MONGODB_PASSWORD=anki_password
export MONGODB_DATABASE=anki_generator
export MONGODB_AUTH_SOURCE=anki_generator
export MONGODB_MAX_POOL_SIZE=100
export MONGODB_MIN_POOL_SIZE=10
export MONGODB_SSL=false

# Configurações da aplicação
export APP_ENV=development
export APP_DEBUG=true
export APP_HOST=0.0.0.0
export APP_PORT=8000

# Configurações de geração de cards
export MAX_CARDS_PER_GENERATION=10
export CARD_QUALITY_THRESHOLD=0.7
export DUPLICATE_SIMILARITY_THRESHOLD=0.8

echo "✅ Variáveis de ambiente configuradas!"
echo "📋 Para usar, execute: source setup_env.sh"
