from carteiras_analysis_utils import processar_carteira_completa, salvar_carteira_serializada
import os

# Configurações
CNPJ_CHIMBORAZO = '54.195.596/0001-51'
NOME_CHIMBORAZO = 'chimborazo'
BASE_DIR = r"C:\Users\guilh\Documents\GitHub\sherpa\database"

print("Forçando atualização da carteira do Chimborazo...")
print("="*80)

# Remover arquivo serializado antigo para forçar reprocessamento
serial_path = os.path.join(BASE_DIR, 'serial_carteiras', 'carteira_chimborazo.pkl')
if os.path.exists(serial_path):
    print(f"\nRemovendo arquivo serializado antigo...")
    os.rename(serial_path, serial_path + '.backup')
    print("Arquivo movido para backup")

# Processar apenas os 3 arquivos mais recentes
print("\nProcessando arquivos mais recentes...")
carteiras = processar_carteira_completa(
    cnpj_fundo=CNPJ_CHIMBORAZO,
    base_dir=BASE_DIR,
    limite_arquivos=3  # Processar apenas os 3 mais recentes
)

if carteiras:
    print(f"\nDatas encontradas: {sorted(carteiras.keys())}")
    data_mais_recente = max(carteiras.keys())
    print(f"Data mais recente: {data_mais_recente}")
    
    # Salvar
    salvar_carteira_serializada(
        carteiras=carteiras,
        nome_fundo=NOME_CHIMBORAZO,
        base_dir=BASE_DIR
    )
    print("\nDados atualizados salvos com sucesso!")
else:
    print("\nERRO: Nenhuma carteira encontrada!")
    # Restaurar backup se necessário
    if os.path.exists(serial_path + '.backup'):
        os.rename(serial_path + '.backup', serial_path)
        print("Backup restaurado")