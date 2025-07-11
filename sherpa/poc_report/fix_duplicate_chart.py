#!/usr/bin/env python3
"""
Remove duplicação do código do gráfico e corrige a estrutura
"""

import re

# Ler o arquivo
with open('gestao-ativa.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remover a duplicação no bloco catch
pattern = r'(} catch \(error\) \{.*?)\n\s*// Criar gráfico de backtest.*?}\);\s*}'

replacement = r'''\1}'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Salvar o arquivo modificado
with open('gestao-ativa.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Duplicação do código do gráfico removida")
print("✓ Estrutura do event listener corrigida")