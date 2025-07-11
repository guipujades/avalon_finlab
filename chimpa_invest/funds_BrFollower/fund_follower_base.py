import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('../sherpa')

from pathlib import Path

class FundFollower:
    def __init__(self, cnpj_target: str, nome_target: str = "Fundo Alvo"):
        """
        Inicializa o sistema de fund follower
        
        Args:
            cnpj_target: CNPJ do fundo alvo a ser seguido
            nome_target: Nome do fundo alvo
        """
        self.cnpj_target = cnpj_target
        self.nome_target = nome_target
        self.returns_target = None
        self.returns_universe = {}
        self.prices_universe = {}
        self.beta_target = None
        self.weights_optimal = None
        self.tracking_error = None
        self.in_sample_period = None
        self.out_sample_period = None
        
    def load_target_returns(self, file_path: str = None):
        """Carrega os retornos do fundo alvo"""
        if file_path:
            if file_path.endswith('.csv'):
                self.returns_target = pd.read_csv(file_path, index_col=0, parse_dates=True)
            elif file_path.endswith('.pkl'):
                self.returns_target = pd.read_pickle(file_path)
        else:
            cnpj_limpo = self.cnpj_target.replace('.', '').replace('/', '').replace('-', '')
            path_csv = f'dados/{cnpj_limpo}/csv/retornos_mensais.csv'
            if os.path.exists(path_csv):
                df = pd.read_csv(path_csv)
                if 'periodo' in df.columns and 'retorno_diario' in df.columns:
                    df['periodo'] = pd.to_datetime(df['periodo'])
                    df = df.set_index('periodo')['retorno_diario']
                    self.returns_target = df
                else:
                    raise ValueError("Formato de dados não reconhecido")
            else:
                raise FileNotFoundError(f"Arquivo de retornos não encontrado: {path_csv}")
    
    def load_universe_returns(self, universe_data: Union[str, pd.DataFrame, Dict]):
        """
        Carrega retornos do universo de fundos/ativos disponíveis
        
        Args:
            universe_data: Caminho do arquivo, DataFrame ou dicionário com retornos
        """
        if isinstance(universe_data, str):
            if universe_data.endswith('.csv'):
                self.returns_universe = pd.read_csv(universe_data, index_col=0, parse_dates=True)
            elif universe_data.endswith('.pkl'):
                self.returns_universe = pd.read_pickle(universe_data)
        elif isinstance(universe_data, pd.DataFrame):
            self.returns_universe = universe_data
        elif isinstance(universe_data, dict):
            self.returns_universe = pd.DataFrame(universe_data)
        else:
            raise ValueError("Formato de dados não suportado")
    
    def split_data(self, train_ratio: float = 0.4):
        """
        Divide os dados em in-sample (treinamento) e out-of-sample (teste)
        
        Args:
            train_ratio: Proporção dos dados para treinamento
        """
        if self.returns_target is None:
            raise ValueError("Retornos do fundo alvo não carregados")
        
        n_periods = len(self.returns_target)
        n_train = int(n_periods * train_ratio)
        
        split_date = self.returns_target.index[n_train]
        
        self.in_sample_period = (self.returns_target.index[0], split_date)
        self.out_sample_period = (split_date, self.returns_target.index[-1])
        
        print(f"Período in-sample: {self.in_sample_period[0].strftime('%Y-%m')} a {self.in_sample_period[1].strftime('%Y-%m')}")
        print(f"Período out-of-sample: {self.out_sample_period[0].strftime('%Y-%m')} a {self.out_sample_period[1].strftime('%Y-%m')}")
    
    def calculate_beta(self, market_returns: pd.Series = None):
        """
        Calcula o beta do fundo alvo em relação ao mercado
        
        Args:
            market_returns: Série de retornos do mercado (Ibovespa, por exemplo)
        """
        if market_returns is None:
            print("Aviso: Sem retornos de mercado, beta não será calculado")
            return
        
        returns_target_train = self.returns_target[self.in_sample_period[0]:self.in_sample_period[1]]
        market_returns_train = market_returns[self.in_sample_period[0]:self.in_sample_period[1]]
        
        aligned_data = pd.DataFrame({
            'target': returns_target_train,
            'market': market_returns_train
        }).dropna()
        
        if len(aligned_data) < 12:
            print("Aviso: Poucos dados para cálculo confiável do beta")
            return
        
        covariance = aligned_data.cov().iloc[0, 1]
        market_variance = aligned_data['market'].var()
        
        self.beta_target = covariance / market_variance
        print(f"Beta do fundo alvo: {self.beta_target:.3f}")
    
    def calculate_tracking_error(self, weights: np.ndarray, returns_universe: pd.DataFrame, 
                               returns_target: pd.Series) -> float:
        """
        Calcula o tracking error entre a carteira replicante e o fundo alvo
        
        Args:
            weights: Pesos dos ativos na carteira replicante
            returns_universe: DataFrame com retornos dos ativos disponíveis
            returns_target: Série com retornos do fundo alvo
            
        Returns:
            Tracking error (desvio padrão das diferenças de retorno)
        """
        portfolio_returns = (returns_universe * weights).sum(axis=1)
        
        diff_returns = portfolio_returns - returns_target
        
        tracking_error = diff_returns.std() * np.sqrt(12)
        
        return tracking_error
    
    def optimize_weights_minimum_tracking_error(self):
        """
        Otimiza os pesos para minimizar o tracking error
        """
        if self.returns_universe.empty:
            raise ValueError("Universo de retornos não carregado")
        
        returns_target_train = self.returns_target[self.in_sample_period[0]:self.in_sample_period[1]]
        returns_universe_train = self.returns_universe[self.in_sample_period[0]:self.in_sample_period[1]]
        
        aligned_data = pd.concat([returns_target_train, returns_universe_train], axis=1).dropna()
        returns_target_aligned = aligned_data.iloc[:, 0]
        returns_universe_aligned = aligned_data.iloc[:, 1:]
        
        n_assets = returns_universe_aligned.shape[1]
        
        def objective(weights):
            return self.calculate_tracking_error(weights, returns_universe_aligned, returns_target_aligned)
        
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
        ]
        
        bounds = [(0, 1) for _ in range(n_assets)]
        
        initial_weights = np.ones(n_assets) / n_assets
        
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if result.success:
            self.weights_optimal = result.x
            self.tracking_error = result.fun
            print(f"\nOtimização concluída com sucesso!")
            print(f"Tracking Error (anualizado): {self.tracking_error:.2%}")
            
            print("\nPesos otimizados:")
            for i, (asset, weight) in enumerate(zip(returns_universe_aligned.columns, self.weights_optimal)):
                if weight > 0.01:
                    print(f"{asset}: {weight:.2%}")
        else:
            print(f"Otimização falhou: {result.message}")
    
    def benchmark_beta_matching(self, betas_universe: Dict[str, float]):
        """
        Versão benchmark: seleciona ativos baseado apenas em matching de beta
        
        Args:
            betas_universe: Dicionário com betas dos ativos disponíveis
        """
        if self.beta_target is None:
            print("Beta do fundo alvo não calculado. Usando abordagem alternativa.")
            return
        
        beta_diffs = {asset: abs(beta - self.beta_target) for asset, beta in betas_universe.items()}
        
        sorted_assets = sorted(beta_diffs.items(), key=lambda x: x[1])
        
        n_assets = min(5, len(sorted_assets))
        selected_assets = [asset for asset, _ in sorted_assets[:n_assets]]
        
        weights_benchmark = np.zeros(len(self.returns_universe.columns))
        for i, asset in enumerate(self.returns_universe.columns):
            if asset in selected_assets:
                weights_benchmark[i] = 1 / n_assets
        
        print(f"\nBenchmark (Beta Matching):")
        print(f"Ativos selecionados: {selected_assets}")
        
        self.weights_benchmark = weights_benchmark
    
    def evaluate_out_of_sample(self):
        """
        Avalia o desempenho out-of-sample
        """
        if self.weights_optimal is None:
            print("Pesos otimizados não disponíveis")
            return
        
        returns_target_test = self.returns_target[self.out_sample_period[0]:self.out_sample_period[1]]
        returns_universe_test = self.returns_universe[self.out_sample_period[0]:self.out_sample_period[1]]
        
        aligned_data = pd.concat([returns_target_test, returns_universe_test], axis=1).dropna()
        returns_target_aligned = aligned_data.iloc[:, 0]
        returns_universe_aligned = aligned_data.iloc[:, 1:]
        
        portfolio_returns = (returns_universe_aligned * self.weights_optimal).sum(axis=1)
        
        tracking_error_oos = self.calculate_tracking_error(
            self.weights_optimal, 
            returns_universe_aligned, 
            returns_target_aligned
        )
        
        correlation = portfolio_returns.corr(returns_target_aligned)
        
        target_cumulative = (1 + returns_target_aligned).cumprod()
        portfolio_cumulative = (1 + portfolio_returns).cumprod()
        
        print(f"\nDesempenho Out-of-Sample:")
        print(f"Tracking Error: {tracking_error_oos:.2%}")
        print(f"Correlação: {correlation:.3f}")
        print(f"Retorno acumulado - Fundo Alvo: {(target_cumulative.iloc[-1] - 1):.2%}")
        print(f"Retorno acumulado - Portfolio Replicante: {(portfolio_cumulative.iloc[-1] - 1):.2%}")
        
        self._plot_comparison(target_cumulative, portfolio_cumulative)
    
    def _plot_comparison(self, target_cumulative: pd.Series, portfolio_cumulative: pd.Series):
        """Plota comparação entre fundo alvo e portfolio replicante"""
        plt.figure(figsize=(12, 6))
        
        plt.plot(target_cumulative.index, target_cumulative.values, 
                label=f'{self.nome_target} (Alvo)', linewidth=2)
        plt.plot(portfolio_cumulative.index, portfolio_cumulative.values, 
                label='Portfolio Replicante', linewidth=2, linestyle='--')
        
        plt.title('Comparação: Fundo Alvo vs Portfolio Replicante (Out-of-Sample)')
        plt.xlabel('Data')
        plt.ylabel('Retorno Acumulado')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('fund_follower_comparison.png', dpi=300)
        plt.show()
    
    def save_results(self, output_dir: str = 'resultados_fund_follower'):
        """Salva os resultados da análise"""
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            'cnpj_target': self.cnpj_target,
            'nome_target': self.nome_target,
            'beta_target': self.beta_target,
            'tracking_error': self.tracking_error,
            'in_sample_period': self.in_sample_period,
            'out_sample_period': self.out_sample_period,
            'weights_optimal': self.weights_optimal,
            'assets': list(self.returns_universe.columns) if not self.returns_universe.empty else []
        }
        
        pd.DataFrame([results]).to_csv(f'{output_dir}/fund_follower_results.csv', index=False)
        
        if self.weights_optimal is not None:
            weights_df = pd.DataFrame({
                'Asset': self.returns_universe.columns,
                'Weight': self.weights_optimal
            })
            weights_df = weights_df[weights_df['Weight'] > 0.01].sort_values('Weight', ascending=False)
            weights_df.to_csv(f'{output_dir}/optimal_weights.csv', index=False)
        
        print(f"\nResultados salvos em: {output_dir}/")


def main():
    """Exemplo de uso do FundFollower"""
    
    cnpj_kokorikus = "38.351.476/0001-40"
    
    follower = FundFollower(cnpj_kokorikus, "KOKORIKUS FI AÇÕES")
    
    print("1. Carregando retornos do fundo alvo...")
    follower.load_target_returns()
    
    print("\n2. Dividindo dados em in-sample e out-of-sample...")
    follower.split_data(train_ratio=0.4)
    
    print("\n3. Para completar a análise, você precisa:")
    print("   - Carregar retornos do universo de fundos disponíveis")
    print("   - Calcular beta (opcional, para benchmark)")
    print("   - Otimizar pesos para minimizar tracking error")
    print("   - Avaliar desempenho out-of-sample")


if __name__ == "__main__":
    main()