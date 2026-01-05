"""
Teste simples para verificar a conexão MongoDB
"""

import asyncio
from infrastructure.database.mongodb_connection import ensure_mongodb_connection

async def test_simple():
    print("🔌 Testando conexão simples...")
    
    try:
        mongodb_manager = await ensure_mongodb_connection()
        health = await mongodb_manager.health_check()
        
        print(f"✅ MongoDB conectado: {health['status']}")
        
        # Testa inserção simples
        collection = await mongodb_manager.get_collection("test")
        result = await collection.insert_one({"test": "value"})
        print(f"✅ Documento inserido: {result.inserted_id}")
        
        # Busca o documento
        doc = await collection.find_one({"_id": result.inserted_id})
        print(f"✅ Documento encontrado: {doc}")
        
        # Remove o documento de teste
        await collection.delete_one({"_id": result.inserted_id})
        print("✅ Documento removido")
        
        await mongodb_manager.disconnect()
        print("✅ Teste simples concluído!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple())
