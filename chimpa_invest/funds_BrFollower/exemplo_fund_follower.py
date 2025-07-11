import pandas as pd
import numpy as np
import os
from fund_follower_base import FundFollower
from extrair_retornos_universo import ExtractorRetornosFundos
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta

def obter_benchmark_ibovespa(periodo_inicial: str, periodo_final: str) -> pd.Series:
    """
    Obtém retornos do Ibovespa para cálculo de beta
    
    Args:
        periodo_inicial: Data inicial (YYYY-MM)
        periodo_final: Data final (YYYY-MM)
        
    Returns:
        Série com retornos mensais do Ibovespa
    """
    try:
        inicio = datetime.strptime(periodo_inicial, "%Y-%m")
        fim = datetime.strptime(periodo_final, "%Y-%m") + timedelta(days=31)
        
        ibov = yf.download("^BVSP", start=inicio, end=fim, progress=False)
        
        if not ibov.empty:
            ibov['retorno_diario'] = ibov['Adj Close'].pct_change()
            retorno_mensal = ibov['retorno_diario'].resample('M').apply(lambda x: (1 + x).prod() - 1)
            return retorno_mensal
    except:
        print("Erro ao baixar dados do Ibovespa. Gerando série sintética...")
        
        dates = pd.date_range(start=periodo_inicial, end=periodo_final, freq='M')
        retornos = np.random.normal(0.008, 0.045, len(dates))
        return pd.Series(retornos, index=dates)


def calcular_betas_universo(retornos_universo: pd.DataFrame, retornos_mercado: pd.Series) -> dict:
    """
    Calcula betas de todos os fundos em relação ao mercado
    
    Args:
        retornos_universo: DataFrame com retornos dos fundos
        retornos_mercado: Série com retornos do mercado
        
    Returns:
        Dicionário com betas dos fundos
    """
    betas = {}
    
    for fundo in retornos_universo.columns:
        try:
            dados_alinhados = pd.DataFrame({
                'fundo': retornos_universo[fundo],
                'mercado': retornos_mercado
            }).dropna()
            
            if len(dados_alinhados) >= 12:
                cov = dados_alinhados.cov().iloc[0, 1]
                var_mercado = dados_alinhados['mercado'].var()
                beta = cov / var_mercado
                betas[fundo] = beta
        except:
            continue
    
    return betas


def exemplo_completo():
    """Exemplo completo de uso do Fund Follower"""
    
    print("="*60)
    print("FUND FOLLOWER - EXEMPLO COMPLETO")
    print("="*60)
    
    cnpj_kokorikus = "38.351.476/0001-40"
    
    print("\n1. Verificando se há dados do universo de fundos...")
    if not os.path.exists("dados_universo/retornos_mensais_universo.csv"):
        print("   Dados não encontrados. Extraindo amostra...")
        from extrair_retornos_universo import extrair_amostra_pequena
        df_universo = extrair_amostra_pequena()
    else:
        print("   Carregando dados existentes...")
        df_universo = pd.read_csv("dados_universo/retornos_mensais_universo.csv", 
                                  index_col=0, parse_dates=True)
    
    if df_universo.empty:
        print("ERRO: Não foi possível obter dados do universo de fundos")
        return
    
    print(f"   Universo carregado: {len(df_universo.columns)} fundos")
    
    print("\n2. Inicializando Fund Follower...")
    follower = FundFollower(cnpj_kokorikus, "KOKORIKUS FI AÇÕES")
    
    print("\n3. Carregando retornos do fundo alvo...")
    try:
        follower.load_target_returns()
        print(f"   Retornos carregados: {len(follower.returns_target)} observações")
    except Exception as e:
        print(f"   ERRO: {e}")
        print("   Gerando retornos sintéticos para demonstração...")
        dates = pd.date_range(start='2020-01', end='2024-08', freq='M')
        retornos_sinteticos = np.random.normal(0.012, 0.06, len(dates))
        follower.returns_target = pd.Series(retornos_sinteticos, index=dates)
    
    print("\n4. Alinhando períodos...")
    periodo_comum_inicio = max(follower.returns_target.index[0], df_universo.index[0])
    periodo_comum_fim = min(follower.returns_target.index[-1], df_universo.index[-1])
    
    follower.returns_target = follower.returns_target[periodo_comum_inicio:periodo_comum_fim]
    df_universo_alinhado = df_universo[periodo_comum_inicio:periodo_comum_fim]
    
    print(f"   Período comum: {periodo_comum_inicio.strftime('%Y-%m')} a {periodo_comum_fim.strftime('%Y-%m')}")
    
    print("\n5. Carregando universo de retornos no Fund Follower...")
    follower.load_universe_returns(df_universo_alinhado)
    
    print("\n6. Dividindo dados (40% treino, 60% teste)...")
    follower.split_data(train_ratio=0.4)
    
    print("\n7. Calculando beta do fundo alvo...")
    periodo_str_inicio = follower.returns_target.index[0].strftime('%Y-%m')
    periodo_str_fim = follower.returns_target.index[-1].strftime('%Y-%m')
    retornos_mercado = obter_benchmark_ibovespa(periodo_str_inicio, periodo_str_fim)
    follower.calculate_beta(retornos_mercado)
    
    print("\n8. Versão Benchmark - Seleção por Beta...")
    if follower.beta_target is not None:
        print("   Calculando betas do universo...")
        betas_universo = calcular_betas_universo(df_universo_alinhado, retornos_mercado)
        print(f"   Betas calculados para {len(betas_universo)} fundos")
        
        follower.benchmark_beta_matching(betas_universo)
    
    print("\n9. Otimização - Minimizando Tracking Error...")
    follower.optimize_weights_minimum_tracking_error()
    
    print("\n10. Avaliação Out-of-Sample...")
    follower.evaluate_out_of_sample()
    
    print("\n11. Salvando resultados...")
    follower.save_results()
    
    print("\n12. Análise adicional...")
    if follower.weights_optimal is not None:
        n_ativos_selecionados = np.sum(follower.weights_optimal > 0.01)
        print(f"   Número de ativos na carteira ótima: {n_ativos_selecionados}")
        
        concentracao_top5 = np.sum(np.sort(follower.weights_optimal)[-5:])
        print(f"   Concentração nos 5 maiores: {concentracao_top5:.1%}")
    
    print("\n" + "="*60)
    print("ANÁLISE CONCLUÍDA!")
    print("="*60)


