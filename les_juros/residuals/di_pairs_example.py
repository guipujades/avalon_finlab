"""
Exemplo simplificado da estratégia de Pairs Trading com DIs
Demonstração do conceito sem dependências externas
"""

import random
from datetime import datetime, timedelta

class SimpleDiPairsTrading:
    """
    Estratégia simplificada de pairs trading com contratos DI.
    """
    
    def __init__(self, di_long='DI1F25', di_short='DI1F26', window=20, n_std=2.0):
        self.di_long = di_long
        self.di_short = di_short
        self.window = window
        self.n_std = n_std
        
    def generate_sample_data(self, n_days=100):
        """Gera dados de exemplo para demonstração"""
        print(f"\nGerando {n_days} dias de dados simulados...")
        
        # Simula taxas DI com correlação
        base_rate = 13.0  # Taxa base
        dates = []
        rates_long = []
        rates_short = []
        
        for i in range(n_days):
            date = datetime.now() - timedelta(days=n_days-i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            # Adiciona ruído correlacionado
            noise_common = random.gauss(0, 0.1)
            noise_long = random.gauss(0, 0.05)
            noise_short = random.gauss(0, 0.05)
            
            # DI mais curto tem taxa menor (curva normal)
            rate_long = base_rate + noise_common + noise_long
            rate_short = base_rate + 0.3 + noise_common + noise_short  # 30bps acima
            
            rates_long.append(rate_long)
            rates_short.append(rate_short)
            
        return dates, rates_long, rates_short
    
    def calculate_spread(self, rates_long, rates_short):
        """Calcula o spread entre as taxas"""
        return [long - short for long, short in zip(rates_long, rates_short)]
    
    def calculate_bollinger_bands(self, spread):
        """Calcula bandas de Bollinger simplificadas"""
        bands = {
            'media': [],
            'superior': [],
            'inferior': []
        }
        
        for i in range(len(spread)):
            if i < self.window:
                bands['media'].append(None)
                bands['superior'].append(None)
                bands['inferior'].append(None)
            else:
                # Calcula média e desvio padrão da janela
                window_data = spread[i-self.window:i]
                media = sum(window_data) / len(window_data)
                
                # Desvio padrão
                variance = sum((x - media) ** 2 for x in window_data) / len(window_data)
                std_dev = variance ** 0.5
                
                bands['media'].append(media)
                bands['superior'].append(media + self.n_std * std_dev)
                bands['inferior'].append(media - self.n_std * std_dev)
                
        return bands
    
    def generate_signals(self, spread, bands):
        """Gera sinais de trading"""
        signals = []
        posicao = 0
        
        for i in range(len(spread)):
            if i < self.window:
                signals.append({'posicao': 0, 'acao': 'aguardando'})
                continue
                
            spread_atual = spread[i]
            media = bands['media'][i]
            banda_sup = bands['superior'][i]
            banda_inf = bands['inferior'][i]
            
            # Lógica de entrada e saída
            if posicao == 0:  # Sem posição
                if spread_atual > banda_sup:
                    posicao = -1  # Vende spread
                    signals.append({'posicao': -1, 'acao': 'venda_spread'})
                elif spread_atual < banda_inf:
                    posicao = 1   # Compra spread
                    signals.append({'posicao': 1, 'acao': 'compra_spread'})
                else:
                    signals.append({'posicao': 0, 'acao': 'aguardando'})
            else:  # Com posição
                # Sai quando volta para a média
                if posicao == -1 and spread_atual <= media:
                    posicao = 0
                    signals.append({'posicao': 0, 'acao': 'fecha_venda'})
                elif posicao == 1 and spread_atual >= media:
                    posicao = 0
                    signals.append({'posicao': 0, 'acao': 'fecha_compra'})
                else:
                    signals.append({'posicao': posicao, 'acao': 'mantém'})
                    
        return signals
    
    def run_example(self):
        """Executa exemplo da estratégia"""
        print("\n=== ESTRATÉGIA DE PAIRS TRADING COM DIs ===")
        print(f"DI Long: {self.di_long}")
        print(f"DI Short: {self.di_short}")
        print(f"Janela: {self.window} dias")
        print(f"Desvio Padrão: {self.n_std}")
        
        # Gera dados
        dates, rates_long, rates_short = self.generate_sample_data()
        
        # Calcula spread
        spread = self.calculate_spread(rates_long, rates_short)
        
        # Calcula bandas
        bands = self.calculate_bollinger_bands(spread)
        
        # Gera sinais
        signals = self.generate_signals(spread, bands)
        
        # Conta operações
        trades = 0
        for i in range(1, len(signals)):
            if signals[i]['acao'] in ['compra_spread', 'venda_spread']:
                trades += 1
        
        print(f"\nTotal de trades gerados: {trades}")
        
        # Mostra últimos 10 dias
        print("\nÚltimos 10 dias de operação:")
        print("Data        | Taxa Long | Taxa Short | Spread | Banda Inf | Média | Banda Sup | Sinal")
        print("-" * 90)
        
        for i in range(max(0, len(dates)-10), len(dates)):
            if bands['media'][i] is not None:
                print(f"{dates[i]} | {rates_long[i]:9.2f} | {rates_short[i]:10.2f} | "
                      f"{spread[i]:6.2f} | {bands['inferior'][i]:9.2f} | "
                      f"{bands['media'][i]:5.2f} | {bands['superior'][i]:9.2f} | "
                      f"{signals[i]['acao']}")


# Executa exemplo
if __name__ == "__main__":
    print("\nESTRATÉGIA DE PAIRS TRADING COM CONTRATOS DI")
    print("=" * 50)
    print("\nCONCEITO:")
    print("- Monitora o spread entre dois contratos DI de vencimentos diferentes")
    print("- Quando o spread sai das bandas de Bollinger, abre posição")
    print("- Fecha posição quando o spread retorna à média")
    print("\nLÓGICA:")
    print("- Spread > Banda Superior: Vende spread (vende DI curto, compra DI longo)")
    print("- Spread < Banda Inferior: Compra spread (compra DI curto, vende DI longo)")
    
    # Cria e executa estratégia
    strategy = SimpleDiPairsTrading(
        di_long='DI1F25',
        di_short='DI1F26',
        window=20,
        n_std=2.0
    )
    
    strategy.run_example()
    
    print("\n\nOBSERVAÇÕES IMPORTANTES:")
    print("- Este é um exemplo simplificado para demonstração")
    print("- Na prática, deve-se considerar:")
    print("  * Custos operacionais e slippage")
    print("  * Ajustes diários dos contratos")
    print("  * Cálculo correto de PU baseado em dias úteis")
    print("  * Gestão de risco e stops")
    print("  * Análise de correlação histórica entre os contratos")