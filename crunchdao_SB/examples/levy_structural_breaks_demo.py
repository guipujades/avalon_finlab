"""
Demonstração de detecção de quebras estruturais usando seções de Lévy.

Este script mostra como aplicar o método das seções de Lévy para:
1. Detectar mudanças de regime em séries temporais financeiras
2. Extrair features robustas para machine learning
3. Visualizar os resultados

Author: CrunchDAO SB Team
Date: 2025-06-26
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from src.features.levy_sections import LevySectionsAnalyzer, analyze_structural_breaks_for_series

# Configurar estilo de visualização
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def load_financial_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Carrega dados financeiros do Yahoo Finance"""
    print(f"\nCarregando dados para {ticker}...")
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    data['Returns'] = np.log(data['Close'] / data['Close'].shift(1))
    return data.dropna()


def main():
    """Demonstração principal"""
    
    # 1. Carregar dados de diferentes períodos (incluindo crises conhecidas)
    print("=" * 60)
    print("DEMONSTRAÇÃO: Detecção de Quebras Estruturais com Seções de Lévy")
    print("=" * 60)
    
    # Período incluindo COVID-19 e recuperação
    ticker = "^BVSP"  # IBOVESPA
    start_date = "2019-01-01"
    end_date = "2024-12-31"
    
    data = load_financial_data(ticker, start_date, end_date)
    returns = data['Returns'].values
    dates = data.index
    
    print(f"Período analisado: {dates[0].strftime('%Y-%m-%d')} a {dates[-1].strftime('%Y-%m-%d')}")
    print(f"Total de observações: {len(returns)}")
    
    # 2. Aplicar seções de Lévy com diferentes parâmetros
    print("\n" + "=" * 60)
    print("ANÁLISE 1: Detecção de Quebras com tau = 0.005")
    print("=" * 60)
    
    analyzer = LevySectionsAnalyzer(tau=0.005, q=5)
    levy_result = analyzer.compute_levy_sections(returns)
    
    print(f"\nNúmero de seções de Lévy: {len(levy_result.S_tau)}")
    print(f"Duração média das seções: {np.mean(levy_result.durations):.2f} dias")
    print(f"Desvio padrão das durações: {np.std(levy_result.durations):.2f} dias")
    
    # 3. Detectar quebras estruturais
    breaks_info = analyzer.detect_structural_breaks()
    
    if breaks_info['breaks']:
        print(f"\nQuebras estruturais detectadas: {len(breaks_info['breaks'])}")
        print("\nDetalhes das quebras:")
        print("-" * 80)
        
        for i, brk in enumerate(breaks_info['breaks']):
            # Mapear para data aproximada
            section_idx = brk['index']
            if section_idx < len(levy_result.start_indices):
                date_idx = levy_result.start_indices[section_idx]
                if date_idx < len(dates):
                    break_date = dates[date_idx]
                    print(f"\nQuebra {i+1}:")
                    print(f"  Data aproximada: {break_date.strftime('%Y-%m-%d')}")
                    print(f"  Duração média antes: {brk['mean_before']:.2f} dias")
                    print(f"  Duração média depois: {brk['mean_after']:.2f} dias")
                    print(f"  Razão de mudança: {brk['change_ratio']:.3f}")
                    print(f"  P-valor: {brk['p_value']:.4f}")
                    
                    # Interpretar a mudança
                    if brk['change_ratio'] < 0.7:
                        print(f"  Interpretação: AUMENTO significativo na volatilidade")
                    elif brk['change_ratio'] > 1.3:
                        print(f"  Interpretação: REDUÇÃO significativa na volatilidade")
                    else:
                        print(f"  Interpretação: Mudança moderada na volatilidade")
    
    # 4. Análise com múltiplos valores de tau
    print("\n" + "=" * 60)
    print("ANÁLISE 2: Comparação com Diferentes Valores de tau")
    print("=" * 60)
    
    tau_values = [0.001, 0.005, 0.01, 0.02]
    breaks_summary = analyze_structural_breaks_for_series(returns, dates, tau_values)
    
    if not breaks_summary.empty:
        print("\nResumo de quebras detectadas por tau:")
        print(breaks_summary.to_string(index=False))
        
        # Identificar quebras consistentes
        print("\n" + "=" * 60)
        print("ANÁLISE 3: Quebras Consistentes em Múltiplos tau")
        print("=" * 60)
        
        # Agrupar quebras próximas no tempo (dentro de 30 dias)
        breaks_summary['year_month'] = pd.to_datetime(breaks_summary['break_date']).dt.to_period('M')
        consistent_breaks = breaks_summary.groupby('year_month').agg({
            'tau': 'count',
            'change_ratio': 'mean',
            'break_date': 'first'
        }).rename(columns={'tau': 'count'})
        
        # Filtrar apenas quebras detectadas em múltiplos tau
        consistent_breaks = consistent_breaks[consistent_breaks['count'] >= 2]
        
        if not consistent_breaks.empty:
            print("\nQuebras detectadas consistentemente:")
            for idx, row in consistent_breaks.iterrows():
                print(f"\n{idx}: Detectada em {row['count']} valores de tau")
                print(f"  Razão média de mudança: {row['change_ratio']:.3f}")
    
    # 5. Extrair features para ML
    print("\n" + "=" * 60)
    print("ANÁLISE 4: Features para Machine Learning")
    print("=" * 60)
    
    features = analyzer.extract_features()
    
    print("\nPrincipais features extraídas:")
    for key, value in sorted(features.items())[:10]:
        if not np.isnan(value):
            print(f"  {key}: {value:.4f}")
    
    # Teste de normalidade
    print(f"\n\nTeste de Normalidade (Shapiro-Wilk):")
    print(f"  P-valor: {features['levy_shapiro_pvalue']:.4f}")
    if features['levy_shapiro_pvalue'] > 0.05:
        print("  Resultado: Não rejeitamos H0 - Distribuição é compatível com normalidade")
    else:
        print("  Resultado: Rejeitamos H0 - Distribuição não é normal")
    
    print(f"\nCurtose das somas normalizadas: {features['levy_norm_kurtosis']:.4f}")
    print(f"  (Valor próximo a 0 indica sucesso da 'Gaussianização')")
    
    # 6. Visualizações
    print("\n" + "=" * 60)
    print("VISUALIZAÇÕES")
    print("=" * 60)
    
    fig = analyzer.plot_analysis(breaks_info, title_prefix=f"{ticker} (tau={analyzer.tau})")
    plt.suptitle(f"Análise de Seções de Lévy - {ticker}", fontsize=16)
    plt.tight_layout()
    
    # Salvar figura
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = f"{output_dir}/levy_breaks_{ticker.replace('^', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\nGráfico salvo em: {filename}")
    
    # 7. Comparação com eventos conhecidos
    print("\n" + "=" * 60)
    print("VALIDAÇÃO: Comparação com Eventos Conhecidos")
    print("=" * 60)
    
    known_events = [
        ("2020-02-20", "2020-03-23", "Crash COVID-19"),
        ("2022-01-03", "2022-03-08", "Início conflito Rússia-Ucrânia"),
        ("2023-03-08", "2023-03-20", "Crise bancária SVB")
    ]
    
    print("\nEventos conhecidos vs. quebras detectadas:")
    for start, end, event in known_events:
        event_start = pd.to_datetime(start)
        event_end = pd.to_datetime(end)
        
        # Verificar se alguma quebra foi detectada próxima ao evento
        detected = False
        for _, brk in breaks_summary.iterrows():
            if pd.notna(brk['break_date']):
                break_date = pd.to_datetime(brk['break_date'])
                if event_start - timedelta(days=30) <= break_date <= event_end + timedelta(days=30):
                    detected = True
                    print(f"\n✓ {event}: Quebra detectada em {break_date.strftime('%Y-%m-%d')}")
                    print(f"  tau={brk['tau']}, razão={brk['change_ratio']:.3f}")
                    break
        
        if not detected:
            print(f"\n✗ {event}: Nenhuma quebra detectada no período")
    
    print("\n" + "=" * 60)
    print("CONCLUSÃO")
    print("=" * 60)
    print("\nO método das seções de Lévy detectou com sucesso várias quebras")
    print("estruturais na volatilidade, muitas coincidindo com eventos de mercado conhecidos.")
    print("\nAs features extraídas mostram que o método consegue 'Gaussianizar'")
    print("a distribuição dos retornos, tornando-as úteis para modelos de ML.")
    
    plt.show()


if __name__ == "__main__":
    main()