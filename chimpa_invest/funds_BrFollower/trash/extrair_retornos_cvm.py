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
    def __init__(self, periodo_inicial="2020-01", periodo_final="2024-12"):
        self.periodo_inicial = periodo_inicial
        self.periodo_final = periodo_final
        self.inf_diario_dir = BASE_DIR / "INF_DIARIO"
        self.retornos_fundos = {}
        
    def _extrair_periodo_arquivo(self, nome_arquivo):
        periodo = nome_arquivo.replace("inf_diario_fi_", "").replace(".zip", "")
        if len(periodo) == 6:
            return f"{periodo[:4]}-{periodo[4:6]}"
        return periodo
    
    def processar_arquivo_zip(self, arquivo_path):
        fundos_periodo = {}
        
        try:
            with zipfile.ZipFile(arquivo_path, 'r') as zip_file:
                for nome_interno in zip_file.namelist():
                    if nome_interno.endswith('.csv'):
                        with zip_file.open(nome_interno) as f:
                            df = pd.read_csv(f, sep=';', encoding='ISO-8859-1')
                            
                            colunas_necessarias = ['DT_COMPTC', 'CNPJ_FUNDO', 'VL_QUOTA']
                            if all(col in df.columns for col in colunas_necessarias):
                                df['DT_COMPTC'] = pd.to_datetime(df['DT_COMPTC'])
                                
                                for cnpj in df['CNPJ_FUNDO'].unique():
                                    df_fundo = df[df['CNPJ_FUNDO'] == cnpj][['DT_COMPTC', 'VL_QUOTA']].copy()
                                    df_fundo = df_fundo.sort_values('DT_COMPTC')
                                    df_fundo.set_index('DT_COMPTC', inplace=True)
                                    
                                    if len(df_fundo) > 0 and df_fundo['VL_QUOTA'].notna().any():
                                        fundos_periodo[cnpj] = df_fundo
        except:
            pass
            
        return fundos_periodo
    
    def extrair_retornos_todos_fundos(self):
        periodo_inicial_dt = datetime.strptime(self.periodo_inicial, "%Y-%m")
        periodo_final_dt = datetime.strptime(self.periodo_final, "%Y-%m")
        
        arquivos_processar = []
        
        for arquivo in sorted(os.listdir(self.inf_diario_dir)):
            if arquivo.startswith("inf_diario_fi_") and arquivo.endswith(".zip"):
                periodo_str = self._extrair_periodo_arquivo(arquivo)
                try:
                    periodo_dt = datetime.strptime(periodo_str, "%Y-%m")
                    if periodo_inicial_dt <= periodo_dt <= periodo_final_dt:
                        arquivos_processar.append((arquivo, self.inf_diario_dir / arquivo))
                except:
                    continue
        
        series_cotas = {}
        
        for nome_arquivo, arquivo_path in tqdm(arquivos_processar, desc="Processando arquivos"):
            fundos_periodo = self.processar_arquivo_zip(arquivo_path)
            
            for cnpj, df_cotas in fundos_periodo.items():
                if cnpj not in series_cotas:
                    series_cotas[cnpj] = []
                series_cotas[cnpj].append(df_cotas)
        
        for cnpj, lista_dfs in tqdm(series_cotas.items(), desc="Consolidando fundos"):
            if lista_dfs:
                df_completo = pd.concat(lista_dfs)
                df_completo = df_completo[~df_completo.index.duplicated(keep='first')]
                df_completo = df_completo.sort_index()
                
                if len(df_completo) >= 20:
                    df_completo['retorno'] = df_completo['VL_QUOTA'].pct_change()
                    df_completo = df_completo.dropna(subset=['retorno'])
                    
                    if len(df_completo) >= 20:
                        self.retornos_fundos[cnpj] = df_completo
    
    def calcular_retornos_mensais(self):
        retornos_mensais = {}
        
        for cnpj, df in tqdm(self.retornos_fundos.items(), desc="Calculando retornos mensais"):
            if 'retorno' in df.columns:
                retorno_mensal = df['retorno'].resample('M').apply(lambda x: (1 + x).prod() - 1)
                
                if len(retorno_mensal) >= 12:
                    retornos_mensais[cnpj] = retorno_mensal
        
        if retornos_mensais:
            df_retornos = pd.DataFrame(retornos_mensais)
            min_observacoes = len(df_retornos) * 0.5
            df_retornos = df_retornos.dropna(thresh=min_observacoes, axis=1)
            return df_retornos
        
        return pd.DataFrame()
    
    def salvar_retornos_consolidados(self):
        df_retornos = self.calcular_retornos_mensais()
        
        if not df_retornos.empty:
            output_file = OUTPUT_DIR / "retornos_fundos_cvm.csv"
            df_retornos.to_csv(output_file)
            
            # Criar também um arquivo com estatísticas básicas
            stats = pd.DataFrame({
                'retorno_medio': df_retornos.mean(),
                'volatilidade': df_retornos.std(),
                'sharpe_ratio': df_retornos.mean() / df_retornos.std() * np.sqrt(12),
                'min_retorno': df_retornos.min(),
                'max_retorno': df_retornos.max(),
                'qtd_observacoes': df_retornos.count()
            })
            stats.to_csv(OUTPUT_DIR / "estatisticas_fundos_cvm.csv")
            
            return df_retornos
        
        return pd.DataFrame()


def main():
    extractor = ExtractorRetornosCVM(
        periodo_inicial="2020-01",
        periodo_final="2024-12"
    )
    
    extractor.extrair_retornos_todos_fundos()
    df_retornos = extractor.salvar_retornos_consolidados()
    
    if not df_retornos.empty:
        print(f"\nRetornos salvos em: {OUTPUT_DIR / 'retornos_fundos_cvm.csv'}")
        print(f"Total de fundos: {len(df_retornos.columns)}")
        print(f"Período: {df_retornos.index[0].strftime('%Y-%m')} a {df_retornos.index[-1].strftime('%Y-%m')}")


if __name__ == "__main__":
    main()