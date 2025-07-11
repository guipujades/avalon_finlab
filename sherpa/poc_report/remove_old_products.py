#!/usr/bin/env python3
"""
Remove a seção antiga de "Análise Detalhada dos Produtos" que contém 
produtos que não fazem mais parte da carteira de manutenção
"""

import re

# Ler o arquivo
with open('gestao-ativa.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remover a seção antiga de "Análise Detalhada dos Produtos" que vem DEPOIS da camada de manutenção
# Esta seção contém IHYG, SHYU, SGOV, SGLN que não fazem mais parte da nova carteira
pattern = r'</div>\s*</div>\s*<!-- Análise Detalhada dos Produtos -->.*?<!-- Camada de Ganho -->'

# Substituir por apenas a transição para a Camada de Ganho
replacement = '</div>\n\n            <!-- Camada de Ganho -->'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Salvar o arquivo modificado
with open('gestao-ativa.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Seção antiga de 'Análise Detalhada dos Produtos' removida")
print("✓ Produtos obsoletos (IHYG, SHYU, SGOV, SGLN) removidos")
print("✓ Mantida apenas a nova estrutura com PIMCO, IB01 e SGLN")