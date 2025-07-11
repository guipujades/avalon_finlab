"""
Script de teste para estratégia de pairs trading com DIs
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from estrategia_pairs_di import DiPairsTrading
import matplotlib.pyplot as plt


def analyze_di_correlations(df, di_list):
    """
    Analisa correlações entre diferentes DIs para identificar melhores pares
    """
    print("\n=== ANÁLISE DE CORRELAÇÕES ===")
    
    # Calcula matriz de correlação
    corr_matrix = df[di_list].corr()
    
    # Identifica pares com alta correlação (> 0.9) mas não perfeita (< 0.99)
    good_pairs = []
    for i in range(len(di_list)):
        for j in range(i+1, len(di_list)):
            corr = corr_matrix.iloc[i, j]
            if 0.9 < corr < 0.99:
                good_pairs.append((di_list[i], di_list[j], corr))
    
    # Ordena por correlação
    good_pairs.sort(key=lambda x: x[2], reverse=True)
    
    print("\nMelhores pares para trading (correlação entre 0.9 e 0.99):")
    for di1, di2, corr in good_pairs[:10]:
        print(f"{di1} vs {di2}: correlação = {corr:.4f}")
    
    return good_pairs


def optimize_parameters(df, di_long, di_short, venc_long, venc_short):
    """
    Otimiza parâmetros da estratégia (janela e desvio padrão)
    """
    print(f"\n=== OTIMIZAÇÃO DE PARÂMETROS: {di_long} vs {di_short} ===")
    
    best_result = None
    best_params = None
    best_sharpe = -np.inf
    
    results_grid = []
    
    for window in [15, 20, 25, 30]:
        for n_std in [1.5, 2.0, 2.5, 3.0]:
            strategy = DiPairsTrading(di_long, di_short, window=window, n_std=n_std)
            results = strategy.backtest(df, venc_long, venc_short)
            
            if 'sharpe_ratio' in results['metrics']:
                sharpe = results['metrics']['sharpe_ratio']
                total = results['metrics']['resultado_total']
                trades = results['metrics']['total_trades']
                
                results_grid.append({
                    'window': window,
                    'n_std': n_std,
                    'sharpe': sharpe,
                    'total': total,
                    'trades': trades
                })
                
                if sharpe > best_sharpe and trades > 5:  # Mínimo de 5 trades
                    best_sharpe = sharpe
                    best_result = results
                    best_params = (window, n_std)
    
    # Mostra grid de resultados
    print("\nGrid de Resultados:")
    print("Window | N_Std | Sharpe | Total | Trades")
    print("-" * 45)
    for r in results_grid:
        print(f"{r['window']:6d} | {r['n_std']:5.1f} | {r['sharpe']:6.2f} | {r['total']:6.0f} | {r['trades']:6d}")
    
    if best_params:
        print(f"\nMelhores parâmetros: Window={best_params[0]}, N_Std={best_params[1]}")
        print(f"Sharpe Ratio: {best_sharpe:.2f}")
    
    return best_params, best_result


def create_performance_report(results, di_long, di_short):
    """
    Cria relatório detalhado de performance
    """
    print(f"\n=== RELATÓRIO DE PERFORMANCE: {di_long} vs {di_short} ===")
    
    if not results['trades']:
        print("Nenhum trade executado!")
        return
    
    trades_df = pd.DataFrame(results['trades'])
    trades_fechados = trades_df[trades_df['resultado_liquido'].notna()]
    
    if trades_fechados.empty:
        print("Nenhum trade fechado!")
        return
    
    # Estatísticas detalhadas
    print("\n1. RESUMO GERAL:")
    print(f"   - Total de trades: {len(trades_fechados)}")
    print(f"   - Taxa de acerto: {results['metrics']['win_rate']:.1f}%")
    print(f"   - Resultado total: {results['metrics']['resultado_total']:.0f} pontos")
    print(f"   - Resultado médio: {results['metrics']['resultado_medio']:.1f} pontos")
    
    print("\n2. ANÁLISE DE RISCO:")
    print(f"   - Maior ganho: {results['metrics']['maior_gain']:.0f} pontos")
    print(f"   - Maior perda: {results['metrics']['maior_loss']:.0f} pontos")
    print(f"   - Sharpe Ratio: {results['metrics']['sharpe_ratio']:.2f}")
    
    # Análise temporal
    trades_fechados['mes'] = pd.to_datetime(trades_fechados['data_saida']).dt.to_period('M')
    resultado_mensal = trades_fechados.groupby('mes')['resultado_liquido'].sum()
    
    print("\n3. PERFORMANCE MENSAL:")
    for mes, resultado in resultado_mensal.items():
        print(f"   - {mes}: {resultado:+.0f} pontos")
    
    # Duração média dos trades
    trades_fechados['duracao'] = (pd.to_datetime(trades_fechados['data_saida']) - 
                                  pd.to_datetime(trades_fechados['data_entrada'])).dt.days
    
    print("\n4. DURAÇÃO DOS TRADES:")
    print(f"   - Duração média: {trades_fechados['duracao'].mean():.1f} dias")
    print(f"   - Duração máxima: {trades_fechados['duracao'].max()} dias")
    print(f"   - Duração mínima: {trades_fechados['duracao'].min()} dias")


def plot_spread_analysis(df, di_pairs):
    """
    Plota análise comparativa de spreads
    """
    fig, axes = plt.subplots(len(di_pairs), 1, figsize=(12, 4*len(di_pairs)), sharex=True)
    
    if len(di_pairs) == 1:
        axes = [axes]
    
    for idx, (di1, di2) in enumerate(di_pairs):
        if di1 in df.columns and di2 in df.columns:
            spread = df[di1] - df[di2]
            spread_ma = spread.rolling(20).mean()
            spread_std = spread.rolling(20).std()
            
            axes[idx].plot(spread.index, spread, label=f'Spread {di1}-{di2}', alpha=0.7)
            axes[idx].plot(spread_ma.index, spread_ma, 'r--', label='MA(20)')
            axes[idx].fill_between(spread.index, 
                                  spread_ma - 2*spread_std, 
                                  spread_ma + 2*spread_std, 
                                  alpha=0.2, color='gray')
            
            axes[idx].set_ylabel('Spread (bps)')
            axes[idx].legend()
            axes[idx].grid(True, alpha=0.3)
            axes[idx].set_title(f'Spread Analysis: {di1} vs {di2}')
    
    axes[-1].set_xlabel('Data')
    plt.tight_layout()
    plt.show()


def main():
    """
    Função principal de teste
    """
    # Carrega dados
    data_path = Path(__file__).parent / 'futures_v2.pkl'
    
    try:
        with open(data_path, 'rb') as f:
            df = pickle.load(f)
        
        print("=== ESTRATÉGIA DE PAIRS TRADING COM DIs ===")
        print(f"Dados carregados: {len(df)} dias")
        print(f"Período: {df.index[0]} a {df.index[-1]}")
        
        # Lista DIs disponíveis
        di_columns = [col for col in df.columns if col.startswith('DI1')]
        print(f"\nContratos DI disponíveis: {len(di_columns)}")
        
        # Analisa correlações
        if len(di_columns) > 10:
            di_list = di_columns[:20]  # Primeiros 20 DIs
        else:
            di_list = di_columns
            
        good_pairs = analyze_di_correlations(df, di_list)
        
        # Testa estratégia com melhor par
        if good_pairs:
            di_long, di_short, _ = good_pairs[0]
            
            # Define vencimentos (simplificado - ajustar conforme necessário)
            venc_long = pd.Timestamp('2025-01-02')
            venc_short = pd.Timestamp('2026-01-02')
            
            # Otimiza parâmetros
            best_params, best_results = optimize_parameters(
                df, di_long, di_short, venc_long, venc_short
            )
            
            if best_results:
                # Cria relatório de performance
                create_performance_report(best_results, di_long, di_short)
                
                # Plota estratégia otimizada
                strategy = DiPairsTrading(
                    di_long, di_short, 
                    window=best_params[0], 
                    n_std=best_params[1]
                )
                strategy.plot_strategy(best_results)
        
        # Análise comparativa de spreads
        test_pairs = [
            ('DI1F24', 'DI1F25'),
            ('DI1F25', 'DI1F26'),
            ('DI1F26', 'DI1F27')
        ]
        plot_spread_analysis(df, test_pairs)
        
    except FileNotFoundError:
        print(f"Erro: Arquivo {data_path} não encontrado!")
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()