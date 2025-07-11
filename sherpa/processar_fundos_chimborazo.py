import zipfile
import pandas as pd
import os
import pickle
from datetime import datetime

def processar_blc2_com_erro(arquivo_zip, cnpj_fundo='54.195.596/0001-51'):
    """
    Processa o arquivo BLC_2 que contém os fundos, lidando com erros de parsing
    """
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        # Extrair BLC_2
        blc2_name = None
        for arq in zip_ref.namelist():
            if 'BLC_2' in arq and arq.endswith('.csv'):
                blc2_name = arq
                break
                
        if not blc2_name:
            print("BLC_2 não encontrado!")
            return None
            
        print(f"Processando {blc2_name}...")
        
        # Extrair para memória
        with zip_ref.open(blc2_name) as f:
            # Ler linha por linha até encontrar erro
            linhas_validas = []
            linha_num = 0
            
            for linha in f:
                linha_num += 1
                try:
                    # Decodificar linha
                    linha_str = linha.decode('latin-1').strip()
                    
                    # Adicionar apenas se não for linha vazia
                    if linha_str:
                        linhas_validas.append(linha_str)
                        
                    # A cada 10000 linhas, mostrar progresso
                    if linha_num % 10000 == 0:
                        print(f"  Processadas {linha_num} linhas...")
                        
                except Exception as e:
                    print(f"  Erro na linha {linha_num}: {e}")
                    # Continuar processando
                    
            print(f"  Total de linhas válidas: {len(linhas_validas)}")
            
            # Converter para DataFrame
            if linhas_validas:
                # Primeira linha é o cabeçalho
                header = linhas_validas[0].split(';')
                
                # Processar dados
                dados = []
                for linha in linhas_validas[1:]:
                    try:
                        valores = linha.split(';')
                        # Garantir que tem o mesmo número de colunas
                        if len(valores) == len(header):
                            dados.append(valores)
                    except:
                        pass
                        
                print(f"  Total de registros processados: {len(dados)}")
                
                # Criar DataFrame
                df = pd.DataFrame(dados, columns=header)
                
                # Filtrar pelo CNPJ do Chimborazo
                df_chimbo = df[df['CNPJ_FUNDO_CLASSE'] == cnpj_fundo].copy()
                print(f"  Registros do Chimborazo: {len(df_chimbo)}")
                
                return df_chimbo
                
    return None

def processar_todos_blcs(base_dir, cnpj_fundo='54.195.596/0001-51'):
    """
    Processa todos os BLCs para capturar a carteira completa
    """
    resultados = {}
    
    # Listar arquivos ZIP de 2025
    arquivos_2025 = [
        'cda_fi_202501.zip',
        'cda_fi_202502.zip', 
        'cda_fi_202503.zip',
        'cda_fi_202504.zip',
        'cda_fi_202505.zip'
    ]
    
    for arquivo in arquivos_2025:
        caminho_zip = os.path.join(base_dir, 'CDA', arquivo)
        if not os.path.exists(caminho_zip):
            print(f"Arquivo não encontrado: {arquivo}")
            continue
            
        print(f"\n{'='*60}")
        print(f"Processando {arquivo}...")
        
        # Extrair período do nome
        periodo = arquivo.replace('cda_fi_', '').replace('.zip', '')
        data_formatada = f"{periodo[:4]}-{periodo[4:]}"
        
        dados_periodo = []
        
        with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
            # Processar cada BLC
            for num_blc in range(1, 9):
                blc_name = f'cda_fi_BLC_{num_blc}_{periodo}.csv'
                
                if blc_name not in zip_ref.namelist():
                    continue
                    
                print(f"\n  Processando BLC_{num_blc}...")
                
                try:
                    # Método especial para BLC_2
                    if num_blc == 2:
                        df_blc = processar_blc2_com_erro(caminho_zip, cnpj_fundo)
                        if df_blc is not None and len(df_blc) > 0:
                            df_blc['TIPO_BLC'] = f'BLC_{num_blc}'
                            dados_periodo.append(df_blc)
                    else:
                        # Método padrão para outros BLCs
                        with zip_ref.open(blc_name) as f:
                            try:
                                df = pd.read_csv(f, sep=';', encoding='latin-1', low_memory=False)
                                df_chimbo = df[df['CNPJ_FUNDO_CLASSE'] == cnpj_fundo].copy()
                                
                                if len(df_chimbo) > 0:
                                    print(f"    ✓ {len(df_chimbo)} registros encontrados")
                                    df_chimbo['TIPO_BLC'] = f'BLC_{num_blc}'
                                    dados_periodo.append(df_chimbo)
                                else:
                                    print(f"    - Nenhum registro do Chimborazo")
                                    
                            except Exception as e:
                                print(f"    ✗ Erro: {e}")
                                
                except Exception as e:
                    print(f"    ✗ Erro geral: {e}")
        
        # Consolidar dados do período
        if dados_periodo:
            df_consolidado = pd.concat(dados_periodo, ignore_index=True)
            resultados[data_formatada] = df_consolidado
            
            print(f"\n  Resumo de {data_formatada}:")
            print(f"  - Total de registros: {len(df_consolidado)}")
            
            if 'TP_APLIC' in df_consolidado.columns:
                print("  - Distribuição por TP_APLIC:")
                for tp, count in df_consolidado['TP_APLIC'].value_counts().items():
                    print(f"      {tp}: {count}")
                    
            # Converter valores para numérico
            if 'VL_MERC_POS_FINAL' in df_consolidado.columns:
                df_consolidado['VL_MERC_POS_FINAL'] = pd.to_numeric(
                    df_consolidado['VL_MERC_POS_FINAL'].str.replace(',', '.'), 
                    errors='coerce'
                )
                total = df_consolidado['VL_MERC_POS_FINAL'].sum()
                print(f"  - Valor total: R$ {total:,.2f}")
    
    return resultados

