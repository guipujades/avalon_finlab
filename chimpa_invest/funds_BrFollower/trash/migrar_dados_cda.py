import os
import shutil
from pathlib import Path
from tqdm import tqdm

# Diretórios
SOURCE_DIR = Path("C:/Users/guilh/Documents/GitHub/sherpa/database/CDA")
TARGET_DIR = Path("C:/Users/guilh/Documents/GitHub/database/funds_cvm/CDA")

def migrar_dados_cda():
    # Criar diretório de destino
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    # Listar todos os arquivos para copiar
    arquivos_copiar = []
    
    # Arquivos na raiz
    for arquivo in SOURCE_DIR.glob("*.zip"):
        arquivos_copiar.append((arquivo, TARGET_DIR / arquivo.name))
    
    # Arquivos na pasta HIST
    hist_source = SOURCE_DIR / "HIST"
    if hist_source.exists():
        hist_target = TARGET_DIR / "HIST"
        hist_target.mkdir(exist_ok=True)
        for arquivo in hist_source.glob("*.zip"):
            arquivos_copiar.append((arquivo, hist_target / arquivo.name))
    
    # Copiar arquivos com progresso
    for origem, destino in tqdm(arquivos_copiar, desc="Copiando CDA"):
        if not destino.exists():
            shutil.copy2(origem, destino)
    
    print(f"\nMigração CDA concluída!")
    print(f"Total de arquivos copiados: {len(arquivos_copiar)}")
    print(f"Destino: {TARGET_DIR}")

if __name__ == "__main__":
    migrar_dados_cda()