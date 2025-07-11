#!/usr/bin/env python3
"""
Script para executar análise de Lévy em lote para múltiplos ativos.

Uso:
    python run_levy_batch.py --config batch_config.json
    python run_levy_batch.py --tickers PETR4.SA VALE3.SA ITUB4.SA --start 2020-01-01

Author: CrunchDAO SB Team
Date: 2025-06-26
"""

import argparse
import json
import sys
import os
from datetime import datetime
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Importar o módulo principal
from run_levy_analysis import load_data, analyze_levy_sections, setup_directories


def process_single_ticker(ticker, start_date, end_date, tau, q):
    """
    Processa um único ativo.
    
    Args:
        ticker: Símbolo do ativo
        start_date: Data inicial
        end_date: Data final
        tau: Parâmetro tau
        q: Parâmetro q
        
    Returns:
        Tupla (ticker, resultados, erro)
    """
    try:
        print(f"\n🔄 Processando {ticker}...")
        
        # Carregar dados
        data = load_data(ticker, start_date, end_date)
        
        # Analisar
        results = analyze_levy_sections(data, ticker, tau=tau, q=q, save_results=True)
        
        # Preparar resumo
        summary = {
            'ticker': ticker,
            'n_observations': len(data),
            'n_sections': len(results['levy_result'].S_tau),
            'n_breaks': len(results['breaks_with_dates']),
            'mean_duration': results['levy_result'].durations.mean(),
            'cv_duration': results['levy_result'].durations.std() / results['levy_result'].durations.mean(),
            'norm_kurtosis': results['features']['levy_norm_kurtosis'],
            'shapiro_pvalue': results['features']['levy_shapiro_pvalue'],
            'breaks': results['breaks_with_dates']
        }
        
        return ticker, summary, None
        
    except Exception as e:
        print(f"❌ Erro ao processar {ticker}: {str(e)}")
        return ticker, None, str(e)


