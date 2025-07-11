import os
import pickle
from carteiras_analysis_utils import processar_carteira_completa

def atualizar_carteira_chimborazo():
    """
    Atualiza o arquivo serializado do Chimborazo com todos os dados disponíveis de 2025
    """
    CNPJ_CHIMBORAZO = '54.195.596/0001-51'
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    
    print("Atualizando carteira do Chimborazo com dados até maio/2025...")
    
    # Processar últimos 12 meses para garantir que pegamos todos os dados de 2025
    carteiras = processar_carteira_completa(
        cnpj_fundo=CNPJ_CHIMBORAZO,
        base_dir=BASE_DIR,
        limite_arquivos=12  # Processar últimos 12 arquivos
    )
    
    if carteiras:
        # Salvar dados serializados
        dados_completos = {
            'cnpj': CNPJ_CHIMBORAZO,
            'nome': 'CHIMBORAZO',
            'carteira_categorizada': carteiras
        }
        
        caminho_serial = os.path.join(BASE_DIR, 'serial_carteiras', 'carteira_chimborazo.pkl')
        os.makedirs(os.path.dirname(caminho_serial), exist_ok=True)
        
        with open(caminho_serial, 'wb') as f:
            pickle.dump(dados_completos, f)
        
        print(f"\nArquivo atualizado com sucesso!")
        print(f"Datas disponíveis: {sorted(carteiras.keys())}")
        print(f"Data mais recente: {max(carteiras.keys())}")
    else:
        print("Erro ao processar carteiras")

if __name__ == "__main__":
    atualizar_carteira_chimborazo()