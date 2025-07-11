#!/usr/bin/env python3
"""
Teste rápido de conexão com OpenAI
==================================
"""

import asyncio
import os
from dotenv import load_dotenv

async def test_openai_connection():
    """Teste rápido de conexão"""
    
    print("TESTE DE CONEXÃO OPENAI")
    print("=" * 30)
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("[ERRO] OPENAI_API_KEY não encontrada")
        return
    
    print(f"API Key encontrada: {api_key[:10]}...")
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        print("Cliente OpenAI criado")
        
        # Teste simples
        print("Fazendo teste simples...")
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Diga apenas 'Teste bem-sucedido!'"}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"Resposta recebida: {result}")
        
        print("\nTeste de análise financeira básica...")
        
        # Teste com dados fictícios
        financial_prompt = """Analise brevemente estes dados financeiros fictícios:
        Receita: R$ 100M
        Lucro: R$ 10M
        Margem: 10%
        
        Dê uma análise em 2 frases."""
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um analista financeiro."},
                {"role": "user", "content": financial_prompt}
            ],
            max_tokens=100
        )
        
        analysis = response.choices[0].message.content
        print(f"Análise recebida: {analysis}")
        
        print("\nTODOS OS TESTES PASSARAM!")
        print("O Analysis Agent deve funcionar corretamente")
        
    except Exception as e:
        print(f"[ERRO] Teste falhou: {e}")
        
        # Tentar com requests como fallback
        print("\nTestando fallback com requests...")
        
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Responda apenas: OK"}
                ],
                "max_tokens": 5
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"Fallback funcionou: {content}")
            else:
                print(f"[ERRO] HTTP: {response.status_code}")
                print(f"Resposta: {response.text}")
                
        except Exception as e2:
            print(f"[ERRO] Fallback falhou: {e2}")

if __name__ == "__main__":
    asyncio.run(test_openai_connection())