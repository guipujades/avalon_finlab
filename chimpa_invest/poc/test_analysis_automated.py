#!/usr/bin/env python3
"""
Teste automatizado do Analysis Agent
===================================
"""

import asyncio
import os
from pathlib import Path
from analysis_agent import ChimpaAnalysisAgent

async def test_automated():
    """Teste automatizado completo"""
    
    print("TESTE AUTOMATIZADO DO ANALYSIS AGENT")
    print("=" * 50)
    
    # Verificar arquivos
    data_dir = Path("data")
    valuation_files = list(data_dir.glob("*_COMPLETO.txt"))
    
    if not valuation_files:
        print("[ERRO] Nenhum arquivo de valuation encontrado")
        return
    
    valuation_file = valuation_files[0]
    print(f"Arquivo selecionado: {valuation_file.name}")
    
    # Verificar release correspondente
    release_file = None
    documents_dir = Path("documents/parsed")
    if documents_dir.exists():
        release_files = list(documents_dir.glob("*.txt"))
        for rf in release_files:
            if "BANCO_DO_BRASIL" in rf.name:
                release_file = rf
                break
    
    print(f"Release: {release_file.name if release_file else 'Não encontrado'}")
    
    # Inicializar agente
    try:
        agent = ChimpaAnalysisAgent()
        print("Agente inicializado com sucesso")
    except Exception as e:
        print(f"[ERRO] Agente não inicializado: {e}")
        return
    
    # Teste 1: Análise rápida
    print("\n[TESTE 1] Análise Rápida")
    print("-" * 30)
    
    try:
        quick_result = await agent.analyze_complete_valuation(
            str(valuation_file),
            str(release_file) if release_file else None,
            "quick"
        )
        
        if quick_result.get("status") == "success":
            print("Análise rápida bem-sucedida!")
            print(f"Tempo: {quick_result['metadata']['processing_time']:.2f}s")
            print(f"Modelo: {quick_result['metadata']['model_used']}")
            
            # Gerar e salvar resumo para áudio
            audio_summary = agent.generate_audio_summary(quick_result)
            audio_file = "test_audio_quick.txt"
            
            with open(audio_file, 'w', encoding='utf-8') as f:
                f.write(audio_summary)
            
            print(f"Resumo para áudio salvo: {audio_file}")
            
            # Mostrar preview
            lines = audio_summary.split('\n')[:5]
            print(f"\nPREVIEW (primeiras 5 linhas):")
            for line in lines:
                if line.strip():
                    print(f"   {line}")
            
        else:
            print(f"[ERRO] Análise rápida falhou: {quick_result.get('error')}")
    
    except Exception as e:
        print(f"[ERRO] Exceção na análise rápida: {e}")
    
    # Teste 2: Análise detalhada (opcional - mais lenta)
    print(f"\n[TESTE 2] Análise Detalhada")
    print("-" * 30)
    print("Iniciando análise detalhada (pode demorar 30-60s)...")
    
    try:
        detailed_result = await agent.analyze_complete_valuation(
            str(valuation_file),
            str(release_file) if release_file else None,
            "detailed"
        )
        
        if detailed_result.get("status") == "success":
            print("Análise detalhada bem-sucedida!")
            print(f"[TEMPO] Tempo: {detailed_result['metadata']['processing_time']:.2f}s")
            print(f"[MODELO] Modelo: {detailed_result['metadata']['model_used']}")
            
            # Salvar relatório completo
            report_path = agent.save_analysis_report(detailed_result, "test_detailed_report.json")
            print(f"[RELATORIO] Relatório completo salvo: {report_path}")
            
            # Estatísticas da análise
            valuation_analysis = detailed_result.get("valuation_analysis", {})
            release_analysis = detailed_result.get("release_analysis")
            integrated_analysis = detailed_result.get("integrated_analysis", {})
            
            print(f"\n[COMPONENTES] COMPONENTES DA ANÁLISE:")
            print(f"   - Valuation: [OK] ({len(valuation_analysis.get('analysis', ''))} chars)")
            print(f"   - Release: {'[OK]' if release_analysis else '[AUSENTE]'}")
            print(f"   - Integrada: [OK] ({len(integrated_analysis.get('integrated_analysis', ''))} chars)")
            
        else:
            print(f"[ERRO] Erro na análise detalhada: {detailed_result.get('error')}")
    
    except Exception as e:
        print(f"[ERRO] Exceção na análise detalhada: {e}")
    
    print(f"\n[CONCLUIDO] TESTE AUTOMATIZADO CONCLUÍDO!")
    print("=" * 50)
    
    # Resumo final
    print(f"\n[RESUMO] RESUMO DO TESTE:")
    print(f"   [ARQUIVO] Arquivo analisado: {valuation_file.name}")
    print(f"   [RELEASE] Release incluído: {'Sim' if release_file else 'Não'}")
    print(f"   [AGENTE] Agente: ChimpaAnalysisAgent")
    print(f"   [RAPIDA] Análise rápida: Para áudio de 2 minutos")
    print(f"   [DETALHADA] Análise detalhada: Para relatório completo")
    
    print(f"\n[PROXIMOS PASSOS] PRÓXIMOS PASSOS:")
    print(f"   1. Use test_audio_quick.txt para áudio")
    print(f"   2. Use test_detailed_report.json para relatório")
    print(f"   3. Integre com sistema de TTS para áudio")
    print(f"   4. Customize prompts conforme necessário")

if __name__ == "__main__":
    asyncio.run(test_automated())