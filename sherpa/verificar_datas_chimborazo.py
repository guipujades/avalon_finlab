import os
import zipfile
from datetime import datetime

def verificar_datas_disponiveis():
    """
    Verifica quais datas de dados estão disponíveis para o Chimborazo
    """
    CNPJ_CHIMBORAZO = '54.195.596/0001-51'
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    CDA_DIR = os.path.join(BASE_DIR, 'CDA')
    
    print("Verificando datas disponíveis para o Chimborazo...")
    print("="*80)
    
    # Listar todos os arquivos ZIP
    arquivos_zip = sorted([f for f in os.listdir(CDA_DIR) if f.endswith('.zip') and f.startswith('cda_fi_')])
    
    print(f"\nTotal de arquivos ZIP encontrados: {len(arquivos_zip)}")
    print(f"Primeiro arquivo: {arquivos_zip[0] if arquivos_zip else 'Nenhum'}")
    print(f"Último arquivo: {arquivos_zip[-1] if arquivos_zip else 'Nenhum'}")
    
    # Verificar se o Chimborazo aparece nos arquivos mais recentes
    print(f"\nVerificando presença do Chimborazo nos 5 arquivos mais recentes...")
    
    cnpj_limpo = CNPJ_CHIMBORAZO.replace('.', '').replace('/', '').replace('-', '')
    
    for arquivo in arquivos_zip[-5:]:
        caminho_completo = os.path.join(CDA_DIR, arquivo)
        data_arquivo = arquivo.replace('cda_fi_', '').replace('.zip', '')
        
        try:
            with zipfile.ZipFile(caminho_completo, 'r') as zf:
                # Listar arquivos BLC
                arquivos_blc = [f for f in zf.namelist() if f.endswith('_BLC_1.csv') or f.endswith('_BLC_2.csv')]
                
                chimborazo_encontrado = False
                for arquivo_blc in arquivos_blc:
                    # Ler apenas as primeiras linhas para verificar
                    with zf.open(arquivo_blc) as f:
                        conteudo = f.read(10000).decode('latin-1')  # Ler apenas 10KB
                        if cnpj_limpo in conteudo or CNPJ_CHIMBORAZO in conteudo:
                            chimborazo_encontrado = True
                            break
                
                if chimborazo_encontrado:
                    print(f"  ✓ {data_arquivo}: Chimborazo ENCONTRADO")
                else:
                    print(f"  ✗ {data_arquivo}: Chimborazo NÃO encontrado")
                    
        except Exception as e:
            print(f"  ! {data_arquivo}: Erro ao processar - {str(e)}")
    
    # Verificar o arquivo serializado
    print(f"\n\nVerificando arquivo serializado...")
    serial_path = os.path.join(BASE_DIR, 'serial_carteiras', 'carteira_chimborazo.pkl')
    if os.path.exists(serial_path):
        mod_time = os.path.getmtime(serial_path)
        mod_date = datetime.fromtimestamp(mod_time)
        print(f"Arquivo serializado última modificação: {mod_date.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Arquivo serializado não encontrado!")

if __name__ == "__main__":
    verificar_datas_disponiveis()