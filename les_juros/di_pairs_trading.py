import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, Dict, List, Optional
from datetime import datetime
import pickle
import xlrd
from urllib.request import urlretrieve


class DiPairsTrading:
    """
    Estratégia de pairs trading com contratos DI futuros.
    Long/Short em dois DIs diferentes, operando quando o spread sai das bandas.
    """
    
    def __init__(self, di_long: str, di_short: str, window: int = 20, n_std: float = 2.0):
        """
        Inicializa a estratégia de pairs trading.
        
        Parameters:
            di_long: Código do DI para posição comprada (ex: 'DI1F25')
            di_short: Código do DI para posição vendida (ex: 'DI1F26')
            window: Janela para cálculo da média móvel e desvio padrão
            n_std: Número de desvios padrão para as bandas
        """
        self.di_long = di_long
        self.di_short = di_short
        self.window = window
        self.n_std = n_std
        self.holidays_anbima = self._get_anbima_holidays()
        
    def _get_anbima_holidays(self) -> List[datetime]:
        """Obtém feriados da ANBIMA para cálculo de dias úteis"""
        try:
            url_anbima = 'http://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls'
            path = 'feriados_nacionais.xls'
            urlretrieve(url_anbima, filename=path)
            wb = xlrd.open_workbook(path)
            ws = wb.sheet_by_index(0)
            i = 1
            anbima_holidays = []
            while ws.cell_type(i, 0) == 3:
                y, m, d, _, _, _ = xlrd.xldate_as_tuple(ws.cell_value(i, 0), wb.datemode)
                anbima_holidays.append(pd.Timestamp(datetime(y, m, d)))
                i += 1
            return [d.date() for d in anbima_holidays]
        except:
            print("Aviso: Não foi possível obter feriados ANBIMA. Usando apenas fins de semana.")
            return []
    
    def calculate_di_pu(self, taxa: float, vencimento: pd.Timestamp, data_atual: pd.Timestamp) -> float:
        """
        Calcula o PU (Preço Unitário) do contrato DI.
        
        Parameters:
            taxa: Taxa do DI em % ao ano
            vencimento: Data de vencimento do contrato
            data_atual: Data atual para cálculo
            
        Returns:
            PU do contrato
        """
        du = np.busday_count(data_atual.date(), vencimento.date(), holidays=self.holidays_anbima)
        pu = 100_000 / (1 + taxa / 100) ** (du / 252)
        return pu
    
    def calculate_spread(self, df: pd.DataFrame, venc_long: pd.Timestamp, venc_short: pd.Timestamp) -> pd.Series:
        """
        Calcula o spread entre dois DIs.
        
        Parameters:
            df: DataFrame com taxas dos DIs
            venc_long: Data de vencimento do DI long
            venc_short: Data de vencimento do DI short
            
        Returns:
            Serie temporal do spread
        """
        spread_list = []
        
        for idx in df.index:
            if self.di_long in df.columns and self.di_short in df.columns:
                taxa_long = df.loc[idx, self.di_long]
                taxa_short = df.loc[idx, self.di_short]
                
                # Calcula PUs
                pu_long = self.calculate_di_pu(taxa_long, venc_long, idx)
                pu_short = self.calculate_di_pu(taxa_short, venc_short, idx)
                
                # Spread = diferença entre as taxas
                spread = taxa_long - taxa_short
                spread_list.append(spread)
            else:
                spread_list.append(np.nan)
                
        return pd.Series(spread_list, index=df.index, name='spread')
    
    def calculate_bollinger_bands(self, spread: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcula as bandas de Bollinger para o spread.
        
        Parameters:
            spread: Serie temporal do spread
            
        Returns:
            media_movel, banda_superior, banda_inferior
        """
        media_movel = spread.rolling(window=self.window).mean()
        desvio_padrao = spread.rolling(window=self.window).std()
        
        banda_superior = media_movel + (self.n_std * desvio_padrao)
        banda_inferior = media_movel - (self.n_std * desvio_padrao)
        
        return media_movel, banda_superior, banda_inferior
    
    def generate_signals(self, spread: pd.Series, banda_superior: pd.Series, 
                        banda_inferior: pd.Series) -> pd.DataFrame:
        """
        Gera sinais de entrada e saída baseados nas bandas.
        
        Parameters:
            spread: Serie temporal do spread
            banda_superior: Banda superior de Bollinger
            banda_inferior: Banda inferior de Bollinger
            
        Returns:
            DataFrame com sinais
        """
        signals = pd.DataFrame(index=spread.index)
        signals['spread'] = spread
        signals['banda_superior'] = banda_superior
        signals['banda_inferior'] = banda_inferior
        signals['posicao'] = 0
        
        # Quando spread > banda superior: vende spread (compra short, vende long)
        # Quando spread < banda inferior: compra spread (compra long, vende short)
        
        for i in range(1, len(signals)):
            if pd.notna(spread.iloc[i]) and pd.notna(banda_superior.iloc[i]):
                # Entrada
                if spread.iloc[i] > banda_superior.iloc[i] and signals['posicao'].iloc[i-1] == 0:
                    signals.loc[signals.index[i], 'posicao'] = -1  # Vende spread
                elif spread.iloc[i] < banda_inferior.iloc[i] and signals['posicao'].iloc[i-1] == 0:
                    signals.loc[signals.index[i], 'posicao'] = 1   # Compra spread
                # Saída (volta para a média)
                elif signals['posicao'].iloc[i-1] == -1 and spread.iloc[i] <= spread.rolling(self.window).mean().iloc[i]:
                    signals.loc[signals.index[i], 'posicao'] = 0
                elif signals['posicao'].iloc[i-1] == 1 and spread.iloc[i] >= spread.rolling(self.window).mean().iloc[i]:
                    signals.loc[signals.index[i], 'posicao'] = 0
                else:
                    signals.loc[signals.index[i], 'posicao'] = signals['posicao'].iloc[i-1]
        
        # Identifica trades
        signals['trade'] = signals['posicao'].diff().fillna(0)
        
        return signals
    
    def backtest(self, df: pd.DataFrame, venc_long: pd.Timestamp, venc_short: pd.Timestamp,
                 custo_operacional: float = 5.0) -> Dict:
        """
        Executa backtest da estratégia.
        
        Parameters:
            df: DataFrame com dados históricos
            venc_long: Data de vencimento do DI long
            venc_short: Data de vencimento do DI short
            custo_operacional: Custo por operação em pontos
            
        Returns:
            Dicionário com resultados e métricas
        """
        # Calcula spread
        spread = self.calculate_spread(df, venc_long, venc_short)
        
        # Calcula bandas
        media_movel, banda_superior, banda_inferior = self.calculate_bollinger_bands(spread)
        
        # Gera sinais
        signals = self.generate_signals(spread, banda_superior, banda_inferior)
        
        # Calcula retornos
        trades = []
        posicao_atual = 0
        entrada_spread = None
        
        for idx in signals.index:
            trade_signal = signals.loc[idx, 'trade']
            
            if trade_signal != 0:
                if posicao_atual == 0:  # Entrada
                    entrada_spread = signals.loc[idx, 'spread']
                    posicao_atual = signals.loc[idx, 'posicao']
                    trades.append({
                        'data_entrada': idx,
                        'spread_entrada': entrada_spread,
                        'tipo': 'compra_spread' if posicao_atual == 1 else 'venda_spread',
                        'posicao': posicao_atual
                    })
                else:  # Saída
                    saida_spread = signals.loc[idx, 'spread']
                    resultado_bruto = (saida_spread - entrada_spread) * posicao_atual * -100  # -100 para inverter sinal
                    resultado_liquido = resultado_bruto - custo_operacional
                    
                    trades[-1].update({
                        'data_saida': idx,
                        'spread_saida': saida_spread,
                        'resultado_bruto': resultado_bruto,
                        'resultado_liquido': resultado_liquido
                    })
                    posicao_atual = 0
        
        # Calcula métricas
        trades_fechados = [t for t in trades if 'resultado_liquido' in t]
        
        if trades_fechados:
            resultados = [t['resultado_liquido'] for t in trades_fechados]
            wins = [r for r in resultados if r > 0]
            losses = [r for r in resultados if r < 0]
            
            metrics = {
                'total_trades': len(trades_fechados),
                'wins': len(wins),
                'losses': len(losses),
                'win_rate': len(wins) / len(trades_fechados) * 100,
                'resultado_medio': np.mean(resultados),
                'resultado_total': sum(resultados),
                'maior_gain': max(resultados) if resultados else 0,
                'maior_loss': min(resultados) if resultados else 0,
                'sharpe_ratio': np.mean(resultados) / np.std(resultados) if np.std(resultados) > 0 else 0
            }
        else:
            metrics = {'erro': 'Nenhum trade fechado'}
        
        return {
            'signals': signals,
            'trades': trades,
            'metrics': metrics,
            'spread': spread,
            'media_movel': media_movel,
            'banda_superior': banda_superior,
            'banda_inferior': banda_inferior
        }
    
    def plot_strategy(self, results: Dict):
        """
        Plota os resultados da estratégia.
        
        Parameters:
            results: Dicionário retornado pelo backtest
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        
        # Subplot 1: Spread e Bandas
        ax1.plot(results['spread'].index, results['spread'], label='Spread', color='blue', alpha=0.7)
        ax1.plot(results['media_movel'].index, results['media_movel'], label='Média Móvel', color='black', linestyle='--')
        ax1.plot(results['banda_superior'].index, results['banda_superior'], label=f'Banda Superior ({self.n_std}σ)', color='red', linestyle=':')
        ax1.plot(results['banda_inferior'].index, results['banda_inferior'], label=f'Banda Inferior ({self.n_std}σ)', color='green', linestyle=':')
        
        # Marca entradas e saídas
        signals = results['signals']
        entradas_compra = signals[(signals['trade'] == 1) & (signals['posicao'] == 1)]
        entradas_venda = signals[(signals['trade'] == -1) & (signals['posicao'] == -1)]
        saidas = signals[(signals['trade'] != 0) & (signals['posicao'] == 0)]
        
        ax1.scatter(entradas_compra.index, results['spread'][entradas_compra.index], 
                   color='green', marker='^', s=100, label='Compra Spread')
        ax1.scatter(entradas_venda.index, results['spread'][entradas_venda.index], 
                   color='red', marker='v', s=100, label='Venda Spread')
        ax1.scatter(saidas.index, results['spread'][saidas.index], 
                   color='black', marker='x', s=100, label='Saída')
        
        ax1.set_ylabel('Spread (bps)')
        ax1.set_title(f'Pairs Trading: {self.di_long} vs {self.di_short}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Subplot 2: Resultado Acumulado
        if results['trades']:
            trades_df = pd.DataFrame([t for t in results['trades'] if 'resultado_liquido' in t])
            if not trades_df.empty:
                trades_df['resultado_acumulado'] = trades_df['resultado_liquido'].cumsum()
                ax2.plot(trades_df['data_saida'], trades_df['resultado_acumulado'], 
                        marker='o', color='darkblue', linewidth=2)
                ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                ax2.set_ylabel('Resultado Acumulado (pontos)')
                ax2.set_xlabel('Data')
                ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


# Exemplo de uso
if __name__ == "__main__":
    # Carrega dados
    try:
        with open('/mnt/c/Users/guilh/Documents/GitHub/les_juros/futures_v2.pkl', 'rb') as f:
            df = pickle.load(f)
        
        # Exemplo: DI1F25 (venc. jan/25) vs DI1F26 (venc. jan/26)
        strategy = DiPairsTrading(
            di_long='DI1F25',
            di_short='DI1F26',
            window=20,
            n_std=2.0
        )
        
        # Define vencimentos
        venc_long = pd.Timestamp('2025-01-02')
        venc_short = pd.Timestamp('2026-01-02')
        
        # Executa backtest
        results = strategy.backtest(df, venc_long, venc_short)
        
        # Mostra métricas
        print("\nMétricas da Estratégia:")
        for key, value in results['metrics'].items():
            print(f"{key}: {value}")
        
        # Plota resultados
        strategy.plot_strategy(results)
        
    except Exception as e:
        print(f"Erro ao executar estratégia: {e}")