"""
Teste simplificado da estratégia de pairs trading
Sem dependências externas complexas
"""

import pickle
from pathlib import Path
import json

def test_simple():
    """Teste básico para verificar se os dados carregam"""
    data_path = Path(__file__).parent / 'futures_v2.pkl'
    
    try:
        with open(data_path, 'rb') as f:
            df = pickle.load(f)
        
        print("=== DADOS CARREGADOS COM SUCESSO ===")
        print(f"Tipo: {type(df)}")
        print(f"Shape: {df.shape}")
        print(f"Período: {df.index[0]} a {df.index[-1]}")
        
        # Lista contratos DI
        di_columns = [col for col in df.columns if col.startswith('DI1')]
        print(f"\nContratos DI encontrados: {len(di_columns)}")
        print("Primeiros 10 DIs:")
        for i, di in enumerate(di_columns[:10]):
            print(f"  {i+1}. {di}")
        
        # Verifica dados de exemplo
        if len(di_columns) >= 2:
            di1 = di_columns[0]
            di2 = di_columns[1]
            
            print(f"\n=== EXEMPLO DE SPREAD: {di1} vs {di2} ===")
            
            # Calcula spread simples
            spread = df[di1] - df[di2]
            
            print(f"Spread médio: {spread.mean():.4f}")
            print(f"Desvio padrão: {spread.std():.4f}")
            print(f"Mínimo: {spread.min():.4f}")
            print(f"Máximo: {spread.max():.4f}")
            
            # Simula estratégia básica
            window = 20
            n_std = 2.0
            
            # Calcula médias e bandas (forma simplificada)
            signals = 0
            for i in range(window, len(spread)):
                window_data = spread.iloc[i-window:i]
                mean = window_data.mean()
                std = window_data.std()
                
                upper_band = mean + n_std * std
                lower_band = mean - n_std * std
                
                if spread.iloc[i] > upper_band or spread.iloc[i] < lower_band:
                    signals += 1
            
            print(f"\n=== SIMULAÇÃO BÁSICA ===")
            print(f"Janela: {window} dias")
            print(f"Desvio padrão: {n_std}")
            print(f"Sinais gerados: {signals}")
            print(f"Frequência de sinais: {signals/len(spread)*100:.1f}%")
            
            # Salva resultado em JSON
            result = {
                'di1': di1,
                'di2': di2,
                'spread_mean': float(spread.mean()),
                'spread_std': float(spread.std()),
                'total_days': len(spread),
                'signals': signals,
                'signal_frequency': float(signals/len(spread)*100)
            }
            
            with open('test_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print("\nResultado salvo em test_result.json")
            
    except FileNotFoundError:
        print(f"Erro: Arquivo {data_path} não encontrado!")
        print("Certifique-se de que futures_v2.pkl está nesta pasta")
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_simple()