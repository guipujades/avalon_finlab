import pickle
import sys

# Adicionar o diretório ao path
sys.path.append('/mnt/c/Users/guilh/Documents/GitHub/sherpa')

def verificar_carteira_serializada():
    """
    Verifica o conteúdo do arquivo serializado
    """
    caminho = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database/serial_carteiras/carteira_chimborazo.pkl"
    
    try:
        with open(caminho, 'rb') as f:
            # Tentar ler o pickle em modo básico
            import io
            data = f.read()
            print(f"Tamanho do arquivo: {len(data)} bytes")
            
            # Verificar se é um arquivo pickle válido
            if data[:2] == b'\x80\x04':
                print("Arquivo pickle protocolo 4 detectado")
            elif data[:2] == b'\x80\x03':
                print("Arquivo pickle protocolo 3 detectado")
                
            # Tentar uma análise básica do conteúdo
            content_str = str(data[:1000])
            
            # Procurar por palavras-chave
            if "Cotas de Fundos" in content_str:
                print("\n✓ ENCONTRADO: 'Cotas de Fundos' está presente no arquivo!")
            else:
                print("\n✗ NÃO ENCONTRADO: 'Cotas de Fundos' não aparece no início do arquivo")
                
            if "TP_APLIC" in content_str:
                print("✓ Coluna TP_APLIC está presente")
                
            if "CNPJ_FUNDO_CLASSE_COTA" in content_str:
                print("✓ Coluna CNPJ_FUNDO_CLASSE_COTA está presente")
                
            # Verificar datas
            print("\nDatas encontradas no arquivo:")
            for year in ['2024', '2025']:
                for month in range(1, 13):
                    date_str = f"{year}-{month:02d}"
                    if date_str.encode() in data:
                        print(f"  - {date_str}")
                        
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")

def processar_carteira_raw():
    """
    Processa a carteira diretamente dos arquivos ZIP
    """
    from carteiras_analysis_utils import processar_carteira_completa
    
    CNPJ = '54.195.596/0001-51'
    BASE_DIR = "/mnt/c/Users/guilh/Documents/GitHub/sherpa/database"
    
    print("\n\n=== PROCESSANDO CARTEIRA DIRETAMENTE DOS ARQUIVOS ZIP ===")
    
    try:
        # Processar apenas o arquivo mais recente
        carteiras = processar_carteira_completa(
            cnpj_fundo=CNPJ,
            base_dir=BASE_DIR,
            limite_arquivos=1
        )
        
        if carteiras:
            data = max(carteiras.keys())
            df = carteiras[data]
            
            print(f"\nProcessado período: {data}")
            print(f"Total de registros: {len(df)}")
            
            # Analisar TP_APLIC
            if 'TP_APLIC' in df.columns:
                print("\nDistribuição por TP_APLIC:")
                tp_counts = df['TP_APLIC'].value_counts()
                for tp, count in tp_counts.items():
                    print(f"  - {tp}: {count}")
                    
                # Verificar fundos
                fundos = df[df['TP_APLIC'] == 'Cotas de Fundos']
                print(f"\n✓ FUNDOS ENCONTRADOS: {len(fundos)} registros com TP_APLIC='Cotas de Fundos'")
                
                if len(fundos) > 0:
                    print("\nExemplos de fundos:")
                    cols_interesse = ['CNPJ_FUNDO_CLASSE_COTA', 'NM_FUNDO_CLASSE_SUBCLASSE_COTA', 'VL_MERC_POS_FINAL']
                    for i, (idx, row) in enumerate(fundos.head(5).iterrows()):
                        print(f"\n  Fundo {i+1}:")
                        for col in cols_interesse:
                            if col in row:
                                print(f"    {col}: {row[col]}")
                                
            # Salvar para análise
            print("\nSalvando dados completos...")
            df.to_csv('/mnt/c/Users/guilh/Documents/GitHub/sherpa/carteira_chimborazo_completa.csv', index=False)
            print("✓ Dados salvos em carteira_chimborazo_completa.csv")
            
            # Salvar apenas fundos
            if 'TP_APLIC' in df.columns:
                fundos = df[df['TP_APLIC'] == 'Cotas de Fundos']
                if len(fundos) > 0:
                    fundos.to_csv('/mnt/c/Users/guilh/Documents/GitHub/sherpa/fundos_chimborazo.csv', index=False)
                    print(f"✓ {len(fundos)} fundos salvos em fundos_chimborazo.csv")
                    
    except Exception as e:
        print(f"Erro ao processar: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== VERIFICAÇÃO SIMPLIFICADA DOS DADOS DO CHIMBORAZO ===\n")
    
    # Verificar arquivo serializado
    verificar_carteira_serializada()
    
    # Processar diretamente dos ZIPs
    processar_carteira_raw()