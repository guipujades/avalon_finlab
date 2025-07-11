#!/usr/bin/env python3
"""
Teste otimizado do Analysis Agent
================================
Versão que processa apenas partes essenciais dos dados
"""

import asyncio
import os
from pathlib import Path
from analysis_agent import ChimpaAnalysisAgent

async def test_optimized():
    """Teste com dados reduzidos para análise rápida"""
    
    print("TESTE OTIMIZADO DO ANALYSIS AGENT")
    print("=" * 50)
    
    # Encontrar arquivo de valuation
    data_dir = Path("data")
    valuation_files = list(data_dir.glob("*_COMPLETO.txt"))
    
    if not valuation_files:
        print("[ERRO] Nenhum arquivo de valuation encontrado")
        return
    
    valuation_file = valuation_files[0]
    print(f"Arquivo: {valuation_file.name}")
    
    # Carregar e processar dados essenciais
    with open(valuation_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extrair apenas seções essenciais (primeiro 1000 caracteres + dados de mercado)
    lines = content.split('\n')
    
    # Identificar empresa
    empresa = "Empresa não identificada"
    for line in lines[:10]:
        if "VALUATION TEMPORAL -" in line:
            parts = line.split(' - ')
            if len(parts) > 1:
                empresa = parts[1].split('(')[0].strip()
                break
    
    # Extrair dados principais das primeiras seções
    essential_data = []
    essential_data.extend(lines[:20])  # Header
    
    # Procurar estatísticas dos últimos 5 anos
    for i, line in enumerate(lines):
        if "ESTATÍSTICAS DOS ÚLTIMOS 5 ANOS" in line:
            essential_data.extend(lines[i:i+50])  # Próximas 50 linhas
            break
    
    # Procurar dados de mercado
    for i, line in enumerate(lines):
        if "DADOS DE MERCADO" in line:
            essential_data.extend(lines[i:i+30])  # Próximas 30 linhas
            break
    
    essential_content = '\n'.join(essential_data)
    
    print(f"Empresa: {empresa}")
    print(f"Conteúdo original: {len(content)} chars")
    print(f"Conteúdo essencial: {len(essential_content)} chars")
    
    # Inicializar agente
    try:
        agent = ChimpaAnalysisAgent()
        print("Agente inicializado")
    except Exception as e:
        print(f"[ERRO] Agente falhou: {e}")
        return
    
    # Fazer análise direta com dados reduzidos
    print("\nANÁLISE RÁPIDA COM DADOS ESSENCIAIS")
    print("-" * 40)
    
    try:
        prompt = f"""Analise rapidamente os dados financeiros essenciais da empresa {empresa}:

DADOS ESSENCIAIS:
{essential_content}

FORNEÇA:
1. SITUAÇÃO FINANCEIRA atual (2-3 frases)
2. PRINCIPAIS TENDÊNCIAS identificadas (2-3 frases)  
3. PRINCIPAL RISCO (1 frase)
4. PRINCIPAL OPORTUNIDADE (1 frase)
5. CONCLUSÃO para investimento (1-2 frases)

Total máximo: 200 palavras."""

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": "Você é um analista financeiro sênior especializado em análise fundamentalista brasileira. Seja objetivo e direto."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        analysis = response.choices[0].message.content
        
        print("ANÁLISE CONCLUÍDA!")
        print("=" * 40)
        print(analysis)
        
        # Salvar resultado
        output_file = f"analysis_quick_{empresa.replace(' ', '_')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"ANÁLISE RÁPIDA - {empresa}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Data: {asyncio.get_running_loop().time()}\n")
            f.write(f"Arquivo origem: {valuation_file.name}\n\n")
            f.write(analysis)
            f.write(f"\n\n--- Análise gerada automaticamente pelo Chimpa Analysis Agent ---")
        
        print(f"\nAnálise salva: {output_file}")
        
        # Teste de formato para áudio
        print(f"\nFORMATO PARA ÁUDIO (2 MINUTOS):")
        print("-" * 40)
        
        audio_lines = analysis.split('\n')
        audio_content = []
        
        for line in audio_lines:
            if line.strip():
                # Remover numeração e formatação
                clean_line = line.replace('1.', '').replace('2.', '').replace('3.', '')
                clean_line = clean_line.replace('4.', '').replace('5.', '').strip()
                if clean_line:
                    audio_content.append(clean_line)
        
        audio_text = ' '.join(audio_content)
        
        # Limitar para aproximadamente 300 palavras (2 minutos de áudio)
        words = audio_text.split()
        if len(words) > 300:
            audio_text = ' '.join(words[:300]) + "..."
        
        print(f"Palavras: {len(audio_text.split())}")
        print(f"Duração estimada: ~{len(audio_text.split()) * 0.4:.0f} segundos")
        print()
        print(audio_text)
        
        # Salvar versão para áudio
        audio_file = f"audio_script_{empresa.replace(' ', '_')}.txt"
        with open(audio_file, 'w', encoding='utf-8') as f:
            f.write(f"SCRIPT PARA ÁUDIO - {empresa}\n")
            f.write("=" * 30 + "\n")
            f.write(f"Duração: ~{len(audio_text.split()) * 0.4:.0f} segundos\n")
            f.write(f"Palavras: {len(audio_text.split())}\n\n")
            f.write(audio_text)
        
        print(f"\nScript para áudio salvo: {audio_file}")
        
    except Exception as e:
        print(f"[ERRO] Análise falhou: {e}")
    
    print(f"\nTESTE OTIMIZADO CONCLUÍDO!")

if __name__ == "__main__":
    asyncio.run(test_optimized())