def create_consolidated_report(all_results, output_file):
    """
    Cria relatório consolidado de todos os ativos.
    
    Args:
        all_results: Lista de resultados
        output_file: Arquivo de saída
    """
    print(f"\n📊 Criando relatório consolidado...")
    
    # Criar DataFrame resumido
    summary_data = []
    breaks_data = []
    
    for ticker, result, error in all_results:
        if error:
            summary_data.append({
                'ticker': ticker,
                'status': 'ERRO',
                'error': error
            })
        else:
            # Resumo do ativo
            summary_data.append({
                'ticker': ticker,
                'status': 'OK',
                'n_observations': result['n_observations'],
                'n_sections': result['n_sections'],
                'n_breaks': result['n_breaks'],
                'mean_duration': round(result['mean_duration'], 2),
                'cv_duration': round(result['cv_duration'], 3),
                'norm_kurtosis': round(result['norm_kurtosis'], 4),
                'shapiro_pvalue': round(result['shapiro_pvalue'], 4)
            })
            
            # Quebras detectadas
            for brk in result['breaks']:
                breaks_data.append({
                    'ticker': ticker,
                    'date': brk['date'].strftime('%Y-%m-%d'),
                    'duration_before': round(brk['mean_before'], 1),
                    'duration_after': round(brk['mean_after'], 1),
                    'change_ratio': round(brk['change_ratio'], 3),
                    'p_value': round(brk['p_value'], 4)
                })
    
    # Salvar resumos
    summary_df = pd.DataFrame(summary_data)
    breaks_df = pd.DataFrame(breaks_data)
    
    # Criar Excel com múltiplas abas
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
        if not breaks_df.empty:
            breaks_df.to_excel(writer, sheet_name='Quebras', index=False)
            
            # Análise de quebras por período
            breaks_df['year_month'] = pd.to_datetime(breaks_df['date']).dt.to_period('M')
            period_analysis = breaks_df.groupby('year_month').agg({
                'ticker': 'count',
                'change_ratio': 'mean'
            }).rename(columns={'ticker': 'n_breaks', 'change_ratio': 'avg_change_ratio'})
            period_analysis.to_excel(writer, sheet_name='Quebras_por_Período')
    
    print(f"✅ Relatório consolidado salvo em: {output_file}")
    
    # Estatísticas gerais
    success_count = len([r for _, _, e in all_results if e is None])
    error_count = len(all_results) - success_count
    total_breaks = sum([r['n_breaks'] for _, r, e in all_results if e is None])
    
    print(f"\n📈 RESUMO GERAL:")
    print(f"   Ativos processados: {len(all_results)}")
    print(f"   Sucessos: {success_count}")
    print(f"   Erros: {error_count}")
    print(f"   Total de quebras detectadas: {total_breaks}")
    
    if not breaks_df.empty:
        print(f"\n🎯 Períodos com mais quebras:")
        top_periods = period_analysis.nlargest(5, 'n_breaks')
        for idx, row in top_periods.iterrows():
            print(f"   {idx}: {row['n_breaks']} quebras (razão média: {row['avg_change_ratio']:.3f})")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Análise em lote de quebras estruturais com seções de Lévy'
    )
    
    parser.add_argument('--config', type=str,
                        help='Arquivo JSON com configuração')
    parser.add_argument('--tickers', nargs='+',
                        help='Lista de tickers para analisar')
    parser.add_argument('--start', type=str, default='2019-01-01',
                        help='Data inicial (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2024-12-31',
                        help='Data final (YYYY-MM-DD)')
    parser.add_argument('--tau', type=float, default=0.005,
                        help='Parâmetro tau (default: 0.005)')
    parser.add_argument('--q', type=int, default=5,
                        help='Janela para volatilidade local (default: 5)')
    parser.add_argument('--workers', type=int, default=4,
                        help='Número de processos paralelos (default: 4)')
    
    args = parser.parse_args()
    
    # Setup
    setup_directories()
    
    print("\n" + "="*60)
    print("ANÁLISE EM LOTE - SEÇÕES DE LÉVY")
    print("="*60)
    
    # Determinar lista de tickers
    if args.config:
        print(f"📄 Carregando configuração de: {args.config}")
        with open(args.config, 'r') as f:
            config = json.load(f)
            tickers = config.get('tickers', [])
            start_date = config.get('start_date', args.start)
            end_date = config.get('end_date', args.end)
            tau = config.get('tau', args.tau)
            q = config.get('q', args.q)
    elif args.tickers:
        tickers = args.tickers
        start_date = args.start
        end_date = args.end
        tau = args.tau
        q = args.q
    else:
        # Lista padrão de ativos brasileiros
        tickers = [
            '^BVSP',      # Índice Bovespa
            'PETR4.SA',   # Petrobras
            'VALE3.SA',   # Vale
            'ITUB4.SA',   # Itaú
            'BBDC4.SA',   # Bradesco
            'ABEV3.SA',   # Ambev
            'B3SA3.SA',   # B3
            'WEGE3.SA',   # WEG
            'MGLU3.SA',   # Magazine Luiza
            'PRIO3.SA'    # PetroRio
        ]
        start_date = args.start
        end_date = args.end
        tau = args.tau
        q = args.q
    
    print(f"\n📊 Ativos para análise: {len(tickers)}")
    print(f"📅 Período: {start_date} a {end_date}")
    print(f"⚙️  Parâmetros: tau={tau}, q={q}")
    print(f"🔧 Processos paralelos: {args.workers}")
    
    # Processar em paralelo
    all_results = []
    
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        # Submeter tarefas
        futures = {
            executor.submit(process_single_ticker, ticker, start_date, end_date, tau, q): ticker
            for ticker in tickers
        }
        
        # Coletar resultados
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                result = future.result()
                all_results.append(result)
                if result[2] is None:  # Sem erro
                    print(f"✅ {ticker} concluído")
                else:
                    print(f"❌ {ticker} falhou")
            except Exception as e:
                print(f"❌ Erro ao processar {ticker}: {e}")
                all_results.append((ticker, None, str(e)))
    
    # Criar relatório consolidado
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"outputs/levy_batch_report_{timestamp}.xlsx"
    create_consolidated_report(all_results, output_file)
    
    print("\n" + "="*60)
    print("✨ ANÁLISE EM LOTE CONCLUÍDA!")
    print("="*60)


if __name__ == "__main__":
    main()