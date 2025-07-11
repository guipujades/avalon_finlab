import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional
import MetaTrader5 as mt5
from datetime import datetime
import matplotlib.pyplot as plt

import seaborn as sns


class MT5:
    """
    Classe para gerenciar conexoes e operacoes com o MetaTrader 5.
    Fornece metodos para inicializacao, preparacao de simbolos e obtencao de dados historicos.
    """
    
    @staticmethod
    def initialize(login: Optional[int] = None, 
                  server: Optional[str] = None, 
                  key: Optional[str] = None, 
                  user_path: Optional[str] = None) -> None:
        """
        Inicializa a conexao com o MetaTrader 5.

        Parameters:
            login (int, optional): Numero da conta
            server (str, optional): Nome do servidor
            key (str, optional): Senha da conta
            user_path (str, optional): Caminho para o terminal do MetaTrader 5

        Returns:
            None
        """
        if user_path is None:
            if not mt5.initialize(login=login, server=server, password=key):
                print('Inicializacao falhou. Verifique sua conexao.')
                mt5.shutdown()
            else:
                print('MT5 inicializado com sucesso...')
        else:
            if not mt5.initialize(path=user_path, login=login, server=server, password=key):
                print('Inicializacao falhou. Verifique sua conexao.')
                mt5.shutdown()
            else:
                print('MT5 inicializado com sucesso...')
    
    @staticmethod
    def prepare_symbol(symbol: str) -> None:
        """
        Prepara um simbolo para negociacao, verificando sua disponibilidade e visibilidade.

        Parameters:
            symbol (str): Simbolo a ser preparado

        Returns:
            None

        Raises:
            Warning se o simbolo nao for encontrado ou nao estiver visivel
        """
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(symbol, 'not found, can not call order_check()')
            return
        
        if not symbol_info.visible:
            print(symbol, 'is not visible, trying to switch on...')
            if not mt5.symbol_select(symbol, True):
                print('symbol_select() failed, exit', symbol)
                return
    
    @staticmethod
    def get_prices_mt5(symbol: str, n: int, timeframe: int) -> Optional[pd.DataFrame]:
        """
        Importa dados historicos do MT5 para o simbolo escolhido.

        Parameters:
            symbol (str): Simbolo para obter os dados
            n (int): Numero de barras/candles a serem obtidos
            timeframe (int): Timeframe desejado (use as constantes MT5, ex: mt5.TIMEFRAME_D1)

        Returns:
            Optional[pd.DataFrame]: DataFrame com os dados historicos ou None se houver erro
                Colunas retornadas:
                - Abertura
                - Maxima
                - Minima
                - Fechamento
                - Volume

        Example:
            >>> mt5 = MT5()
            >>> df = mt5.get_prices_mt5("PETR4", 100, mt5.TIMEFRAME_D1)
        """
        utc_from = datetime.now()
        
        try:
            rates = mt5.copy_rates_from(symbol, timeframe, utc_from, n)
            rates_frame = pd.DataFrame(rates)
            rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
            rates_frame['time'] = pd.to_datetime(rates_frame['time'], format='%Y-%m-%d')
            rates_frame = rates_frame.set_index('time')
            rates_frame = rates_frame.rename(columns={
                'open': 'Abertura',
                'high': 'Maxima',
                'low': 'Minima',
                'close': 'Fechamento',
                'real_volume': 'Volume'
            })
            
            return rates_frame
            
        except Exception as e:
            print(e)
            print(f'Nao foi possivel pegar os precos de {symbol}')
            return None