def salvar_carteira_completa(carteiras, base_dir):
    """
    Salva a carteira completa com todos os dados
    """
    # Preparar dados para serialização
    dados_completos = {
        'cnpj': '54.195.596/0001-51',
        'nome': 'CHIMBORAZO',
        'carteira_categorizada': carteiras
    }
    
    # Salvar pickle
    caminho_serial = os.path.join(base_dir, 'serial_carteiras', 'carteira_chimborazo_completa.pkl')
    os.makedirs(os.path.dirname(caminho_serial), exist_ok=True)
    
    with open(caminho_serial, 'wb') as f:
        pickle.dump(dados_completos, f)
    
    print(f"\n✓ Carteira completa salva em: {caminho_serial}")
    
    # Salvar também em Excel para análise
    with pd.ExcelWriter(os.path.join(base_dir, 'chimborazo_carteira_completa.xlsx')) as writer:
        for data, df in carteiras.items():
            # Limitar nome da aba a 31 caracteres (limite do Excel)
            sheet_name = data.replace('-', '_')
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"✓ Excel salvo em: chimborazo_carteira_completa.xlsx")

def main():
    BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"
    
    print("=== PROCESSANDO CARTEIRA COMPLETA DO CHIMBORAZO ===\n")
    
    # Processar todos os BLCs
    carteiras = processar_todos_blcs(BASE_DIR)
    
    if carteiras:
        print(f"\n\n{'='*60}")
        print("RESUMO GERAL:")
        print(f"Períodos processados: {sorted(carteiras.keys())}")
        
        # Salvar carteira completa
        salvar_carteira_completa(carteiras, BASE_DIR)
        
        # Análise final
        data_mais_recente = max(carteiras.keys())
        df_recente = carteiras[data_mais_recente]
        
        print(f"\n\nDADOS MAIS RECENTES ({data_mais_recente}):")
        print(f"Total de registros: {len(df_recente)}")
        
        if 'TP_APLIC' in df_recente.columns:
            fundos = df_recente[df_recente['TP_APLIC'] == 'Cotas de Fundos']
            print(f"\n✓ FUNDOS ENCONTRADOS: {len(fundos)} fundos")
            
            if len(fundos) > 0 and 'VL_MERC_POS_FINAL' in fundos.columns:
                fundos['VL_MERC_POS_FINAL'] = pd.to_numeric(
                    fundos['VL_MERC_POS_FINAL'].str.replace(',', '.'), 
                    errors='coerce'
                )
                total_fundos = fundos['VL_MERC_POS_FINAL'].sum()
                print(f"Valor total em fundos: R$ {total_fundos:,.2f}")

if __name__ == "__main__":
    main()