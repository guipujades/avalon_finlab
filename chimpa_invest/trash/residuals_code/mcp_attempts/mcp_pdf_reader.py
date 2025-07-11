"""
Interface com MCP (Model Context Protocol) para leitura de PDFs grandes
"""
import os
import json
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass
import hashlib
import re
from datetime import datetime


@dataclass
class DocumentChunk:
    """Representa um pedaço do documento"""
    content: str
    page_numbers: List[int]
    chunk_index: int
    total_chunks: int
    metadata: Dict[str, Any]


@dataclass
class TableData:
    """Representa dados extraídos de tabela"""
    headers: List[str]
    rows: List[List[str]]
    page_number: int
    table_index: int


class MCPPDFReader:
    """
    Leitor de PDFs otimizado para documentos financeiros grandes
    Integração com MCP do Claude para processamento eficiente
    """
    
    def __init__(self, chunk_size: int = 4000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.processed_cache = {}
        
    def read_pdf(self, file_path: str, extract_tables: bool = True) -> Dict[str, Any]:
        """
        Lê PDF e retorna conteúdo estruturado
        
        Args:
            file_path: Caminho do arquivo PDF
            extract_tables: Se deve extrair tabelas separadamente
            
        Returns:
            Documento estruturado com texto e tabelas
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        # Verifica cache
        file_hash = self._get_file_hash(file_path)
        if file_hash in self.processed_cache:
            return self.processed_cache[file_hash]
            
        document = {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_hash': file_hash,
            'processed_at': datetime.now().isoformat(),
            'content': '',
            'chunks': [],
            'tables': [],
            'metadata': {}
        }
        
        # Simula extração via MCP
        # Em produção, isso seria uma chamada real ao MCP
        raw_content = self._simulate_mcp_extraction(file_path)
        
        document['content'] = raw_content
        document['chunks'] = list(self._create_chunks(raw_content))
        
        if extract_tables:
            document['tables'] = self._extract_tables_from_content(raw_content)
            
        # Extrai metadados
        document['metadata'] = self._extract_metadata(raw_content)
        
        # Cacheia resultado
        self.processed_cache[file_hash] = document
        
        return document
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calcula hash do arquivo para cache"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _simulate_mcp_extraction(self, file_path: str) -> str:
        """
        Simula extração via MCP
        Em produção, seria substituído por chamada real ao MCP
        """
        # Por ora, retorna conteúdo simulado
        return f"""
        DEMONSTRAÇÕES FINANCEIRAS
        Empresa XYZ S.A.
        Exercício findo em 31 de dezembro de 2024
        
        BALANÇO PATRIMONIAL
        (Em milhares de reais)
        
        ATIVO                           2024        2023
        Circulante                    
          Caixa e equivalentes       150.000     120.000
          Contas a receber           200.000     180.000
          Estoques                   100.000      90.000
        Total Circulante             450.000     390.000
        
        Não Circulante
          Imobilizado                800.000     750.000
          Intangível                 150.000     140.000
        Total Não Circulante         950.000     890.000
        
        TOTAL DO ATIVO             1.400.000   1.280.000
        
        DEMONSTRAÇÃO DO RESULTADO
        (Em milhares de reais)
        
                                        2024        2023
        Receita Líquida               900.000     820.000
        Custo dos Produtos Vendidos  (540.000)   (492.000)
        Lucro Bruto                   360.000     328.000
        
        Despesas Operacionais        (180.000)   (164.000)
        EBIT                          180.000     164.000
        
        Resultado Financeiro          (30.000)    (28.000)
        Lucro Antes do IR             150.000     136.000
        
        IR e CSLL                     (45.000)    (40.800)
        Lucro Líquido                 105.000      95.200
        """
    
    def _create_chunks(self, content: str) -> Generator[DocumentChunk, None, None]:
        """
        Divide conteúdo em chunks com overlap
        """
        lines = content.split('\n')
        total_lines = len(lines)
        
        chunk_index = 0
        start_idx = 0
        
        # Estima número total de chunks
        total_chunks = (total_lines - self.overlap) // (self.chunk_size - self.overlap) + 1
        
        while start_idx < total_lines:
            end_idx = min(start_idx + self.chunk_size, total_lines)
            
            chunk_lines = lines[start_idx:end_idx]
            chunk_content = '\n'.join(chunk_lines)
            
            # Estima páginas (simplificado)
            pages_start = (start_idx // 50) + 1
            pages_end = (end_idx // 50) + 1
            page_numbers = list(range(pages_start, pages_end + 1))
            
            yield DocumentChunk(
                content=chunk_content,
                page_numbers=page_numbers,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                metadata={
                    'line_start': start_idx,
                    'line_end': end_idx,
                    'char_count': len(chunk_content)
                }
            )
            
            chunk_index += 1
            start_idx = end_idx - self.overlap
            
            if start_idx >= total_lines:
                break
    
    def _extract_tables_from_content(self, content: str) -> List[TableData]:
        """
        Extrai tabelas do conteúdo
        """
        tables = []
        lines = content.split('\n')
        
        table_index = 0
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Detecta início de tabela (linha com múltiplos espaços/tabs)
            if self._is_table_row(line):
                table_lines = [line]
                j = i + 1
                
                # Coleta linhas da tabela
                while j < len(lines) and self._is_table_row(lines[j]):
                    table_lines.append(lines[j])
                    j += 1
                
                if len(table_lines) > 2:  # Mínimo para ser considerado tabela
                    table = self._parse_table(table_lines, table_index)
                    if table:
                        tables.append(table)
                        table_index += 1
                
                i = j
            else:
                i += 1
                
        return tables
    
    def _is_table_row(self, line: str) -> bool:
        """Detecta se linha parece ser parte de tabela"""
        # Conta espaços múltiplos ou tabs
        spaces_count = len(re.findall(r'\s{2,}|\t', line))
        
        # Verifica se tem números
        has_numbers = bool(re.search(r'\d', line))
        
        return spaces_count >= 2 or (spaces_count >= 1 and has_numbers)
    
    def _parse_table(self, lines: List[str], table_index: int) -> Optional[TableData]:
        """Parseia linhas de tabela"""
        if not lines:
            return None
            
        # Primeira linha geralmente é header
        headers = re.split(r'\s{2,}|\t', lines[0].strip())
        headers = [h for h in headers if h]  # Remove vazios
        
        rows = []
        for line in lines[1:]:
            cells = re.split(r'\s{2,}|\t', line.strip())
            cells = [c for c in cells if c]
            if cells:
                rows.append(cells)
                
        if headers and rows:
            return TableData(
                headers=headers,
                rows=rows,
                page_number=1,  # Simplificado
                table_index=table_index
            )
            
        return None
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extrai metadados do documento"""
        metadata = {
            'type': 'financial_report',
            'language': 'pt-BR',
            'extracted_dates': [],
            'extracted_values': [],
            'key_sections': []
        }
        
        # Extrai datas
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}'
        dates = re.findall(date_pattern, content)
        metadata['extracted_dates'] = list(set(dates))
        
        # Extrai valores monetários
        money_pattern = r'R\$\s*[\d.,]+|[\d.,]+\s*(?:mil|milhões|bilhões)'
        values = re.findall(money_pattern, content)
        metadata['extracted_values'] = values[:10]  # Limita a 10
        
        # Identifica seções principais
        section_keywords = [
            'balanço patrimonial', 'demonstração do resultado',
            'fluxo de caixa', 'notas explicativas', 'relatório',
            'ebitda', 'receita', 'lucro'
        ]
        
        content_lower = content.lower()
        for keyword in section_keywords:
            if keyword in content_lower:
                metadata['key_sections'].append(keyword)
                
        return metadata
    
    def search_in_chunks(self, document: Dict[str, Any], 
                        query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Busca query nos chunks do documento
        
        Args:
            document: Documento processado
            query: Termo de busca
            max_results: Número máximo de resultados
            
        Returns:
            Chunks relevantes com scores
        """
        results = []
        query_lower = query.lower()
        
        for chunk in document['chunks']:
            content_lower = chunk.content.lower()
            
            # Conta ocorrências
            occurrences = content_lower.count(query_lower)
            
            if occurrences > 0:
                # Calcula contexto
                first_occurrence = content_lower.find(query_lower)
                context_start = max(0, first_occurrence - 100)
                context_end = min(len(chunk.content), first_occurrence + len(query) + 100)
                context = chunk.content[context_start:context_end]
                
                results.append({
                    'chunk_index': chunk.chunk_index,
                    'pages': chunk.page_numbers,
                    'occurrences': occurrences,
                    'context': context,
                    'score': occurrences * (1 / (chunk.chunk_index + 1))
                })
                
        # Ordena por score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:max_results]
    
    def extract_financial_data(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados financeiros estruturados do documento
        
        Args:
            document: Documento processado
            
        Returns:
            Dados financeiros estruturados
        """
        financial_data = {
            'balance_sheet': {},
            'income_statement': {},
            'cash_flow': {},
            'ratios': {},
            'period': None
        }
        
        # Processa tabelas identificadas
        for table in document['tables']:
            table_type = self._identify_table_type(table)
            
            if table_type == 'balance_sheet':
                financial_data['balance_sheet'] = self._parse_balance_sheet(table)
            elif table_type == 'income_statement':
                financial_data['income_statement'] = self._parse_income_statement(table)
            elif table_type == 'cash_flow':
                financial_data['cash_flow'] = self._parse_cash_flow(table)
                
        # Extrai período
        for date in document['metadata']['extracted_dates']:
            if len(date) == 4 and date.isdigit():
                financial_data['period'] = int(date)
                break
                
        return financial_data
    
    def _identify_table_type(self, table: TableData) -> Optional[str]:
        """Identifica tipo de tabela financeira"""
        headers_text = ' '.join(table.headers).lower()
        first_rows_text = ' '.join([' '.join(row) for row in table.rows[:3]]).lower()
        
        combined_text = headers_text + ' ' + first_rows_text
        
        if any(term in combined_text for term in ['ativo', 'passivo', 'patrimônio']):
            return 'balance_sheet'
        elif any(term in combined_text for term in ['receita', 'lucro', 'resultado']):
            return 'income_statement'
        elif any(term in combined_text for term in ['caixa', 'fluxo']):
            return 'cash_flow'
            
        return None
    
    def _parse_balance_sheet(self, table: TableData) -> Dict[str, Any]:
        """Parseia dados do balanço patrimonial"""
        data = {}
        
        for row in table.rows:
            if len(row) >= 2:
                label = row[0].strip()
                
                # Tenta extrair valor
                for cell in row[1:]:
                    value = self._extract_numeric_value(cell)
                    if value is not None:
                        data[self._normalize_label(label)] = value
                        break
                        
        return data
    
    def _parse_income_statement(self, table: TableData) -> Dict[str, Any]:
        """Parseia dados da DRE"""
        data = {}
        
        for row in table.rows:
            if len(row) >= 2:
                label = row[0].strip()
                
                for cell in row[1:]:
                    value = self._extract_numeric_value(cell)
                    if value is not None:
                        data[self._normalize_label(label)] = value
                        break
                        
        return data
    
    def _parse_cash_flow(self, table: TableData) -> Dict[str, Any]:
        """Parseia dados do fluxo de caixa"""
        data = {}
        
        for row in table.rows:
            if len(row) >= 2:
                label = row[0].strip()
                
                for cell in row[1:]:
                    value = self._extract_numeric_value(cell)
                    if value is not None:
                        data[self._normalize_label(label)] = value
                        break
                        
        return data
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extrai valor numérico de texto"""
        # Remove caracteres não numéricos exceto vírgula, ponto e parênteses
        cleaned = re.sub(r'[^\d.,()\-]', '', text)
        
        # Trata parênteses como negativo
        is_negative = '(' in cleaned
        cleaned = cleaned.replace('(', '').replace(')', '')
        
        # Converte vírgula para ponto
        cleaned = cleaned.replace('.', '').replace(',', '.')
        
        try:
            value = float(cleaned)
            if is_negative:
                value = -value
            return value
        except ValueError:
            return None
    
    def _normalize_label(self, label: str) -> str:
        """Normaliza rótulo para chave"""
        # Remove acentos e caracteres especiais
        normalized = label.lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = normalized.replace(' ', '_')
        
        # Mapeamento de termos comuns
        mappings = {
            'caixa_e_equivalentes': 'caixa',
            'contas_a_receber': 'contas_receber',
            'receita_liquida': 'receita_liquida',
            'lucro_bruto': 'lucro_bruto',
            'lucro_liquido': 'lucro_liquido'
        }
        
        return mappings.get(normalized, normalized)