from analise_temporal_fundos import AnalisadorTemporalFundos
import pandas as pd

# CNPJ do fundo específico para teste
cnpj_teste = "38.351.476/0001-40"  # CNPJ que você mencionou

def testar_analise_temporal():
    print("Testando análise temporal de fundos...")
    
    # Verificar se o CNPJ está nos retornos
    retornos_path = "C:/Users/guilh/Documents/GitHub/database/chimpa/retornos_fundos_cvm.csv"
    df_retornos = pd.read_csv(retornos_path, index_col=0, nrows=5)
    
    cnpj_usar = cnpj_teste
    if cnpj_teste in df_retornos.columns:
        print(f"✅ CNPJ {cnpj_teste} encontrado nos retornos")
    else:
        print(f"❌ CNPJ {cnpj_teste} não encontrado")
        # Pegar o primeiro CNPJ disponível
        cnpj_usar = df_retornos.columns[0]
        print(f"Usando {cnpj_usar} como teste")
    
    # Criar analisador
    analisador = AnalisadorTemporalFundos(
        cnpj_fundo=cnpj_usar,
        nome_fundo="Fundo Teste",
        periodo_minimo_anos=2
    )
    
    try:
        # Processar carteiras
        print("Processando carteiras...")
        resultado = analisador.processar_carteiras()
        
        if resultado:
            print("✅ Processamento concluído com sucesso!")
            print(f"Períodos encontrados: {len(resultado)}")
            
            # Mostrar exemplo dos dados
            if analisador.df_evolucao is not None and not analisador.df_evolucao.empty:
                print("\n📊 Exemplo dados de evolução:")
                print(analisador.df_evolucao.head())
            
            if analisador.df_acoes is not None and not analisador.df_acoes.empty:
                print("\n📈 Exemplo dados de ações:")
                print(analisador.df_acoes.head())
                
        else:
            print("❌ Nenhum dado encontrado")
            
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")

if __name__ == "__main__":
    testar_analise_temporal()