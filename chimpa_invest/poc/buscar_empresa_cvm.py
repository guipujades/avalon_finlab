#!/usr/bin/env python3
"""
Sistema de busca inteligente para empresas CVM
Busca por: ticker, nome, código CVM, CNPJ
"""
import json
from pathlib import Path
from difflib import get_close_matches
import re

class BuscadorEmpresasCVM:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.dados_path = self.base_path / "dados"
        
        # Carregar dados
        self.empresas = self._carregar_empresas()
        self.indice = self._carregar_indice()
        self.tickers = self._criar_mapa_tickers()
        
    def _carregar_empresas(self):
        """Carrega lista completa de empresas"""
        arquivo = self.dados_path / "empresas_cvm_completa.json"
        if arquivo.exists():
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _carregar_indice(self):
        """Carrega índice de busca"""
        arquivo = self.dados_path / "indice_busca_empresas.json"
        if arquivo.exists():
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"por_nome": {}, "por_codigo_cvm": {}, "por_cnpj": {}}
    
    def _criar_mapa_tickers(self):
        """Cria mapeamento de tickers comuns"""
        # Mapa básico de tickers conhecidos
        mapa = {
            # Bancos
            'ITUB3': 'ITAÚ UNIBANCO HOLDING',
            'ITUB4': 'ITAÚ UNIBANCO HOLDING',
            'BBAS3': 'BANCO DO BRASIL',
            'BBDC3': 'BANCO BRADESCO',
            'BBDC4': 'BANCO BRADESCO',
            'SANB3': 'BANCO SANTANDER',
            'SANB4': 'BANCO SANTANDER',
            'SANB11': 'BANCO SANTANDER',
            
            # Petróleo e Mineração
            'PETR3': 'PETROLEO BRASILEIRO',
            'PETR4': 'PETROLEO BRASILEIRO',
            'VALE3': 'VALE',
            'VALE': 'VALE',
            
            # Varejo
            'MGLU3': 'MAGAZINE LUIZA',
            'LREN3': 'LOJAS RENNER',
            'AMER3': 'AMERICANAS',
            'PETZ3': 'PET CENTER',
            'VIIA3': 'VIA',
            
            # Energia
            'ELET3': 'ELETROBRAS',
            'ELET6': 'ELETROBRAS',
            'CMIG3': 'CEMIG',
            'CMIG4': 'CEMIG',
            'CPFE3': 'CPFL ENERGIA',
            'ENBR3': 'EDP',
            'ENGI11': 'ENERGISA',
            
            # Outros
            'ABEV3': 'AMBEV',
            'WEGE3': 'WEG',
            'SUZB3': 'SUZANO',
            'RENT3': 'LOCALIZA',
            'RAIL3': 'RUMO',
            'EMBR3': 'EMBRAER',
            'AZUL4': 'AZUL',
            'GOLL4': 'GOL',
            'BEEF3': 'MINERVA',
            'JBSS3': 'JBS',
            'MRFG3': 'MARFRIG',
        }
        
        # Adicionar variações
        tickers_completos = {}
        for ticker, nome in mapa.items():
            tickers_completos[ticker] = nome
            # Adicionar sem números
            base = re.sub(r'\d+$', '', ticker)
            if base != ticker:
                tickers_completos[base] = nome
        
        return tickers_completos
    
    def buscar(self, termo):
        """Busca empresa por qualquer termo"""
        termo = termo.strip().upper()
        resultados = []
        
        # 1. Buscar por ticker
        if termo in self.tickers:
            nome_busca = self.tickers[termo]
            resultados.extend(self._buscar_por_nome_parcial(nome_busca))
            if resultados:
                return resultados
        
        # 2. Buscar por código CVM (se for número)
        if termo.isdigit():
            codigo = int(termo)
            if str(codigo) in self.indice.get('por_codigo_cvm', {}):
                resultados.extend(self.indice['por_codigo_cvm'][str(codigo)])
                if resultados:
                    return resultados
        
        # 3. Buscar por CNPJ
        cnpj_limpo = re.sub(r'[^\d]', '', termo)
        if len(cnpj_limpo) >= 8:  # Pelo menos os primeiros 8 dígitos
            for cnpj_key in self.indice.get('por_cnpj', {}).keys():
                if cnpj_limpo in re.sub(r'[^\d]', '', cnpj_key):
                    resultados.extend(self.indice['por_cnpj'][cnpj_key])
        
        if resultados:
            return resultados
        
        # 4. Buscar por nome exato
        if termo in self.indice.get('por_nome', {}):
            return self.indice['por_nome'][termo]
        
        # 5. Buscar por nome parcial
        resultados = self._buscar_por_nome_parcial(termo)
        if resultados:
            return resultados
        
        # 6. Buscar por similaridade
        return self._buscar_similar(termo)
    
    def _buscar_por_nome_parcial(self, termo):
        """Busca empresas que contenham o termo no nome"""
        resultados = []
        palavras = termo.split()
        
        # Primeiro, busca exata
        if termo in self.indice.get('por_nome', {}):
            return self.indice['por_nome'][termo]
        
        # Depois, busca por nome completo
        for nome_busca, empresas in self.indice.get('por_nome', {}).items():
            for empresa in empresas:
                if termo in empresa['nome_completo'].upper():
                    resultados.append(empresa)
        
        if resultados:
            return resultados
        
        # Por último, busca parcial por palavras
        for nome_busca, empresas in self.indice.get('por_nome', {}).items():
            # Verificar se todas as palavras do termo estão no nome
            if all(palavra in nome_busca for palavra in palavras):
                resultados.extend(empresas)
        
        # Remover duplicatas por código CVM
        vistos = set()
        unicos = []
        for emp in resultados:
            if emp['codigo_cvm'] not in vistos:
                vistos.add(emp['codigo_cvm'])
                unicos.append(emp)
        
        return unicos
    
    def _buscar_similar(self, termo):
        """Busca empresas com nomes similares"""
        todos_nomes = list(self.indice.get('por_nome', {}).keys())
        
        # Encontrar nomes similares
        similares = get_close_matches(termo, todos_nomes, n=5, cutoff=0.6)
        
        resultados = []
        for nome_similar in similares:
            resultados.extend(self.indice['por_nome'][nome_similar])
        
        return resultados
    
    def listar_sugestoes(self, resultados, max_sugestoes=10):
        """Lista sugestões formatadas"""
        if not resultados:
            return []
        
        sugestoes = []
        for i, emp in enumerate(resultados[:max_sugestoes]):
            sugestao = {
                'indice': i + 1,
                'nome_completo': emp['nome_completo'],
                'nome_busca': emp['nome_busca'],
                'codigo_cvm': emp['codigo_cvm'],
                'cnpj': emp['cnpj'],
                'total_docs': emp.get('total_documentos_ipe', 0)
            }
            sugestoes.append(sugestao)
        
        return sugestoes


