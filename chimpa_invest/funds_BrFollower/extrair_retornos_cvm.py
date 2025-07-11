import pandas as pd
import numpy as np
import os
import zipfile
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Configuração dos diretórios
BASE_DIR = Path("C:/Users/guilh/Documents/GitHub/database/funds_cvm")
OUTPUT_DIR = Path("C:/Users/guilh/Documents/GitHub/database/chimpa")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class ExtractorRetornosCVM:
    def __init__(self, init_date="2021-01", final_date="2024-12", min_shareholder=1):
        self.init_date = init_date
        self.final_date = final_date
        self.min_shareholder = min_shareholder
        self.inf_diario_dir = BASE_DIR / "INF_DIARIO"
        
    def get_business_dates(self):
        """Cria um range de datas úteis para o período"""
        dates = pd.date_range(self.init_date, self.final_date, freq='D')
        # Criar DataFrame com todas as datas para usar como índice
        return pd.DataFrame(index=dates)
    
    def process_monthly_file(self, file_path):
        """Processa um arquivo mensal e retorna dados dos fundos"""
        fundos_data = {}
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                for nome_interno in zip_file.namelist():
                    if nome_interno.endswith('.csv'):
                        with zip_file.open(nome_interno) as f:
                            df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                            
                            required_cols = ['DT_COMPTC', 'CNPJ_FUNDO', 'VL_QUOTA', 'NR_COTST']
                            if all(col in df.columns for col in required_cols):
                                df['DT_COMPTC'] = pd.to_datetime(df['DT_COMPTC'])
                                
                                # Agrupar por CNPJ
                                for cnpj, group in df.groupby('CNPJ_FUNDO'):
                                    fundos_data[cnpj] = group.set_index('DT_COMPTC')[['VL_QUOTA', 'NR_COTST']]
                        break
        except Exception as e:
            print(f"Erro ao processar {file_path.name}: {e}")
            
        return fundos_data
    
    def extract_all_funds(self):
        """Extrai dados de todos os fundos no período"""
        dates = pd.date_range(self.init_date, self.final_date, freq='MS')
        all_funds_data = {}
        
        print("Processando arquivos mensais...")
        for d in tqdm(dates):
            file_name = f'inf_diario_fi_{d.year}{d.month:02d}.csv'
            zip_name = f'inf_diario_fi_{d.year}{d.month:02d}.zip'
            file_path = self.inf_diario_dir / zip_name
            
            if file_path.exists():
                monthly_data = self.process_monthly_file(file_path)
                
                for cnpj, data in monthly_data.items():
                    if cnpj not in all_funds_data:
                        all_funds_data[cnpj] = []
                    all_funds_data[cnpj].append(data)
        
        return all_funds_data
    
    def calculate_returns(self):
        """Calcula retornos normalizados dos fundos"""
        all_funds_data = self.extract_all_funds()
        
        # Criar DataFrame base com datas
        bdates = self.get_business_dates()
        funds_returns = pd.DataFrame(index=bdates.index)
        
        print("Calculando retornos...")
        for cnpj, data_list in tqdm(all_funds_data.items()):
            if data_list:
                # Concatenar todos os dados do fundo
                df_fund = pd.concat(data_list)
                df_fund = df_fund[~df_fund.index.duplicated(keep='first')]
                df_fund = df_fund.sort_index()
                
                # Verificar número médio de cotistas
                avg_shareholders = df_fund['NR_COTST'].mean()
                if avg_shareholders < self.min_shareholder:
                    continue
                
                # Normalizar cotas (dividir pelo valor inicial)
                if len(df_fund) > 0 and df_fund['VL_QUOTA'].iloc[0] > 0:
                    normalized_quota = df_fund['VL_QUOTA'] / df_fund['VL_QUOTA'].iloc[0]
                    
                    # Adicionar ao DataFrame principal
                    funds_returns = pd.merge(
                        funds_returns, 
                        normalized_quota.rename(cnpj), 
                        left_index=True, 
                        right_index=True, 
                        how='outer'
                    )
        
        # Ordenar por data e preencher valores faltantes
        funds_returns = funds_returns.sort_index()
        funds_returns = funds_returns.fillna(method='ffill').fillna(method='bfill')
        
        # Calcular retornos (valor final - 1)
        returns_df = funds_returns - 1
        
        return returns_df
    
    def save_returns(self):
        """Salva os retornos em CSV"""
        returns_df = self.calculate_returns()
        
        if not returns_df.empty:
            # Salvar retornos
            output_file = OUTPUT_DIR / "retornos_fundos_cvm.csv"
            returns_df.to_csv(output_file)
            
            # Calcular estatísticas
            total_returns = returns_df.iloc[-1].sort_values(ascending=False)
            stats = pd.DataFrame({
                'retorno_total': total_returns,
                'retorno_anualizado': (1 + total_returns) ** (12/len(returns_df)) - 1,
                'volatilidade_diaria': returns_df.pct_change().std(),
                'sharpe_ratio': total_returns / returns_df.pct_change().std() / np.sqrt(252),
                'max_drawdown': (returns_df / returns_df.cummax() - 1).min(),
                'qtd_observacoes': returns_df.count()
            })
            
            stats.to_csv(OUTPUT_DIR / "estatisticas_fundos_cvm.csv")
            
            print(f"\nRetornos salvos em: {output_file}")
            print(f"Total de fundos: {len(returns_df.columns)}")
            print(f"Período: {returns_df.index[0].strftime('%Y-%m-%d')} a {returns_df.index[-1].strftime('%Y-%m-%d')}")
            print(f"Retorno médio total: {total_returns.mean():.2%}")
            
            return returns_df
        else:
            print("Nenhum dado processado!")
            return pd.DataFrame()


def main():
    extractor = ExtractorRetornosCVM(
        init_date="2021-01",
        final_date="2024-12",
        min_shareholder=1
    )
    
    returns_df = extractor.save_returns()
    return returns_df


if __name__ == "__main__":
    main()