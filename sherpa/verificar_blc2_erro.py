import zipfile
import pandas as pd
import os

def verificar_blc2():
    """
    Verifica o conteúdo do BLC_2 onde estão os fundos
    """
    arquivo_zip = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database/CDA/cda_fi_202505.zip"
    
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        # Listar arquivos
        print("Arquivos no ZIP:")
        for arq in zip_ref.namelist():
            if 'BLC' in arq:
                print(f"  - {arq}")
        
        # Extrair e verificar BLC_2
        blc2_name = 'cda_fi_BLC_2_202505.csv'
        print(f"\nExtraindo {blc2_name}...")
        
        # Extrair para diretório temporário
        temp_dir = "/tmp/cda_temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        zip_ref.extract(blc2_name, temp_dir)
        arquivo_csv = os.path.join(temp_dir, blc2_name)
        
        # Tentar ler com diferentes configurações
        print("\nTentando ler o arquivo com diferentes métodos...")
        
        # Método 1: Padrão com tratamento de erro
        try:
            df = pd.read_csv(arquivo_csv, sep=';', encoding='latin-1', on_bad_lines='skip')
            print(f"✓ Método 1 (skip bad lines): {len(df)} registros lidos")
            
            # Filtrar Chimborazo
            chimbo = df[df['CNPJ_FUNDO_CLASSE'] == '54.195.596/0001-51']
            print(f"  - Registros do Chimborazo: {len(chimbo)}")
            
            if 'TP_APLIC' in chimbo.columns:
                print("\n  Tipos de aplicação encontrados:")
                for tp in chimbo['TP_APLIC'].unique():
                    count = len(chimbo[chimbo['TP_APLIC'] == tp])
                    print(f"    - {tp}: {count}")
                    
            # Salvar amostra
            if len(chimbo) > 0:
                chimbo.to_csv('/mnt/c/Users/guilh/Documents/GitHub/sherpa/chimborazo_blc2_amostra.csv', index=False)
                print("\n✓ Amostra salva em chimborazo_blc2_amostra.csv")
                
                # Mostrar alguns fundos
                fundos = chimbo[chimbo['TP_APLIC'] == 'Cotas de Fundos']
                if len(fundos) > 0:
                    print(f"\n✓ FUNDOS ENCONTRADOS: {len(fundos)} fundos")
                    print("\nPrimeiros 5 fundos:")
                    for i, (idx, row) in enumerate(fundos.head().iterrows()):
                        cnpj = row.get('CNPJ_FUNDO_CLASSE_COTA', 'N/A')
                        nome = row.get('NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'N/A')
                        valor = row.get('VL_MERC_POS_FINAL', 0)
                        print(f"  {i+1}. {cnpj} - {nome[:50]}... R$ {valor:,.2f}")
                        
        except Exception as e:
            print(f"✗ Erro no método 1: {e}")
            
        # Método 2: Ler apenas primeiras linhas para debug
        print("\n\nVerificando primeiras linhas do arquivo...")
        with open(arquivo_csv, 'r', encoding='latin-1') as f:
            for i, linha in enumerate(f):
                if i < 5:
                    print(f"Linha {i}: {linha[:100]}...")
                if i == 5:
                    break
                    
        # Limpar
        import shutil
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    verificar_blc2()