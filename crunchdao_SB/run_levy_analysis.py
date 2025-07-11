#!/usr/bin/env python3
"""
Script principal para executar análise de quebras estruturais com seções de Lévy.

Uso:
    python run_levy_analysis.py --ticker PETR4.SA --start 2020-01-01 --end 2024-12-31
    python run_levy_analysis.py --help

Author: CrunchDAO SB Team
Date: 2025-06-26
"""

import argparse
import sys
import os
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Adicionar diretório src ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.levy_sections import LevySectionsAnalyzer, analyze_structural_breaks_for_series


def setup_directories():
    """Cria diretórios necessários se não existirem"""
    dirs = ['outputs', 'outputs/figures', 'outputs/data']
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def load_data(ticker, start_date, end_date):
    """
    Carrega dados do Yahoo Finance.
    
    Args:
        ticker: Símbolo do ativo
        start_date: Data inicial (YYYY-MM-DD)
        end_date: Data final (YYYY-MM-DD)
        
    Returns:
        DataFrame com preços e retornos
    """
    print(f"\n📊 Carregando dados para {ticker}...")
    print(f"   Período: {start_date} a {end_date}")
    
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            raise ValueError(f"Nenhum dado encontrado para {ticker}")
            
        # Calcular retornos logarítmicos
        data['Returns'] = np.log(data['Close'] / data['Close'].shift(1))
        data = data.dropna()
        
        print(f"✅ {len(data)} observações carregadas")
        return data
        
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        sys.exit(1)


def analyze_levy_sections(data, ticker, tau=0.005, q=5, save_results=True):
    """
    Executa análise completa com seções de Lévy.
    
    Args:
        data: DataFrame com dados do ativo
        ticker: Nome do ativo
        tau: Parâmetro tau para seções de Lévy
        q: Janela para volatilidade local
        save_results: Se True, salva resultados em arquivos
        
    Returns:
        Dicionário com resultados da análise
    """
    print(f"\n🔍 Analisando seções de Lévy (tau={tau}, q={q})...")
    
    returns = data['Returns'].values
    dates = data.index
    
    # Criar analisador
    analyzer = LevySectionsAnalyzer(tau=tau, q=q)
    
    # Calcular seções de Lévy
    levy_result = analyzer.compute_levy_sections(returns)
    print(f"   ✓ {len(levy_result.S_tau)} seções calculadas")
    print(f"   ✓ Duração média: {np.mean(levy_result.durations):.2f} dias")
    print(f"   ✓ Desvio padrão: {np.std(levy_result.durations):.2f} dias")
    
    # Detectar quebras estruturais
    breaks_info = analyzer.detect_structural_breaks()
    n_breaks = len(breaks_info['breaks'])
    print(f"\n🎯 Quebras estruturais detectadas: {n_breaks}")
    
    # Mapear quebras para datas
    breaks_with_dates = []
    for brk in breaks_info['breaks']:
        section_idx = brk['index']
        if section_idx < len(levy_result.start_indices):
            date_idx = levy_result.start_indices[section_idx]
            if date_idx < len(dates):
                break_date = dates[date_idx]
                brk['date'] = break_date
                breaks_with_dates.append(brk)
                
                print(f"\n   📅 {break_date.strftime('%Y-%m-%d')}:")
                print(f"      Duração: {brk['mean_before']:.1f} → {brk['mean_after']:.1f} dias")
                print(f"      Razão: {brk['change_ratio']:.3f}")
                
                if brk['change_ratio'] < 0.7:
                    print(f"      ⚠️  Aumento significativo de volatilidade")
                elif brk['change_ratio'] > 1.3:
                    print(f"      ✅ Redução significativa de volatilidade")
    
    # Extrair features
    features = analyzer.extract_features()
    print(f"\n📈 Features extraídas:")
    print(f"   Curtose normalizada: {features['levy_norm_kurtosis']:.4f}")
    print(f"   P-valor Shapiro-Wilk: {features['levy_shapiro_pvalue']:.4f}")
    print(f"   Autocorrelação durações: {features.get('levy_duration_autocorr', np.nan):.4f}")
    
    # Criar visualizações
    if save_results:
        print(f"\n🎨 Gerando visualizações...")
        fig = analyzer.plot_analysis(breaks_info, title_prefix=ticker)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fig_path = f"outputs/figures/levy_{ticker.replace('.', '_')}_{timestamp}.png"
        fig.savefig(fig_path, dpi=300, bbox_inches='tight')
        print(f"   ✓ Gráfico salvo em: {fig_path}")
        plt.close()
    
    # Preparar resultados
    results = {
        'analyzer': analyzer,
        'levy_result': levy_result,
        'breaks_info': breaks_info,
        'breaks_with_dates': breaks_with_dates,
        'features': features,
        'params': {'tau': tau, 'q': q}
    }
    
    return results