def buscar_empresa_interativo(termo_inicial=None):
    """Função interativa para buscar empresa"""
    buscador = BuscadorEmpresasCVM()
    
    if termo_inicial:
        termo = termo_inicial
    else:
        print("=== Busca de Empresas CVM ===")
        print("Digite: ticker, nome, código CVM ou CNPJ")
        termo = input("\nBuscar: ").strip()
    
    if not termo:
        return None
    
    # Buscar
    resultados = buscador.buscar(termo)
    
    if not resultados:
        print(f"\nNenhuma empresa encontrada para '{termo}'")
        
        # Sugerir busca alternativa
        palavras = termo.split()
        if len(palavras) > 1:
            print("\nTentando busca por palavras individuais...")
            for palavra in palavras:
                if len(palavra) > 3:
                    res = buscador.buscar(palavra)
                    if res:
                        print(f"\nEncontradas {len(res)} empresas com '{palavra}'")
                        resultados = res
                        break
        
        if not resultados:
            return None
    
    # Se encontrou apenas uma, retornar
    if len(resultados) == 1:
        return resultados[0]
    
    # Se encontrou várias, listar opções
    print(f"\nEncontradas {len(resultados)} empresas:")
    sugestoes = buscador.listar_sugestoes(resultados)
    
    for sug in sugestoes:
        print(f"\n{sug['indice']}. {sug['nome_completo']}")
        print(f"   Código CVM: {sug['codigo_cvm']} | CNPJ: {sug['cnpj']}")
        print(f"   Documentos: {sug['total_docs']}")
    
    # Permitir seleção
    try:
        escolha = input("\nEscolha o número (ou ENTER para cancelar): ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(sugestoes):
            indice = int(escolha) - 1
            return resultados[indice]
    except:
        pass
    
    return None


# Função para uso direto em scripts
def obter_nome_cvm(termo):
    """Retorna o nome oficial CVM da empresa"""
    buscador = BuscadorEmpresasCVM()
    resultados = buscador.buscar(termo)
    
    if resultados:
        # Se encontrou múltiplos, pegar o com mais documentos
        if len(resultados) > 1:
            resultados.sort(key=lambda x: x.get('total_documentos_ipe', 0), reverse=True)
        return resultados[0]['nome_completo']
    
    return None


if __name__ == "__main__":
    import sys
    
    # Se passou argumento, buscar direto
    if len(sys.argv) > 1:
        termo = ' '.join(sys.argv[1:])
        empresa = buscar_empresa_interativo(termo)
        
        if empresa:
            print(f"\n=== Empresa Selecionada ===")
            print(f"Nome: {empresa['nome_completo']}")
            print(f"Código CVM: {empresa['codigo_cvm']}")
            print(f"CNPJ: {empresa['cnpj']}")
    else:
        # Modo interativo
        empresa = buscar_empresa_interativo()
        
        if empresa:
            print(f"\n=== Empresa Selecionada ===")
            print(f"Nome: {empresa['nome_completo']}")
            print(f"Código CVM: {empresa['codigo_cvm']}")
            print(f"CNPJ: {empresa['cnpj']}")