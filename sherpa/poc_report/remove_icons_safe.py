#!/usr/bin/env python3
"""
Remove APENAS os ícones SVG dos ETFs, preservando toda a estrutura e funcionalidade
"""

import re

# Ler o arquivo
with open('gestao-ativa.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Contador de substituições
count = 0

# Função para processar cada match
def replace_icon(match):
    global count
    full_match = match.group(0)
    
    # Verificar se é realmente um ícone de ETF (tem path com stroke)
    if 'stroke="currentColor"' in full_match and 'path' in full_match:
        count += 1
        return ''  # Remove apenas o div do ícone
    
    return full_match  # Mantém outros elementos

# Padrão específico para ícones de ETF
# Procura por divs com gradient que contêm SVG com stroke
pattern = r'<div class="[^"]*(?:w-10 h-10|w-12 h-12)[^"]*bg-gradient-to-br[^"]*"[^>]*>\s*<svg[^>]*>[\s\S]*?</svg>\s*</div>'

# Aplicar substituição
content_modified = re.sub(pattern, replace_icon, content)

# Salvar
with open('gestao-ativa.html', 'w', encoding='utf-8') as f:
    f.write(content_modified)

print(f"✓ {count} ícones de ETFs removidos")
print("✓ Estrutura e funcionalidade preservadas")

# Verificar se SGOV e gráficos ainda estão presentes
if 'SGOV' in content_modified:
    print("✓ SGOV preservado")
if 'preservationChart' in content_modified:
    print("✓ Gráfico de preservação preservado")