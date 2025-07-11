import re

with open('fi_analysis_utils.py', 'r') as f:
    lines = f.readlines()

problems = []
try_stack = []

for i, line in enumerate(lines):
    # Detecta try
    if re.match(r'^(\s*)try\s*:', line):
        indent = len(re.match(r'^(\s*)', line).group(1))
        try_stack.append((i+1, indent))
    
    # Detecta except
    elif re.match(r'^(\s*)except\s*.*:', line):
        indent = len(re.match(r'^(\s*)', line).group(1))
        
        # Verifica se há um try correspondente
        if not try_stack:
            problems.append(f'Linha {i+1}: except sem try correspondente')
        else:
            # Verifica se a indentação está correta
            expected_indent = try_stack[-1][1]
            if indent \!= expected_indent:
                problems.append(f'Linha {i+1}: except com indentação incorreta (esperado: {expected_indent} espaços, encontrado: {indent} espaços)')
            try_stack.pop()

# Verifica try sem except
for try_line, _ in try_stack:
    problems.append(f'Linha {try_line}: try sem except correspondente')

if problems:
    print('Problemas encontrados:')
    for p in problems:
        print(p)
else:
    print('Nenhum problema de indentação encontrado em blocos try/except')