def create_summary_report(data, results, ticker):
    """
    Cria relatório resumido da análise.
    
    Args:
        data: DataFrame com dados originais
        results: Resultados da análise de Lévy
        ticker: Nome do ativo
        
    Returns:
        DataFrame com resumo
    """
    print(f"\n📝 Criando relatório resumido...")
    
    # Estatísticas básicas
    returns = data['Returns']
    
    summary = {
        'Ativo': ticker,
        'Período': f"{data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}",
        'Observações': len(data),
        'Retorno Anual (%)': returns.mean() * 252 * 100,
        'Volatilidade Anual (%)': returns.std() * np.sqrt(252) * 100,
        'Sharpe Ratio': (returns.mean() * 252) / (returns.std() * np.sqrt(252)),
        'Curtose Original': returns.kurtosis(),
        'VaR 5% (%)': returns.quantile(0.05) * 100,
        'Parâmetro tau': results['params']['tau'],
        'Parâmetro q': results['params']['q'],
        'Número de Seções': len(results['levy_result'].S_tau),
        'Duração Média (dias)': np.mean(results['levy_result'].durations),
        'CV Durações': np.std(results['levy_result'].durations) / np.mean(results['levy_result'].durations),
        'Quebras Detectadas': len(results['breaks_with_dates']),
        'Curtose Normalizada': results['features']['levy_norm_kurtosis'],
        'P-valor Normalidade': results['features']['levy_shapiro_pvalue']
    }
    
    return pd.DataFrame([summary]).T


