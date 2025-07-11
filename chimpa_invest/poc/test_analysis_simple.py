#!/usr/bin/env python3
"""
Teste simples do Analysis Agent
==============================
"""

import asyncio
import os
from pathlib import Path
from analysis_agent import ChimpaAnalysisAgent

async def test_simple():
    """Teste básico de funcionamento"""
    
    print("TESTE SIMPLES DO ANALYSIS AGENT")
    print("=" * 40)
    
    # Verificar arquivos
    data_dir = Path("data")
    valuation_files = list(data_dir.glob("*_COMPLETO.txt"))
    
    if not valuation_files:
        print("[ERRO] Nenhum arquivo de valuation encontrado")
        return
    
    valuation_file = valuation_files[0]
    print(f"Usando arquivo: {valuation_file}")
    
    # Testar inicialização do agente
    try:
        agent = ChimpaAnalysisAgent()
        print("Agente inicializado com sucesso")
    except Exception as e:
        print(f"[ERRO] Agente não inicializado: {e}")
        return
    
    # Testar carregamento de arquivo
    try:
        valuation_data = agent._load_valuation_txt(str(valuation_file))
        if valuation_data:
            print(f"Arquivo carregado: {valuation_data['empresa']}")
            print(f"Período: {valuation_data['periodo']}")
            print(f"Tamanho: {valuation_data['file_size']} caracteres")
            print(f"Seções encontradas: {len(valuation_data['sections'])}")
        else:
            print("[ERRO] Arquivo não carregado")
            return
    except Exception as e:
        print(f"[ERRO] Carregamento falhou: {e}")
        return
    
    # Teste de análise rápida (apenas se o usuário confirmar)
    resposta = input("\nFazer teste de análise via ChatGPT? (s/N): ").strip().lower()
    
    if resposta == 's':
        print("\nTestando análise rápida...")
        try:
            result = await agent.analyze_complete_valuation(
                str(valuation_file),
                None,  # Sem release
                "quick"
            )
            
            if result.get("status") == "success":
                print("Análise concluída!")
                print(f"Tempo: {result['metadata']['processing_time']:.2f}s")
                print(f"Modelo: {result['metadata']['model_used']}")
                
                # Mostrar preview
                valuation_analysis = result.get("valuation_analysis", {})
                analysis_text = valuation_analysis.get("analysis", "")
                
                if analysis_text:
                    preview = analysis_text[:300] + "..." if len(analysis_text) > 300 else analysis_text
                    print(f"\nPREVIEW DA ANÁLISE:")
                    print("-" * 30)
                    print(preview)
                
                # Gerar resumo para áudio
                audio_summary = agent.generate_audio_summary(result)
                
                # Salvar resumo
                audio_file = f"test_audio_summary_{valuation_file.stem}.txt"
                with open(audio_file, 'w', encoding='utf-8') as f:
                    f.write(audio_summary)
                
                print(f"\nResumo para áudio salvo: {audio_file}")
                
            else:
                print(f"[ERRO] Análise falhou: {result.get('error')}")
                
        except Exception as e:
            print(f"[ERRO] Exceção durante análise: {e}")
    
    else:
        print("Teste de API pulado pelo usuário")
    
    print("\nTESTE CONCLUÍDO!")

if __name__ == "__main__":
    asyncio.run(test_simple())