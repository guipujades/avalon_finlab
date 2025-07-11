import pandas as pd
import numpy as np
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
import pickle
from typing import Dict, List, Tuple
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

home = Path.home()
BASE_DIR = Path(home, 'Documents', 'GitHub', 'sherpa', 'database')

class ExtractorRetornosFundos:
    def __init__(self, periodo_inicial: str = "2020-01", periodo_final: str = "2024-08"):
        """
        Extrai retornos de todos os fundos disponíveis
        
        Args:
            periodo_inicial: Período inicial (YYYY-MM)
            periodo_final: Período final (YYYY-MM)
        """
        self.periodo_inicial = periodo_inicial
        self.periodo_final = periodo_final
        self.inf_diario_dir = os.path.join(BASE_DIR, "INF_DIARIO")
        self.retornos_fundos = {}
        self.info_fundos = {}
        
    def _extrair_periodo_arquivo(self, nome_arquivo: str) -> str:
        """Extrai o período do nome do arquivo"""
        periodo = nome_arquivo.replace("inf_diario_fi_", "").replace(".zip", "")
        if len(periodo) == 6:
            return f"{periodo[:4]}-{periodo[4:6]}"
        return periodo
    
    def processar_arquivo_zip(self, arquivo_path: str) -> Dict[str, pd.DataFrame]:
        """
        Processa um arquivo zip de informe diário
        
        Returns:
            Dicionário com CNPJ como chave e DataFrame de cotas como valor
        """
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
                                        
                                        if cnpj not in self.info_fundos and 'DENOM_SOCIAL' in df.columns:
                                            nome = df[df['CNPJ_FUNDO'] == cnpj]['DENOM_SOCIAL'].iloc[0]
                                            self.info_fundos[cnpj] = {'nome': nome}
                                            
        except Exception as e:
            print(f"Erro ao processar {arquivo_path}: {e}")
            
        return fundos_periodo
    
    def extrair_retornos_todos_fundos(self):
        """Extrai retornos de todos os fundos no período especificado"""
        print(f"Extraindo retornos de {self.periodo_inicial} a {self.periodo_final}")
        print(f"Diretório INF_DIARIO: {self.inf_diario_dir}")
        
        periodo_inicial_dt = datetime.strptime(self.periodo_inicial, "%Y-%m")
        periodo_final_dt = datetime.strptime(self.periodo_final, "%Y-%m")
        
        arquivos_processar = []
        
        for arquivo in sorted(os.listdir(self.inf_diario_dir)):
            if arquivo.startswith("inf_diario_fi_") and arquivo.endswith(".zip"):
                periodo_str = self._extrair_periodo_arquivo(arquivo)
                try:
                    periodo_dt = datetime.strptime(periodo_str, "%Y-%m")
                    if periodo_inicial_dt <= periodo_dt <= periodo_final_dt:
                        arquivos_processar.append((arquivo, os.path.join(self.inf_diario_dir, arquivo)))
                except:
                    continue
        
        print(f"Total de arquivos para processar: {len(arquivos_processar)}")
        
        series_cotas = {}
        
        print("\nProcessando arquivos...")
        for nome_arquivo, arquivo_path in tqdm(arquivos_processar, desc="Arquivos processados"):
            fundos_periodo = self.processar_arquivo_zip(arquivo_path)
            
            for cnpj, df_cotas in fundos_periodo.items():
                if cnpj not in series_cotas:
                    series_cotas[cnpj] = []
                series_cotas[cnpj].append(df_cotas)
        
        print("\nConsolidando séries temporais...")
        
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
        
        print(f"\nTotal de fundos com dados suficientes: {len(self.retornos_fundos)}")
    
    def calcular_retornos_mensais(self) -> pd.DataFrame:
        """
        Calcula retornos mensais para todos os fundos
        
        Returns:
            DataFrame com retornos mensais (fundos nas colunas)
        """
        print("\nCalculando retornos mensais...")
        retornos_mensais = {}
        
        for cnpj, df in tqdm(self.retornos_fundos.items(), desc="Calculando retornos"):
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
    
    def filtrar_fundos_liquidos(self, min_pl: float = 10_000_000) -> List[str]:
        """
        Filtra fundos com patrimônio líquido mínimo
        
        Args:
            min_pl: Patrimônio líquido mínimo
            
        Returns:
            Lista de CNPJs dos fundos que atendem ao critério
        """
        fundos_liquidos = []
        
        print(f"\nFiltrando fundos com PL mínimo de R$ {min_pl:,.0f}")
        
        return list(self.retornos_fundos.keys())
    
    def salvar_dados(self, output_dir: str = "dados_universo"):
        """Salva os dados extraídos"""
        os.makedirs(output_dir, exist_ok=True)
        
        df_retornos = self.calcular_retornos_mensais()
        
        if not df_retornos.empty:
            df_retornos.to_csv(f"{output_dir}/retornos_mensais_universo.csv")
            df_retornos.to_pickle(f"{output_dir}/retornos_mensais_universo.pkl")
            
            print(f"\nDados salvos em {output_dir}/")
            print(f"Total de fundos: {len(df_retornos.columns)}")
            print(f"Período: {df_retornos.index[0].strftime('%Y-%m')} a {df_retornos.index[-1].strftime('%Y-%m')}")
            
            info_df = pd.DataFrame.from_dict(self.info_fundos, orient='index')
            info_df.index.name = 'cnpj'
            info_df.to_csv(f"{output_dir}/info_fundos.csv")
            
            with open(f"{output_dir}/retornos_completos.pkl", 'wb') as f:
                pickle.dump(self.retornos_fundos, f)
        else:
            print("Nenhum dado para salvar!")
        
        return df_retornos


def extrair_amostra_pequena():
    """Extrai uma amostra pequena para testes rápidos"""
    print("Extraindo amostra pequena de fundos...")
    
    extractor = ExtractorRetornosFundos(
        periodo_inicial="2022-01",
        periodo_final="2024-08"
    )
    
    extractor.extrair_retornos_todos_fundos()
    
    df_retornos = extractor.calcular_retornos_mensais()
    
    if not df_retornos.empty:
        top_fundos = df_retornos.columns[:100]
        df_amostra = df_retornos[top_fundos]
        
        df_amostra.to_csv("dados_universo/retornos_amostra_100fundos.csv")
        print(f"Amostra salva com {len(df_amostra.columns)} fundos")
        
        return df_amostra
    
    return pd.DataFrame()


def main():
    """Executa a extração completa"""
    print("="*60)
    print("EXTRAÇÃO DE RETORNOS DO UNIVERSO DE FUNDOS")
    print("="*60)
    
    extractor = ExtractorRetornosFundos(
        periodo_inicial="2020-01",
        periodo_final="2024-08"
    )
    
    extractor.extrair_retornos_todos_fundos()
    
    df_retornos = extractor.salvar_dados()
    
    if not df_retornos.empty:
        print("\nEstatísticas do universo:")
        print(f"Retorno médio mensal: {df_retornos.mean().mean():.2%}")
        print(f"Volatilidade média mensal: {df_retornos.std().mean():.2%}")
        print(f"Fundos com retorno positivo: {(df_retornos.mean() > 0).sum()}")


if __name__ == "__main__":
    print("\nEscolha uma opção:")
    print("1. Extração completa")
    print("2. Amostra pequena (100 fundos)")
    
    opcao = input("\nOpção (1 ou 2): ").strip()
    
    if opcao == "2":
        extrair_amostra_pequena()
    else:
        main()