#!/usr/bin/env python3
"""
Demonstração do Analysis Agent
=============================
Este script demonstra como usar o Analysis Agent para analisar
dados de valuation combinados com releases financeiros.
"""

import asyncio
import json
from pathlib import Path
from analysis_agent import ChimpaAnalysisAgent, analyze_company_valuation


async def demo_analysis_agent():
    """Demonstração completa do Analysis Agent"""
    
    print("DEMONSTRAÇÃO: Chimpa Analysis Agent")
    print("=" * 60)
    
    # Verificar arquivos disponíveis
    poc_dir = Path(__file__).parent
    data_dir = poc_dir / "data"
    documents_dir = poc_dir / "documents" / "parsed"
    
    print("\nVERIFICANDO ARQUIVOS DISPONÍVEIS:")
    print("-" * 40)
    
    # Buscar arquivos de valuation
    valuation_files = list(data_dir.glob("*_COMPLETO.txt"))
    if valuation_files:
        print(f"Encontrados {len(valuation_files)} arquivo(s) de valuation:")
        for file in valuation_files:
            print(f"   Arquivo: {file.name}")
    else:
        print("[ERRO] Nenhum arquivo de valuation encontrado em data/")
        return
    
    # Buscar releases parsed
    release_files = list(documents_dir.glob("*.txt"))
    if release_files:
        print(f"Encontrados {len(release_files)} release(s) parsed:")
        for file in release_files:
            print(f"   Arquivo: {file.name}")
    else:
        print("[AVISO] Nenhum release parsed encontrado")
    
    # Usar o primeiro arquivo de valuation disponível
    valuation_path = valuation_files[0]
    
    # Tentar encontrar release correspondente
    release_path = None
    if "BBAS3" in valuation_path.name and release_files:
        for release_file in release_files:
            if "BANCO_DO_BRASIL" in release_file.name:
                release_path = release_file
                break
    
    print(f"\nANÁLISE SELECIONADA:")
    print(f"   Valuation: {valuation_path.name}")
    print(f"   Release: {release_path.name if release_path else 'Não disponível'}")
    
    # Verificar API key
    try:
        agent = ChimpaAnalysisAgent()
        print(f"Agent inicializado com sucesso")
    except ValueError as e:
        print(f"[ERRO] Configuração inválida: {e}")
        print("\nSOLUÇÃO:")
        print("   1. Configure OPENAI_API_KEY no arquivo .env")
        print("   2. Ou passe a chave como parâmetro:")
        print("      agent = ChimpaAnalysisAgent('sua-api-key-aqui')")
        return
    
    print("\nEXECUTANDO ANÁLISES...")
    print("=" * 50)
    
    # 1. Análise Rápida (para áudio)
    print("\n1. ANÁLISE RÁPIDA (para áudio 2min)")
    print("-" * 40)
    
    try:
        quick_result = await agent.analyze_complete_valuation(
            str(valuation_path),
            str(release_path) if release_path else None,
            "quick"
        )
        
        if quick_result.get("status") == "success":
            print("Análise rápida concluída!")
            
            # Gerar resumo para áudio
            audio_summary = agent.generate_audio_summary(quick_result)
            
            # Salvar resumo para áudio
            audio_file = poc_dir / f"audio_summary_{valuation_path.stem}.txt"
            with open(audio_file, 'w', encoding='utf-8') as f:
                f.write(audio_summary)
            
            print(f"Resumo para áudio salvo: {audio_file.name}")
            print(f"[MODELO] Modelo usado: {quick_result['metadata']['model_used']}")
            print(f"[TEMPO] Tempo de processamento: {quick_result['metadata']['processing_time']:.2f}s")
            
            # Mostrar preview do resumo
            preview = audio_summary[:300] + "..." if len(audio_summary) > 300 else audio_summary
            print(f"\n[PREVIEW] PREVIEW DO RESUMO:")
            print(preview)
            
        else:
            print(f"[ERRO] Erro na análise rápida: {quick_result.get('error')}")
    
    except Exception as e:
        print(f"[ERRO] Exceção na análise rápida: {e}")
    
    # 2. Análise Detalhada
    print("\n\n[2] ANÁLISE DETALHADA (relatório completo)")
    print("-" * 40)
    
    try:
        detailed_result = await agent.analyze_complete_valuation(
            str(valuation_path),
            str(release_path) if release_path else None,
            "detailed"
        )
        
        if detailed_result.get("status") == "success":
            print("[OK] Análise detalhada concluída!")
            
            # Salvar relatório completo
            report_path = agent.save_analysis_report(detailed_result)
            
            print(f"[MODELO] Modelo usado: {detailed_result['metadata']['model_used']}")
            print(f"[TEMPO] Tempo de processamento: {detailed_result['metadata']['processing_time']:.2f}s")
            print(f"[RELATORIO] Relatório completo salvo: {report_path}")
            
            # Mostrar estrutura da análise
            print(f"\n[ESTRUTURA] ESTRUTURA DA ANÁLISE:")
            print(f"   - Análise de Valuation: [OK]")
            print(f"   - Análise de Release: {'[OK]' if detailed_result['release_analysis'] else '[AUSENTE]'}")
            print(f"   - Análise Integrada: [OK]")
            
            # Preview da análise integrada
            integrated = detailed_result.get("integrated_analysis", {})
            integrated_text = integrated.get("integrated_analysis", "")
            if integrated_text:
                preview = integrated_text[:400] + "..." if len(integrated_text) > 400 else integrated_text
                print(f"\n[PREVIEW] PREVIEW DA ANÁLISE INTEGRADA:")
                print(preview)
        
        else:
            print(f"[ERRO] Erro na análise detalhada: {detailed_result.get('error')}")
    
    except Exception as e:
        print(f"[ERRO] Exceção na análise detalhada: {e}")
    
    print("\n[CONCLUIDO] DEMONSTRAÇÃO CONCLUÍDA!")
    print("=" * 50)
    print("\n[INSTRUCOES] COMO USAR O ANALYSIS AGENT:")
    print("1. Importe: from analysis_agent import ChimpaAnalysisAgent")
    print("2. Inicialize: agent = ChimpaAnalysisAgent()")
    print("3. Analise: result = await agent.analyze_complete_valuation(valuation_path, release_path)")
    print("4. Gere áudio: audio = agent.generate_audio_summary(result)")
    print("5. Salve relatório: agent.save_analysis_report(result)")