def exemplo_simples_benchmark():
    """Exemplo simplificado focado apenas no benchmark por beta"""
    
    print("="*60)
    print("FUND FOLLOWER - BENCHMARK POR BETA")
    print("="*60)
    
    print("\n1. Gerando dados sintéticos para demonstração...")
    
    np.random.seed(42)
    dates = pd.date_range(start='2020-01', end='2024-08', freq='M')
    
    retornos_mercado = np.random.normal(0.008, 0.045, len(dates))
    mercado = pd.Series(retornos_mercado, index=dates)
    
    beta_alvo = 1.2
    retornos_fundo_alvo = beta_alvo * retornos_mercado + np.random.normal(0, 0.02, len(dates))
    fundo_alvo = pd.Series(retornos_fundo_alvo, index=dates)
    
    print(f"   Beta do fundo alvo (teórico): {beta_alvo}")
    
    n_fundos = 50
    retornos_universo = {}
    betas_reais = {}
    
    for i in range(n_fundos):
        beta_i = np.random.uniform(0.5, 1.8)
        retornos_i = beta_i * retornos_mercado + np.random.normal(0, 0.025, len(dates))
        retornos_universo[f'Fundo_{i:03d}'] = retornos_i
        betas_reais[f'Fundo_{i:03d}'] = beta_i
    
    df_universo = pd.DataFrame(retornos_universo, index=dates)
    
    print(f"   Universo gerado: {n_fundos} fundos")
    print(f"   Range de betas: {min(betas_reais.values()):.2f} a {max(betas_reals.values()):.2f}")
    
    print("\n2. Selecionando fundos por proximidade de beta...")
    
    diffs_beta = {fundo: abs(beta - beta_alvo) for fundo, beta in betas_reais.items()}
    fundos_ordenados = sorted(diffs_beta.items(), key=lambda x: x[1])
    
    n_selecionar = 5
    fundos_selecionados = [fundo for fundo, _ in fundos_ordenados[:n_selecionar]]
    
    print(f"\n   Top {n_selecionar} fundos selecionados:")
    for fundo in fundos_selecionados:
        print(f"   - {fundo}: Beta = {betas_reais[fundo]:.3f}")
    
    print("\n3. Construindo portfolio equally-weighted...")
    portfolio_benchmark = df_universo[fundos_selecionados].mean(axis=1)
    
    print("\n4. Calculando métricas de performance...")
    
    tracking_error = (portfolio_benchmark - fundo_alvo).std() * np.sqrt(12)
    correlacao = portfolio_benchmark.corr(fundo_alvo)
    
    print(f"\n   Tracking Error (anualizado): {tracking_error:.2%}")
    print(f"   Correlação: {correlacao:.3f}")
    
    print("\n5. Visualizando resultados...")
    
    cumulative_alvo = (1 + fundo_alvo).cumprod()
    cumulative_portfolio = (1 + portfolio_benchmark).cumprod()
    cumulative_mercado = (1 + mercado).cumprod()
    
    plt.figure(figsize=(12, 6))
    plt.plot(dates, cumulative_alvo, label='Fundo Alvo', linewidth=2)
    plt.plot(dates, cumulative_portfolio, label='Portfolio Beta-Matching', linewidth=2, linestyle='--')
    plt.plot(dates, cumulative_mercado, label='Mercado (Ibovespa)', linewidth=1, alpha=0.7)
    
    plt.title('Benchmark por Beta-Matching')
    plt.xlabel('Data')
    plt.ylabel('Retorno Acumulado')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('benchmark_beta_matching.png', dpi=300)
    plt.show()
    
    print("\n" + "="*60)
    print("BENCHMARK CONCLUÍDO!")
    print("="*60)


if __name__ == "__main__":
    print("\nEscolha o tipo de exemplo:")
    print("1. Exemplo completo (dados reais + otimização)")
    print("2. Exemplo benchmark (dados sintéticos + beta matching)")
    
    opcao = input("\nOpção (1 ou 2): ").strip()
    
    if opcao == "2":
        exemplo_simples_benchmark()
    else:
        exemplo_completo()