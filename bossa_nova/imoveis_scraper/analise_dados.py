import json

with open('dados_imoveis/imoveis_2025-06-24.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

imoveis = data['2025-06-24']
total = len(imoveis)

# Filtra dados válidos
com_preco = [i for i in imoveis.values() if i.get('preco')]
com_titulo = [i for i in imoveis.values() if i.get('titulo')]
com_endereco = [i for i in imoveis.values() if i.get('endereco_completo')]
com_area = [i for i in imoveis.values() if i.get('area')]

print(f'📊 ANÁLISE DOS DADOS CAPTURADOS')
print(f'='*40)
print(f'Total de imóveis: {total}')
print(f'Com título: {len(com_titulo)} ({len(com_titulo)/total*100:.1f}%)')
print(f'Com preço: {len(com_preco)} ({len(com_preco)/total*100:.1f}%)')
print(f'Com endereço: {len(com_endereco)} ({len(com_endereco)/total*100:.1f}%)')
print(f'Com área: {len(com_area)} ({len(com_area)/total*100:.1f}%)')

if com_preco:
    precos = [i['preco'] for i in com_preco]
    print(f'\n💰 ESTATÍSTICAS DE PREÇO:')
    print(f'Média: R$ {sum(precos)/len(precos):,.2f}')
    print(f'Mínimo: R$ {min(precos):,.2f}')
    print(f'Máximo: R$ {max(precos):,.2f}')

# Distribuição por bairro
bairros = {}
for key in imoveis.keys():
    if '_' in key:
        bairro = key.split('_')[0]
        bairros[bairro] = bairros.get(bairro, 0) + 1

print(f'\n🏘️ DISTRIBUIÇÃO POR BAIRRO:')
for bairro, count in sorted(bairros.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f'{bairro}: {count} imóveis')

# Exemplos de imóveis completos
print(f'\n🏠 EXEMPLOS DE IMÓVEIS BEM CAPTURADOS:')
exemplos = 0
for key, imovel in imoveis.items():
    if imovel.get('titulo') and imovel.get('preco') and imovel.get('endereco_completo'):
        print(f'\n{key}:')
        print(f'  {imovel["titulo"]}')
        print(f'  R$ {imovel["preco"]:,.2f}')
        print(f'  {imovel["endereco_completo"]}')
        if imovel.get('area'):
            print(f'  {imovel["area"]} m²')
        exemplos += 1
        if exemplos >= 3:
            break