async def demo_com_inputs_customizados():
    """Demonstração com inputs personalizados"""
    
    print("\n[INTERATIVO] MODO INTERATIVO")
    print("=" * 30)
    
    # Permitir ao usuário escolher arquivos
    poc_dir = Path(__file__).parent
    data_dir = poc_dir / "data"
    
    valuation_files = list(data_dir.glob("*_COMPLETO.txt"))
    
    if not valuation_files:
        print("[ERRO] Nenhum arquivo de valuation encontrado!")
        return
    
    print("[ARQUIVOS] ARQUIVOS DE VALUATION DISPONÍVEIS:")
    for i, file in enumerate(valuation_files, 1):
        print(f"   {i}. {file.name}")
    
    try:
        choice = input(f"\nEscolha um arquivo (1-{len(valuation_files)}): ").strip()
        file_index = int(choice) - 1
        
        if 0 <= file_index < len(valuation_files):
            selected_file = valuation_files[file_index]
            
            analysis_type = input("Tipo de análise (quick/detailed) [quick]: ").strip().lower()
            if analysis_type not in ["quick", "detailed"]:
                analysis_type = "quick"
            
            print(f"\n[EXECUTANDO] Executando análise {analysis_type} para {selected_file.name}...")
            
            result = await analyze_company_valuation(
                str(selected_file),
                None,  # Sem release para simplicidade
                analysis_type
            )
            
            if result.get("status") == "success":
                print("[OK] Análise concluída!")
                
                if analysis_type == "quick":
                    agent = ChimpaAnalysisAgent()
                    audio_summary = agent.generate_audio_summary(result)
                    print(f"\n[AUDIO] RESUMO PARA ÁUDIO:")
                    print("=" * 40)
                    print(audio_summary)
                else:
                    agent = ChimpaAnalysisAgent()
                    report_path = agent.save_analysis_report(result)
                    print(f"[RELATORIO] Relatório salvo: {report_path}")
            
            else:
                print(f"[ERRO] Erro: {result.get('error')}")
        
        else:
            print("[ERRO] Escolha inválida!")
    
    except (ValueError, KeyboardInterrupt):
        print("\n[INFO] Operação cancelada pelo usuário")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(demo_com_inputs_customizados())
    else:
        asyncio.run(demo_analysis_agent())