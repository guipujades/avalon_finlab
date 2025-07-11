#!/usr/bin/env python3
"""
Scraper de teste simplificado sem dependências externas
Salva dados de imóveis diariamente em JSON
"""

import json
import os
from datetime import datetime
import re

class ScraperTesteSemDeps:
    def __init__(self):
        self.data_dir = 'dados_imoveis'
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Mapeamento de bairros de Brasília
        self.siglas_bairros = {
            'asa sul': 'ASS',
            'asa norte': 'ASN',
            'lago sul': 'LS',
            'lago norte': 'LN',
            'sudoeste': 'SW',
            'noroeste': 'NW',
            'águas claras': 'AC',
            'aguas claras': 'AC',
            'taguatinga': 'TAG',
            'ceilândia': 'CEI',
            'ceilandia': 'CEI',
            'samambaia': 'SAM',
            'vicente pires': 'VP',
            'guará': 'GUA',
            'guara': 'GUA',
            'sobradinho': 'SOB',
            'planaltina': 'PLA',
            'gama': 'GAM',
            'santa maria': 'SM',
            'recanto das emas': 'RDE',
            'riacho fundo': 'RF',
            'brazlândia': 'BRZ',
            'brazlandia': 'BRZ',
            'paranoá': 'PAR',
            'paranoa': 'PAR',
            'itapoã': 'ITA',
            'itapoa': 'ITA',
            'octogonal': 'OCT',
            'cruzeiro': 'CRZ',
            'park way': 'PKW',
            'jardim botânico': 'JB',
            'jardim botanico': 'JB',
            'são sebastião': 'SS',
            'sao sebastiao': 'SS',
            'arniqueiras': 'ARN'
        }
    
    def parse_endereco(self, endereco_completo):
        """
        Converte endereço completo em formato resumido
        Ex: "SQS 308 Bloco A Apartamento 201, Asa Sul" -> "ASS_308_A_201"
        """
        if not endereco_completo:
            return "SEM_ENDERECO"
        
        endereco_lower = endereco_completo.lower()
        
        # Identifica o bairro
        bairro_sigla = None
        for bairro, sigla in self.siglas_bairros.items():
            if bairro in endereco_lower:
                bairro_sigla = sigla
                break
        
        if not bairro_sigla:
            # Tenta identificar por padrões conhecidos
            if 'sqs' in endereco_lower:
                bairro_sigla = 'ASS'
            elif 'sqn' in endereco_lower:
                bairro_sigla = 'ASN'
            elif 'qn' in endereco_lower or 'qi' in endereco_lower:
                if 'lago' in endereco_lower:
                    bairro_sigla = 'LN' if 'norte' in endereco_lower else 'LS'
                else:
                    bairro_sigla = 'BSB'
            else:
                bairro_sigla = 'BSB'
        
        # Extrai números e identificadores
        numeros = re.findall(r'\d+', endereco_completo)
        
        # Identifica quadra
        quadra = None
        quadra_patterns = [
            r'(?:quadra|qd|q\.?)\s*(\d+)',
            r'(?:sqs|sqn|qi|qn)\s*(\d+)',
            r'(?:rua|r\.?)\s*(\d+)',
            r'(?:qua)\s*(\d+)'
        ]
        
        for pattern in quadra_patterns:
            match = re.search(pattern, endereco_lower)
            if match:
                quadra = match.group(1)
                break
        
        if not quadra and numeros:
            quadra = numeros[0]
        
        # Identifica bloco
        bloco = None
        bloco_match = re.search(r'(?:bloco|bl|b\.?)\s*([a-z0-9]+)', endereco_lower)
        if bloco_match:
            bloco = bloco_match.group(1).upper()
        
        # Identifica apartamento/casa
        unidade = None
        unidade_patterns = [
            r'(?:apartamento|apto|ap\.?)\s*(\d+)',
            r'(?:casa|cs)\s*(\d+)',
            r'(?:lote|lt)\s*(\d+)',
            r'(?:sala)\s*(\d+)'
        ]
        
        for pattern in unidade_patterns:
            match = re.search(pattern, endereco_lower)
            if match:
                unidade = match.group(1)
                break
        
        # Monta o endereço resumido
        partes = [bairro_sigla]
        if quadra:
            partes.append(quadra)
        if bloco:
            partes.append(bloco)
        if unidade:
            partes.append(unidade)
        
        return '_'.join(partes)
    
    def load_daily_data(self, date_str):
        """Carrega dados do dia ou cria estrutura vazia"""
        filename = os.path.join(self.data_dir, f'imoveis_{date_str}.json')
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_daily_data(self, data, date_str):
        """Salva dados do dia"""
        filename = os.path.join(self.data_dir, f'imoveis_{date_str}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Dados salvos em {filename}")
    
    def gerar_dados_teste(self):
        """
        Gera dados de teste simulando um scraping real
        Em produção, aqui você faria o scraping real do site escolhido
        """
        print("🔄 Gerando dados de teste...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_data = self.load_daily_data(today)
        
        if today not in daily_data:
            daily_data[today] = {}
        
        # Dados de teste - simula imóveis capturados
        imoveis_teste = [
            {
                'titulo': 'Apartamento 3 quartos - Asa Sul',
                'endereco': 'SQS 308 Bloco A Apartamento 201, Asa Sul, Brasília',
                'preco': 850000,
                'area': 120,
                'quartos': 3,
                'banheiros': 2,
                'vagas': 2,
                'descricao': 'Apartamento reformado com vista livre',
                'url': 'https://exemplo.com/imovel/1'
            },
            {
                'titulo': 'Cobertura Duplex - Asa Norte',
                'endereco': 'SQN 208 Bloco B Apartamento 604, Asa Norte, Brasília',
                'preco': 1200000,
                'area': 180,
                'quartos': 4,
                'banheiros': 3,
                'vagas': 3,
                'descricao': 'Cobertura com terraço gourmet',
                'url': 'https://exemplo.com/imovel/2'
            },
            {
                'titulo': 'Casa em Condomínio - Lago Norte',
                'endereco': 'QI 5 Conjunto 12 Casa 15, Lago Norte, Brasília',
                'preco': 2500000,
                'area': 400,
                'quartos': 4,
                'banheiros': 4,
                'vagas': 4,
                'descricao': 'Casa com piscina em condomínio fechado',
                'url': 'https://exemplo.com/imovel/3'
            },
            {
                'titulo': 'Apartamento 2 quartos - Águas Claras',
                'endereco': 'Rua 25 Norte Lote 5 Apto 302, Águas Claras, Brasília',
                'preco': 450000,
                'area': 65,
                'quartos': 2,
                'banheiros': 1,
                'vagas': 1,
                'descricao': 'Apartamento próximo ao metrô',
                'url': 'https://exemplo.com/imovel/4'
            },
            {
                'titulo': 'Casa Térrea - Park Way',
                'endereco': 'Quadra 26 Conjunto 3 Casa 18, Park Way, Brasília',
                'preco': 1800000,
                'area': 350,
                'quartos': 3,
                'banheiros': 3,
                'vagas': 3,
                'descricao': 'Casa térrea com amplo jardim',
                'url': 'https://exemplo.com/imovel/5'
            },
            {
                'titulo': 'Kitnet - Asa Norte',
                'endereco': 'SQN 203 Bloco K Apartamento 105, Asa Norte, Brasília',
                'preco': 280000,
                'area': 28,
                'quartos': 1,
                'banheiros': 1,
                'vagas': 0,
                'descricao': 'Kitnet funcional próxima à UnB',
                'url': 'https://exemplo.com/imovel/6'
            },
            {
                'titulo': 'Apartamento Garden - Sudoeste',
                'endereco': 'SQSW 105 Bloco C Apartamento 101, Sudoeste, Brasília',
                'preco': 980000,
                'area': 150,
                'quartos': 3,
                'banheiros': 2,
                'vagas': 2,
                'descricao': 'Garden com área externa privativa',
                'url': 'https://exemplo.com/imovel/7'
            },
            {
                'titulo': 'Casa Colonial - Lago Sul',
                'endereco': 'QI 23 Conjunto 8 Casa 12, Lago Sul, Brasília',
                'preco': 4500000,
                'area': 600,
                'quartos': 5,
                'banheiros': 5,
                'vagas': 6,
                'descricao': 'Casa colonial com vista para o lago',
                'url': 'https://exemplo.com/imovel/8'
            }
        ]
        
        # Processa cada imóvel
        novos_imoveis = 0
        atualizados = 0
        
        for imovel in imoveis_teste:
            endereco_resumido = self.parse_endereco(imovel['endereco'])
            
            # Verifica se já existe
            if endereco_resumido in daily_data[today]:
                atualizados += 1
                print(f"📝 Atualizando: {endereco_resumido}")
            else:
                novos_imoveis += 1
                print(f"🆕 Novo imóvel: {endereco_resumido}")
            
            # Estrutura de dados padronizada
            imovel_data = {
                'titulo': imovel['titulo'],
                'preco': imovel['preco'],
                'area': imovel['area'],
                'quartos': imovel['quartos'],
                'banheiros': imovel['banheiros'],
                'vagas': imovel['vagas'],
                'endereco_completo': imovel['endereco'],
                'endereco_resumido': endereco_resumido,
                'descricao': imovel['descricao'],
                'url': imovel['url'],
                'site': 'Teste Scraper',
                'data_captura': datetime.now().isoformat(),
                'preco_m2': round(imovel['preco'] / imovel['area'], 2) if imovel['area'] else None
            }
            
            daily_data[today][endereco_resumido] = imovel_data
        
        # Salva os dados
        self.save_daily_data(daily_data, today)
        
        print(f"\n✅ Scraping concluído: {novos_imoveis} novos, {atualizados} atualizados")
        
        return daily_data[today]
    
    def mostrar_resumo(self, data=None):
        """Mostra resumo dos dados coletados"""
        if not data:
            today = datetime.now().strftime('%Y-%m-%d')
            daily_data = self.load_daily_data(today)
            data = daily_data.get(today, {})
        
        if not data:
            print("❌ Nenhum dado encontrado para hoje.")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMO DO SCRAPING - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"{'='*60}")
        
        total = len(data)
        precos = [item['preco'] for item in data.values() if item.get('preco')]
        areas = [item['area'] for item in data.values() if item.get('area')]
        
        print(f"\n📈 Total de imóveis: {total}")
        
        if precos:
            print(f"\n💰 PREÇOS:")
            print(f"  • Médio: R$ {sum(precos)/len(precos):,.2f}")
            print(f"  • Mínimo: R$ {min(precos):,.2f}")
            print(f"  • Máximo: R$ {max(precos):,.2f}")
        
        if areas:
            print(f"\n📐 ÁREAS:")
            print(f"  • Média: {sum(areas)/len(areas):.1f} m²")
            print(f"  • Mínima: {min(areas):.1f} m²")
            print(f"  • Máxima: {max(areas):.1f} m²")
        
        # Contagem por bairro
        bairros = {}
        for item in data.values():
            endereco = item.get('endereco_resumido', '')
            if '_' in endereco:
                sigla = endereco.split('_')[0]
                bairros[sigla] = bairros.get(sigla, 0) + 1
        
        if bairros:
            print(f"\n🏘️ IMÓVEIS POR REGIÃO:")
            for bairro, count in sorted(bairros.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {bairro}: {count}")
        
        # Exemplos de imóveis
        print(f"\n🏠 EXEMPLOS DE IMÓVEIS CAPTURADOS:")
        for i, (key, item) in enumerate(list(data.items())[:3]):
            print(f"\n{i+1}. {item['titulo']}")
            print(f"   📍 {item['endereco_completo']}")
            print(f"   💵 R$ {item['preco']:,.2f}")
            print(f"   📏 {item['area']} m² | 🛏️ {item['quartos']} quartos")
            print(f"   🔑 ID: {key}")

def main():
    """Função principal"""
    scraper = ScraperTesteSemDeps()
    
    print("\n🏠 SCRAPER DE IMÓVEIS - TESTE SIMPLIFICADO")
    print("=" * 60)
    print("Este é um teste com dados simulados.")
    print("Em produção, substitua por scraping real do site desejado.")
    print("=" * 60)
    
    try:
        # Executa o "scraping" (dados de teste)
        dados = scraper.gerar_dados_teste()
        
        # Mostra resumo
        scraper.mostrar_resumo(dados)
        
        print(f"\n✅ Teste concluído com sucesso!")
        print(f"📁 Dados salvos em: {os.path.abspath(scraper.data_dir)}/")
        print(f"\n💡 Dica: Os dados são salvos diariamente no formato:")
        print(f"   imoveis_YYYY-MM-DD.json")
        print(f"\n📝 Estrutura do JSON:")
        print(f"   - Chave principal: data (YYYY-MM-DD)")
        print(f"   - Sub-chave: endereço resumido (ex: ASS_308_A_201)")
        print(f"   - Dados: informações completas do imóvel")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()