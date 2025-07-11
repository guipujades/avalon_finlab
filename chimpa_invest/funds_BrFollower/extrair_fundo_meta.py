import pandas as pd
import numpy as np
from pathlib import Path

def extrair_fundo_meta(cnpj_target="38.351.476/0001-40"):
    """
    Extrai a série de retornos de um fundo específico para usar como meta
    
    Args:
        cnpj_target: CNPJ do fundo alvo (com formatação)
    """
    
    # Carregar dados de retornos
    retornos_path = Path("C:/Users/guilh/Documents/GitHub/database/chimpa/retornos_fundos_cvm.csv")
    
    print(f"Carregando dados de retornos...")
    df_retornos = pd.read_csv(retornos_path, index_col=0, parse_dates=True)
    
    print(f"Total de fundos disponíveis: {len(df_retornos.columns)}")
    print(f"Período dos dados: {df_retornos.index[0]} até {df_retornos.index[-1]}")
    
    # Verificar se o fundo existe
    if cnpj_target in df_retornos.columns:
        print(f"✅ Fundo {cnpj_target} encontrado!")
        
        # Extrair série do fundo
        serie_fundo = df_retornos[cnpj_target].dropna()
        
        print(f"Dados disponíveis: {len(serie_fundo)} observações")
        print(f"Período: {serie_fundo.index[0]} até {serie_fundo.index[-1]}")
        print(f"Retorno total: {serie_fundo.iloc[-1]:.2%}")
        
        # Salvar série isolada
        output_dir = Path("C:/Users/guilh/Documents/GitHub/database/chimpa")
        
        # Salvar como CSV
        serie_fundo_df = pd.DataFrame({
            'data': serie_fundo.index,
            'retorno_acumulado': serie_fundo.values
        })
        
        output_file = output_dir / f"fundo_meta_{cnpj_target.replace('.', '').replace('/', '').replace('-', '')}.csv"
        serie_fundo_df.to_csv(output_file, index=False)
        
        print(f"\n📊 Série do fundo salva em: {output_file}")
        
        # Mostrar estatísticas básicas
        retornos_diarios = serie_fundo.pct_change().dropna()
        
        print(f"\n📈 Estatísticas:")
        print(f"Retorno médio diário: {retornos_diarios.mean():.4%}")
        print(f"Volatilidade diária: {retornos_diarios.std():.4%}")
        print(f"Sharpe (anualizado): {retornos_diarios.mean() / retornos_diarios.std() * np.sqrt(252):.2f}")
        
        # Mostrar amostra dos dados
        print(f"\n📋 Primeiros valores:")
        print(serie_fundo_df.head(10))
        
        return serie_fundo
        
    else:
        print(f"❌ Fundo {cnpj_target} não encontrado!")
        print(f"\nPrimeiros 10 CNPJs disponíveis:")
        for i, cnpj in enumerate(df_retornos.columns[:10]):
            print(f"  {i+1}. {cnpj}")
        
        return None

if __name__ == "__main__":
    # Extrair fundo específico
    serie = extrair_fundo_meta("38.351.476/0001-40")