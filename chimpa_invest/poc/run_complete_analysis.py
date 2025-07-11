#!/usr/bin/env python3
"""
Sistema Completo de Análise Financeira - Chimpa Invest
======================================================
Integra valuation temporal, dados de mercado via Perplexity e análise via ChatGPT.

Funcionalidades:
1. Executa valuation temporal completo
2. Busca dados de mercado (interativo via Perplexity)
3. Analisa tudo via ChatGPT
4. Gera relatório detalhado + áudio de 2 minutos

Uso:
    python run_complete_analysis.py BBAS3
    python run_complete_analysis.py PETR4
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Imports dos nossos agentes
from analysis_agent import ChimpaAnalysisAgent

def print_header():
    """Imprime header do sistema"""
    print("CHIMPA INVEST - ANÁLISE FINANCEIRA COMPLETA")
    print("=" * 60)
    print("Sistema integrado: Valuation + Mercado + Análise IA")
    print("=" * 60)

def print_step(step_num, title, description=""):
    """Imprime step do processo"""
    print(f"\n[PASSO {step_num}] {title}")
    print("-" * 40)
    if description:
        print(f"   {description}")

async def run_complete_analysis(ticker: str):
    """
    Executa análise financeira completa para um ticker
    
    Args:
        ticker: Código da ação (ex: BBAS3, PETR4)
    """
    
    start_time = datetime.now()
    print_header()
    print(f"TICKER SELECIONADO: {ticker}")
    print(f"Início: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Verificar se existem dados de valuation para o ticker
    data_dir = Path("data")
    valuation_files = list(data_dir.glob(f"*{ticker}*_COMPLETO.txt"))
    
    if not valuation_files:
        print(f"\n[ERRO] Nenhum arquivo de valuation encontrado para {ticker}")
        print(f"Execute primeiro: python valuation_empresa_temporal.py {ticker}")
        return
    
    # Usar o arquivo mais recente
    valuation_file = sorted(valuation_files)[-1]
    print(f"Arquivo de valuation: {valuation_file.name}")
    
    # Verificar se existe release correspondente
    documents_dir = Path("documents/parsed")
    release_file = None
    
    if documents_dir.exists():
        # Mapear tickers para nomes de empresa
        ticker_map = {
            "BBAS3": "BANCO_DO_BRASIL",
            "PETR3": "PETROBRAS",
            "PETR4": "PETROBRAS", 
            "VALE3": "VALE",
            "ITUB3": "ITAU",
            "ITUB4": "ITAU"
        }
        
        empresa_nome = ticker_map.get(ticker.upper())
        if empresa_nome:
            release_files = list(documents_dir.glob(f"*{empresa_nome}*.txt"))
            if release_files:
                release_file = sorted(release_files)[-1]  # Mais recente
    
    print(f"Release encontrado: {'Sim' if release_file else 'Não'}")
    if release_file:
        print(f"   Arquivo: {release_file.name}")
    
    # PASSO 1: Verificar se dados de mercado existem
    print_step(1, "VERIFICAÇÃO DE DADOS DE MERCADO")
    
    # Buscar JSON de valuation correspondente
    json_files = list(data_dir.glob(f"*{ticker}*[0-9].json"))
    has_market_data = False
    
    if json_files:
        json_file = sorted(json_files)[-1]
        with open(json_file, 'r', encoding='utf-8') as f:
            valuation_data = json.load(f)
            
        market_data = valuation_data.get("dados_mercado", {})
        if market_data:
            approved_data = [k for k, v in market_data.items() if v.get("aprovado")]
            has_market_data = len(approved_data) > 0
            print(f"Dados de mercado encontrados: {len(approved_data)} categorias aprovadas")
        else:
            print("[AVISO] Nenhum dado de mercado encontrado")
    else:
        print("[AVISO] Arquivo JSON de valuation não encontrado")
    
    # PASSO 2: Executar nova análise se necessário
    if not has_market_data:
        print_step(2, "COLETA DE DADOS DE MERCADO", 
                   "Executando valuation com busca de dados atualizados...")
        
        # Executar valuation temporal com dados de mercado
        import subprocess
        
        print("Executando: python valuation_empresa_temporal.py " + ticker)
        print("[AVISO] Isso abrirá o sistema interativo do Perplexity...")
        
        try:
            result = subprocess.run([
                "python3", "valuation_empresa_temporal.py", ticker
            ], cwd=Path.cwd(), timeout=300, capture_output=False)
            
            if result.returncode == 0:
                print("Valuation com dados de mercado concluído!")
                
                # Recarregar arquivos atualizados
                valuation_files = list(data_dir.glob(f"*{ticker}*_COMPLETO.txt"))
                if valuation_files:
                    valuation_file = sorted(valuation_files)[-1]
                    print(f"Novo arquivo: {valuation_file.name}")
                
            else:
                print("[AVISO] Valuation retornou código de erro, continuando com dados existentes...")
                
        except subprocess.TimeoutExpired:
            print("[AVISO] Timeout na execução do valuation, continuando com dados existentes...")
        except Exception as e:
            print(f"[AVISO] Erro na execução: {e}, continuando com dados existentes...")
    
    else:
        print("Dados de mercado já disponíveis, prosseguindo para análise...")
    
    # PASSO 3: Análise via ChatGPT
    print_step(3, "ANÁLISE VIA CHATGPT", 
               "Gerando análise detalhada e resumo para áudio...")
    
    try:
        agent = ChimpaAnalysisAgent()
        print("Analysis Agent inicializado")
        
        # Análise rápida para áudio
        print("\nGerando análise rápida (áudio 2min)...")
        quick_result = await agent.analyze_complete_valuation(
            str(valuation_file),
            str(release_file) if release_file else None,
            "quick"
        )
        
        if quick_result.get("status") == "success":
            print(f"Análise rápida concluída ({quick_result['metadata']['processing_time']:.1f}s)")
            
            # Gerar e salvar áudio
            audio_summary = agent.generate_audio_summary(quick_result)
            audio_file = f"audio_analysis_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(audio_file, 'w', encoding='utf-8') as f:
                f.write(audio_summary)
            
            print(f"Script para áudio salvo: {audio_file}")
            
            # Mostrar preview
            preview_lines = audio_summary.split('\n')[:3]
            print(f"\nPREVIEW DO ÁUDIO:")
            for line in preview_lines:
                if line.strip():
                    print(f"   {line}")
            
        else:
            print(f"[ERRO] Análise rápida falhou: {quick_result.get('error')}")
        
        # Análise detalhada
        print(f"\nGerando análise detalhada...")
        detailed_result = await agent.analyze_complete_valuation(
            str(valuation_file),
            str(release_file) if release_file else None,
            "detailed"
        )
        
        if detailed_result.get("status") == "success":
            print(f"Análise detalhada concluída ({detailed_result['metadata']['processing_time']:.1f}s)")
            
            # Salvar relatório
            report_file = f"analysis_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            agent.save_analysis_report(detailed_result, report_file)
            
            print(f"Relatório completo salvo: {report_file}")
            
        else:
            print(f"[ERRO] Análise detalhada falhou: {detailed_result.get('error')}")
    
    except Exception as e:
        print(f"[ERRO] Analysis Agent falhou: {e}")
        print("Verifique se OPENAI_API_KEY está configurada no .env")
    
    # RESUMO FINAL
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    print_step("FINAL", "RESUMO DA ANÁLISE")
    print(f"Ticker analisado: {ticker}")
    print(f"Valuation: {valuation_file.name}")
    print(f"Release: {release_file.name if release_file else 'Não disponível'}")
    print(f"Dados de mercado: {'Sim' if has_market_data else 'Não'}")
    print(f"Tempo total: {total_time:.1f} segundos")
    print(f"Finalizado: {end_time.strftime('%d/%m/%Y %H:%M:%S')}")
    
    print(f"\nANÁLISE COMPLETA FINALIZADA!")
    print("=" * 50)
    
    # Instruções finais
    print(f"\nPRÓXIMOS PASSOS:")
    print(f"   1. Use o script de áudio para gravação")
    print(f"   2. Consulte o relatório JSON para análise detalhada")
    print(f"   3. Execute novamente para dados atualizados")
    print(f"   4. Compare com outras empresas do setor")

def main():
    """Função principal"""
    
    if len(sys.argv) != 2:
        print("[ERRO] Forneça um ticker como argumento")
        print("\nEXEMPLOS DE USO:")
        print("   python run_complete_analysis.py BBAS3")
        print("   python run_complete_analysis.py PETR4")
        print("   python run_complete_analysis.py VALE3")
        return
    
    ticker = sys.argv[1].upper()
    
    # Verificar se é um ticker válido
    valid_tickers = ["BBAS3", "PETR3", "PETR4", "VALE3", "ITUB3", "ITUB4"]
    if ticker not in valid_tickers:
        print(f"[AVISO] Ticker {ticker} não está na lista pré-configurada")
        print(f"Tickers testados: {', '.join(valid_tickers)}")
        print("Continuando mesmo assim...")
    
    # Executar análise
    asyncio.run(run_complete_analysis(ticker))

if __name__ == "__main__":
    main()