def save_results(data, results, ticker):
    """
    Salva todos os resultados em arquivos.
    
    Args:
        data: DataFrame com dados originais
        results: Resultados da análise
        ticker: Nome do ativo
    """
    print(f"\n💾 Salvando resultados...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f"{ticker.replace('.', '_')}_{timestamp}"
    
    # 1. Salvar quebras detectadas
    if results['breaks_with_dates']:
        breaks_df = pd.DataFrame(results['breaks_with_dates'])
        breaks_df['date'] = pd.to_datetime(breaks_df['date'])
        breaks_file = f"outputs/data/breaks_{base_name}.csv"
        breaks_df.to_csv(breaks_file, index=False)
        print(f"   ✓ Quebras salvas em: {breaks_file}")
    
    # 2. Salvar features
    features_df = pd.DataFrame([results['features']])
    features_file = f"outputs/data/features_{base_name}.csv"
    features_df.to_csv(features_file, index=False)
    print(f"   ✓ Features salvas em: {features_file}")
    
    # 3. Salvar durações das seções
    durations_df = pd.DataFrame({
        'section_index': range(len(results['levy_result'].durations)),
        'duration': results['levy_result'].durations,
        'start_index': results['levy_result'].start_indices,
        'end_index': results['levy_result'].end_indices
    })
    durations_file = f"outputs/data/durations_{base_name}.csv"
    durations_df.to_csv(durations_file, index=False)
    print(f"   ✓ Durações salvas em: {durations_file}")
    
    # 4. Salvar relatório resumido
    summary_df = create_summary_report(data, results, ticker)
    summary_file = f"outputs/summary_{base_name}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write(f"ANÁLISE DE QUEBRAS ESTRUTURAIS - SEÇÕES DE LÉVY\n")
        f.write("="*60 + "\n\n")
        f.write(summary_df.to_string())
        f.write("\n\n" + "="*60 + "\n")
        f.write("QUEBRAS ESTRUTURAIS DETECTADAS:\n")
        f.write("="*60 + "\n")
        
        for i, brk in enumerate(results['breaks_with_dates']):
            f.write(f"\n{i+1}. {brk['date'].strftime('%Y-%m-%d')}\n")
            f.write(f"   Duração antes: {brk['mean_before']:.1f} dias\n")
            f.write(f"   Duração depois: {brk['mean_after']:.1f} dias\n")
            f.write(f"   Razão de mudança: {brk['change_ratio']:.3f}\n")
            f.write(f"   P-valor: {brk['p_value']:.4f}\n")
    
    print(f"   ✓ Resumo salvo em: {summary_file}")


def run_multi_tau_analysis(data, ticker, tau_values=None, q=5):
    """
    Executa análise com múltiplos valores de tau.
    
    Args:
        data: DataFrame com dados
        ticker: Nome do ativo
        tau_values: Lista de valores de tau
        q: Janela para volatilidade local
        
    Returns:
        DataFrame com resultados consolidados
    """
    if tau_values is None:
        tau_values = [0.001, 0.005, 0.01, 0.02, 0.05]
    
    print(f"\n🔄 Executando análise com múltiplos tau: {tau_values}")
    
    returns = data['Returns'].values
    dates = data.index
    
    # Executar análise para cada tau
    all_breaks = analyze_structural_breaks_for_series(returns, dates, tau_values, q)
    
    if not all_breaks.empty:
        print(f"\n📊 Resumo consolidado:")
        print(f"   Total de quebras: {len(all_breaks)}")
        
        # Agrupar por período (quebras próximas)
        all_breaks['year_month'] = pd.to_datetime(all_breaks['break_date']).dt.to_period('M')
        consistent = all_breaks.groupby('year_month').agg({
            'tau': 'count',
            'change_ratio': 'mean',
            'break_date': 'first'
        }).rename(columns={'tau': 'count'})
        
        # Filtrar quebras consistentes (detectadas em múltiplos tau)
        consistent = consistent[consistent['count'] >= 2]
        
        if not consistent.empty:
            print(f"\n   🎯 Quebras consistentes (detectadas em ≥2 tau):")
            for idx, row in consistent.iterrows():
                print(f"      {idx}: {row['count']} detecções, razão média = {row['change_ratio']:.3f}")
    
    return all_breaks


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Análise de quebras estruturais com seções de Lévy'
    )
    
    parser.add_argument('--ticker', type=str, default='^BVSP',
                        help='Símbolo do ativo (ex: PETR4.SA, ^BVSP, BTC-USD)')
    parser.add_argument('--start', type=str, default='2019-01-01',
                        help='Data inicial (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2024-12-31',
                        help='Data final (YYYY-MM-DD)')
    parser.add_argument('--tau', type=float, default=0.005,
                        help='Parâmetro tau (default: 0.005)')
    parser.add_argument('--q', type=int, default=5,
                        help='Janela para volatilidade local (default: 5)')
    parser.add_argument('--multi-tau', action='store_true',
                        help='Executar análise com múltiplos valores de tau')
    parser.add_argument('--no-save', action='store_true',
                        help='Não salvar resultados em arquivos')
    
    args = parser.parse_args()
    
    # Setup
    setup_directories()
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette('husl')
    
    print("\n" + "="*60)
    print("ANÁLISE DE QUEBRAS ESTRUTURAIS COM SEÇÕES DE LÉVY")
    print("="*60)
    
    # Carregar dados
    data = load_data(args.ticker, args.start, args.end)
    
    # Análise principal
    results = analyze_levy_sections(
        data, 
        args.ticker, 
        tau=args.tau, 
        q=args.q,
        save_results=not args.no_save
    )
    
    # Análise multi-tau se solicitada
    if args.multi_tau:
        multi_results = run_multi_tau_analysis(data, args.ticker, q=args.q)
        if not args.no_save and not multi_results.empty:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            multi_file = f"outputs/data/multi_tau_{args.ticker.replace('.', '_')}_{timestamp}.csv"
            multi_results.to_csv(multi_file, index=False)
            print(f"\n✅ Análise multi-tau salva em: {multi_file}")
    
    # Salvar resultados
    if not args.no_save:
        save_results(data, results, args.ticker)
    
    print("\n" + "="*60)
    print("✨ ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("="*60)
    
    # Mostrar resumo final
    summary = create_summary_report(data, results, args.ticker)
    print(f"\n{summary.to_string()}")
    
    print(f"\n📂 Resultados salvos em: outputs/")
    print(f"   - Visualizações: outputs/figures/")
    print(f"   - Dados: outputs/data/")
    print(f"   - Resumos: outputs/summary_*.txt")


if __name__ == "__main__":
    main()