class IndicatorsTA:
    """
    Classe para calculo de indicadores tecnicos
    """
    
    def __init__(
        self,
        bb_period: int = 20,
        bb_std_dev: float = 2.0,
        kc_period: int = 10,
        kc_multiplier: float = 1.5,
        vol_period: int = 20,
        vol_std_dev: float = 2.0,
        ma_fast_period: int = 9,
        ma_slow_period: int = 21
    ):
        """
        Inicializa a classe Indicators com os parametros para cada indicador.
        
        Parameters:
            bb_period (int): Periodo para Bandas de Bollinger
            bb_std_dev (float): Desvio padrao para Bandas de Bollinger
            kc_period (int): Periodo para Canal de Keltner
            kc_multiplier (float): Multiplicador para Canal de Keltner
            vol_period (int): Periodo para Bandas de Volume
            vol_std_dev (float): Desvio padrao para Bandas de Volume
            ma_fast_period (int): Periodo para media movel rapida
            ma_slow_period (int): Periodo para media movel lenta
        """
        
        # BB params
        self.bb_period = bb_period
        self.bb_std_dev = bb_std_dev
        
        # Keltner params
        self.kc_period = kc_period
        self.kc_multiplier = kc_multiplier
        
        # BBV params
        self.vol_period = vol_period
        self.vol_std_dev = vol_std_dev
        
        # MA params
        self.ma_fast_period = ma_fast_period
        self.ma_slow_period = ma_slow_period
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcula as Bandas de Bollinger usando os parametros da instancia
        """
        close = df['Fechamento']
        middle_band = close.rolling(window=self.bb_period).mean()
        std = close.rolling(window=self.bb_period).std()
        
        upper_band = middle_band + (self.bb_std_dev * std)
        lower_band = middle_band - (self.bb_std_dev * std)
        
        return upper_band, lower_band
    
    def calculate_keltner_channel(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcula o Canal de Keltner usando os parametros da instancia
        """
        typical_price = (df['Maxima'] + df['Minima'] + df['Fechamento']) / 3
        center_line = typical_price.rolling(window=self.kc_period).mean()
        range_tr = df['Maxima'] - df['Minima']
        range_ma = range_tr.rolling(window=self.kc_period).mean()
        
        upper_channel = center_line + (self.kc_multiplier * range_ma)
        lower_channel = center_line - (self.kc_multiplier * range_ma)
        
        return upper_channel, lower_channel
    
    def calculate_volume_bands(self, volume: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcula as Bandas de Bollinger para o volume usando os parametros da instancia
        """
        middle_band = volume.rolling(window=self.vol_period).mean()
        std = volume.rolling(window=self.vol_period).std()
        
        upper_band = middle_band + (self.vol_std_dev * std)
        lower_band = middle_band - (self.vol_std_dev * std)
        
        return upper_band, lower_band
    
    def calculate_sma(self, series: pd.Series, period: int) -> pd.Series:
        """
        Calcula a Media Movel Simples
        
        Parameters:
            series (pd.Series): Serie temporal para calculo
            period (int): Periodo da media movel
            
        Returns:
            pd.Series: Media movel calculada
        """
        return series.rolling(window=period).mean()
    
    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """
        Calcula a Media Movel Exponencial
        
        Parameters:
            series (pd.Series): Serie temporal para calculo
            period (int): Periodo da media movel
            
        Returns:
            pd.Series: Media movel calculada
        """
        return series.ewm(span=period, adjust=False).mean()
    
    def calculate_moving_averages(self, df: pd.DataFrame, use_ema: bool = False) -> Tuple[pd.Series, pd.Series]:
        """
        Calcula as medias moveis rapida e lenta
        
        Parameters:
            df (pd.DataFrame): DataFrame com os dados
            use_ema (bool): Se True usa EMA, se False usa SMA
            
        Returns:
            Tuple[pd.Series, pd.Series]: Media rapida e media lenta
        """
        if use_ema:
            fast_ma = self.calculate_ema(df['Fechamento'], self.ma_fast_period)
            slow_ma = self.calculate_ema(df['Fechamento'], self.ma_slow_period)
        else:
            fast_ma = self.calculate_sma(df['Fechamento'], self.ma_fast_period)
            slow_ma = self.calculate_sma(df['Fechamento'], self.ma_slow_period)
            
        return fast_ma, slow_ma


class Strategies:
    
    @staticmethod
    def strategy_bbKeltner_marcius(df_h, df_nmin) -> List:
        
        ind = IndicatorsTA()
        bb_upper_h, bb_lower_h = ind.calculate_bollinger_bands(df_h)
        kc_upper_h, kc_lower_h = ind.calculate_keltner_channel(df_h)
    
        bb_upper_l, bb_lower_l = ind.calculate_bollinger_bands(df_nmin)
        vol_upper, vol_lower = ind.calculate_volume_bands(df_nmin['Volume'])
        
        ops = []
        n_size = 5
        check_for_signal = 60
        next_valid_date = None  # Data a partir da qual podemos operar novamente
        
        for i in range(n_size, len(df_h)-1):
            # Se tiver uma data de break e ainda não chegamos nela, pula
            if next_valid_date is not None and df_h.index[i] < next_valid_date:
                continue
                
            # Se chegamos na data do break, podemos resetar
            if next_valid_date is not None and df_h.index[i] >= next_valid_date:
                next_valid_date = None
            
            # Verifica se as bandas de Bollinger entraram no canal de Keltner
            if (bb_upper_h[i] <= kc_upper_h[i] and bb_lower_h[i] >= kc_lower_h[i]):
                
                # Encontra max e min dos ultimos 5 candles
                range_high = df_h['Maxima'][i-n_size:i].max()
                range_low = df_h['Minima'][i-n_size:i].min()
                range_size = range_high - range_low
                
                # Analise de periodos
                date_ref = df_h.index[i]
                next_date = df_h.index[i + check_for_signal] if i + (check_for_signal+1) < len(df_h) else None
                
                # Filtra dados do timeframe menor
                if next_date:
                    df_nmin_filter = df_nmin[
                        (df_nmin.index >= date_ref) &
                        (df_nmin.index < next_date)
                    ]
                else:
                    df_nmin_filter = df_nmin[df_nmin.index >= date_ref]
                
                for idx in df_nmin_filter.index:
                    current_candle = df_nmin_filter.loc[idx]
                    high_volume = current_candle['Volume_Financeiro'] > vol_upper[idx]
        
                    if high_volume:
                        # Verifica rompimento de máxima
                        if current_candle['Fechamento'] > range_high:
                            movement = current_candle['Fechamento'] - range_high
                            if ((movement <= 0.7 * range_size) and 
                                (current_candle['Fechamento'] > current_candle['Abertura'] + (0.2 * range_size)) and 
                                (current_candle['Fechamento'] > (0.5 * (current_candle['Maxima'] + current_candle['Minima'])))):
                                ops.append({
                                    'data': idx,
                                    'tipo': 'compra',
                                    'entrada': current_candle['Fechamento'],
                                    'stop': current_candle['Minima'],
                                    'alvo': df_h.loc[i, 'Fechamento'] + range_size
                                })
                            else:
                                next_valid_date = idx  # Próxima operação só após esta data
                                break
                        
                        # Verifica rompimento de mínima
                        elif current_candle['Fechamento'] < range_low:
                            movement = range_low - current_candle['Fechamento']
                            if ((movement <= 0.7 * range_size) and
                                (current_candle['Fechamento'] < current_candle['Abertura'] - (0.2 * range_size)) and 
                                (current_candle['Fechamento'] < (0.5 * (current_candle['Maxima'] + current_candle['Minima'])))):
                                ops.append({
                                    'data': idx,
                                    'tipo': 'venda',
                                    'entrada': current_candle['Fechamento'],
                                    'stop': current_candle['Maxima'],
                                    'alvo': df_h.loc[i, 'Fechamento'] - range_size
                                })
                            else:
                                next_valid_date = idx  # Próxima operação só após esta data
                                break
                            
        return ops


class Backtester:
    
    @staticmethod
    def run_backtest(df_nmin: pd.DataFrame, operations: List[dict], is_dol: bool = False) -> List[dict]:
        """
        Executa backtest das operacoes considerando apenas uma posicao por vez
        
        Parameters:
            df_nmin: DataFrame com dados intradiarios
            operations: Lista com operacoes identificadas
                dict com keys: data, tipo, entrada, stop, alvo
            is_dol: Se True, calcula resultado para dolar (0.5 pts = R$5.00)
        
        Returns:
            Lista com as operacoes executadas e seus resultados
        """
        trades = []  # lista para armazenar trades executadas
        trade_atual = None  # controle de trade aberta
        
        # Constantes para calculo do dolar
        CUSTO_OPERACIONAL_DOL = 2.50  # custo por operacao (C&V)
        VALOR_PONTO_DOL = 10.00
        
        # Ordena operacoes por data
        operations = sorted(operations, key=lambda x: x['data'])
        
        # Itera sobre as operacoes identificadas
        for op in operations:
            # Se existe trade aberta, nao opera
            if trade_atual is not None and trade_atual['status'] == 'Aberta':
                continue
            
            # Cria nova trade
            trade_atual = {
                'data_entrada': op['data'],
                'tipo': op['tipo'],
                'entrada': op['entrada'],
                'stop': op['stop'],
                'alvo': op['alvo'],
                'status': 'Aberta',
                'data_saida': None,
                'saida': None,
                'resultado': None,
                'resultado_perc': None,
                'resultado_real': None  # resultado em R$ para dolar
            }
            trades.append(trade_atual)
            
            # Filtra dados posteriores a entrada
            df_pos_entrada = df_nmin[df_nmin.index > op['data']]
            
            for idx, row in df_pos_entrada.iterrows():
                hit_stop = False
                hit_target = False
                
                if op['tipo'] == 'compra':
                    # Verifica stop
                    if row['Minima'] <= trade_atual['stop']:
                        trade_atual['saida'] = trade_atual['stop']
                        trade_atual['status'] = 'StopLoss'
                        hit_stop = True
                    # Verifica alvo
                    elif row['Maxima'] >= trade_atual['alvo']:
                        trade_atual['saida'] = trade_atual['alvo']
                        trade_atual['status'] = 'Alvo'
                        hit_target = True
                
                else:  # venda
                    # Verifica stop
                    if row['Maxima'] >= trade_atual['stop']:
                        trade_atual['saida'] = trade_atual['stop']
                        trade_atual['status'] = 'StopLoss'
                        hit_stop = True
                    # Verifica alvo
                    elif row['Minima'] <= trade_atual['alvo']:
                        trade_atual['saida'] = trade_atual['alvo']
                        trade_atual['status'] = 'Alvo'
                        hit_target = True
                
                if hit_stop or hit_target:
                    trade_atual['data_saida'] = idx
                    # Calcula resultado
                    if trade_atual['tipo'] == 'compra':
                        trade_atual['resultado'] = trade_atual['saida'] - trade_atual['entrada']
                    else:
                        trade_atual['resultado'] = trade_atual['entrada'] - trade_atual['saida']
                        
                    trade_atual['resultado_perc'] = (trade_atual['resultado'] / trade_atual['entrada']) * 100
                    
                    # Calculo para dolar
                    if is_dol:
                        resultado_pontos = abs(trade_atual['resultado']) * VALOR_PONTO_DOL
                        trade_atual['resultado_real'] = (
                            resultado_pontos * np.sign(trade_atual['resultado']) - 
                            (CUSTO_OPERACIONAL_DOL)
                        )
                    
                    trade_atual = None  # libera para proxima operacao
                    break
        
        return trades
    
    @staticmethod
    def calculate_metrics(trades: List[dict], is_dol: bool = False) -> dict:
        """
        Calcula metricas do backtest
        
        Parameters:
            trades: Lista com as operacoes executadas
            is_dol: Se True, usa resultado_real para metricas
        
        Returns:
            Dicionario com as metricas calculadas
        """
        # Filtra apenas trades finalizadas
        trades_finalizadas = [t for t in trades if t['status'] != 'Aberta']
        
        if not trades_finalizadas:
            return {"error": "Nenhuma operacao finalizada"}
        
        # Separa resultados
        if is_dol:
            results = [t['resultado_real'] for t in trades_finalizadas]
            resultado_label = "R$"
        else:
            results = [t['resultado'] for t in trades_finalizadas]
            resultado_label = "pts"
        
        wins = len([r for r in results if r > 0])
        losses = len([r for r in results if r < 0])
        
        # Calcula metricas
        metrics = {
            "total_trades": len(trades),
            "trades_finalizadas": len(trades_finalizadas),
            "trades_abertas": len(trades) - len(trades_finalizadas),
            "trades_win": wins,
            "trades_loss": losses,
            "taxa_acerto": (wins / len(results)) * 100,
            f"resultado_medio_{resultado_label}": np.mean(results),
            "resultado_medio_perc": np.mean([t['resultado_perc'] for t in trades_finalizadas]),
            f"desvio_padrao_{resultado_label}": np.std(results),
            f"maior_gain_{resultado_label}": max(results),
            f"maior_loss_{resultado_label}": min(results),
            f"resultado_acumulado_{resultado_label}": sum(results)
        }
        
        # Calcula fator lucro
        sum_wins = sum([r for r in results if r > 0])
        sum_losses = sum([r for r in results if r < 0])
        metrics["fator_lucro"] = abs(sum_wins / sum_losses) if sum_losses != 0 else float('inf')
        
        return metrics
    
    @staticmethod
    def create_trades_df(trades: List[dict]) -> pd.DataFrame:
        return pd.DataFrame(trades)


class Visual:
    
    def plot_results(df):

        plt.style.use('seaborn')
        sns.set_palette("deep")
        
        df['resultado_acumulado'] = df['resultado_real'].cumsum()
        
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['resultado_acumulado'], linewidth=2, marker='o')
        plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        plt.ylabel('Pontos Acumulados', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=0)

        valor_final = df['resultado_acumulado'].iloc[-1]
        plt.text(len(df)-1, valor_final, f' {valor_final:.1f}', 
                 verticalalignment='bottom')
        plt.tight_layout()
        
        plt.show()


