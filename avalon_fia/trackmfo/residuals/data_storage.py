"""
Sistema de armazenamento estruturado para dados de portfolios
Gerencia salvamento, carregamento e organização de dados capturados
"""

import json
import pickle
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PortfolioDataStorage:
    """Gerenciador de armazenamento de dados de portfolios"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Inicializa o sistema de armazenamento
        
        Args:
            base_path: Caminho base para armazenamento
        """
        if base_path is None:
            base_path = Path.home() / 'Documents' / 'GitHub' / 'database' / 'portfolio_data'
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Subdiretórios organizados
        self.raw_data_path = self.base_path / 'raw'
        self.processed_data_path = self.base_path / 'processed'
        self.reports_path = self.base_path / 'reports'
        self.db_path = self.base_path / 'portfolio.db'
        
        # Criar subdiretórios
        for path in [self.raw_data_path, self.processed_data_path, self.reports_path]:
            path.mkdir(exist_ok=True)
        
        # Inicializar banco de dados
        self._init_database()
    
    def _init_database(self):
        """Inicializa estrutura do banco de dados SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de portfolios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                cnpj TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de capturas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id TEXT NOT NULL,
                capture_date TIMESTAMP NOT NULL,
                status TEXT NOT NULL,
                file_path TEXT,
                total_value REAL,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
        ''')
        
        # Tabela de posições
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capture_id INTEGER NOT NULL,
                asset_type TEXT NOT NULL,
                asset_name TEXT NOT NULL,
                ticker TEXT,
                quantity REAL,
                unit_price REAL,
                total_value REAL,
                percentage REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (capture_id) REFERENCES captures(id)
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_captures_portfolio ON captures(portfolio_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_captures_date ON captures(capture_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_capture ON positions(capture_id)')
        
        conn.commit()
        conn.close()
    
    def save_portfolio_info(self, portfolio_id: str, info: Dict):
        """
        Salva informações de um portfolio
        
        Args:
            portfolio_id: ID único do portfolio
            info: Informações do portfolio
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO portfolios (id, name, type, cnpj, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            portfolio_id,
            info.get('name', 'Unknown'),
            info.get('type', 'Unknown'),
            info.get('cnpj'),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def save_capture(self, portfolio_id: str, capture_data: Dict) -> int:
        """
        Salva dados de uma captura
        
        Args:
            portfolio_id: ID do portfolio
            capture_data: Dados da captura
            
        Returns:
            ID da captura salva
        """
        timestamp = datetime.now()
        
        # Salvar arquivo raw
        raw_file = self._save_raw_data(portfolio_id, capture_data, timestamp)
        
        # Registrar no banco
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO captures (
                portfolio_id, capture_date, status, file_path, 
                total_value, error_message
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            portfolio_id,
            capture_data.get('capture_date', timestamp),
            'success' if capture_data.get('success') else 'failed',
            str(raw_file),
            self._calculate_total_value(capture_data),
            capture_data.get('error') if not capture_data.get('success') else None
        ))
        
        capture_id = cursor.lastrowid
        
        # Salvar posições se houver
        if capture_data.get('success') and 'data' in capture_data:
            self._save_positions(cursor, capture_id, capture_data['data'])
        
        conn.commit()
        conn.close()
        
        return capture_id
    
    def _save_raw_data(self, portfolio_id: str, data: Dict, timestamp: datetime) -> Path:
        """Salva dados brutos em arquivo"""
        filename = f"{portfolio_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pkl"
        file_path = self.raw_data_path / filename
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        
        return file_path
    
    def _save_positions(self, cursor, capture_id: int, data: Dict):
        """Salva posições individuais no banco"""
        # Implementar parsing específico por tipo de dado
        # Por enquanto, versão simplificada
        
        positions = []
        
        # Se for dados processados do MFO
        if isinstance(data, tuple) and len(data) >= 12:
            # Processar cada DataFrame retornado pelo process_account_data
            dataframes = data[:11]  # Os primeiros 11 elementos são DataFrames
            
            for i, df in enumerate(dataframes):
                if isinstance(df, pd.DataFrame) and not df.empty:
                    asset_type = self._get_asset_type_from_index(i)
                    
                    for _, row in df.iterrows():
                        positions.append({
                            'asset_type': asset_type,
                            'asset_name': row.get('FundName', row.get('Issuer', row.get('Ticker', 'Unknown'))),
                            'ticker': row.get('Ticker'),
                            'total_value': row.get('GrossAssetValue', row.get('GrossValue', row.get('Value', 0))),
                        })
        
        # Inserir posições no banco
        for pos in positions:
            cursor.execute('''
                INSERT INTO positions (
                    capture_id, asset_type, asset_name, ticker, 
                    quantity, unit_price, total_value, percentage
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                capture_id,
                pos.get('asset_type', 'Unknown'),
                pos.get('asset_name', 'Unknown'),
                pos.get('ticker'),
                pos.get('quantity'),
                pos.get('unit_price'),
                pos.get('total_value', 0),
                pos.get('percentage', 0)
            ))
    
    def _get_asset_type_from_index(self, index: int) -> str:
        """Mapeia índice do DataFrame para tipo de ativo"""
        mapping = {
            0: 'Fundos',
            1: 'Renda Fixa',
            2: 'COE',
            3: 'Ações',
            4: 'Derivativos',
            5: 'Commodities',
            6: 'Crypto',
            7: 'Caixa',
            8: 'Previdência',
            9: 'Créditos',
            10: 'Valores em Trânsito'
        }
        return mapping.get(index, 'Outros')
    
    def _calculate_total_value(self, capture_data: Dict) -> float:
        """Calcula valor total do portfolio"""
        if not capture_data.get('success'):
            return 0.0
        
        # Implementar cálculo baseado nos dados
        # Por enquanto, retornar 0
        return 0.0
    
    def get_latest_capture(self, portfolio_id: str) -> Optional[Dict]:
        """
        Obtém a captura mais recente de um portfolio
        
        Args:
            portfolio_id: ID do portfolio
            
        Returns:
            Dados da captura ou None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, capture_date, status, file_path, total_value
            FROM captures
            WHERE portfolio_id = ? AND status = 'success'
            ORDER BY capture_date DESC
            LIMIT 1
        ''', (portfolio_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Carregar dados do arquivo
            file_path = Path(row[3])
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                return data
        
        return None
    
    def get_portfolio_history(self, portfolio_id: str, days: int = 30) -> pd.DataFrame:
        """
        Obtém histórico de um portfolio
        
        Args:
            portfolio_id: ID do portfolio
            days: Número de dias de histórico
            
        Returns:
            DataFrame com histórico
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT capture_date, total_value, status
            FROM captures
            WHERE portfolio_id = ?
                AND capture_date >= datetime('now', '-{} days')
            ORDER BY capture_date
        '''.format(days)
        
        df = pd.read_sql_query(query, conn, params=(portfolio_id,))
        conn.close()
        
        return df
    
    def get_all_portfolios(self) -> pd.DataFrame:
        """
        Obtém lista de todos os portfolios
        
        Returns:
            DataFrame com portfolios
        """
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM portfolios', conn)
        conn.close()
        
        return df
    
    def generate_portfolio_report(self, portfolio_id: str) -> Path:
        """
        Gera relatório de um portfolio
        
        Args:
            portfolio_id: ID do portfolio
            
        Returns:
            Caminho do relatório gerado
        """
        timestamp = datetime.now()
        report_file = self.reports_path / f"{portfolio_id}_report_{timestamp.strftime('%Y%m%d')}.xlsx"
        
        with pd.ExcelWriter(report_file, engine='openpyxl') as writer:
            # Informações do portfolio
            conn = sqlite3.connect(self.db_path)
            
            # Info geral
            portfolio_info = pd.read_sql_query(
                'SELECT * FROM portfolios WHERE id = ?',
                conn, params=(portfolio_id,)
            )
            portfolio_info.to_excel(writer, sheet_name='Info', index=False)
            
            # Histórico de capturas
            history = pd.read_sql_query(
                'SELECT * FROM captures WHERE portfolio_id = ? ORDER BY capture_date DESC',
                conn, params=(portfolio_id,)
            )
            history.to_excel(writer, sheet_name='Histórico', index=False)
            
            # Última posição
            latest_capture = pd.read_sql_query('''
                SELECT p.*
                FROM positions p
                JOIN captures c ON p.capture_id = c.id
                WHERE c.portfolio_id = ?
                ORDER BY c.capture_date DESC
                LIMIT 100
            ''', conn, params=(portfolio_id,))
            latest_capture.to_excel(writer, sheet_name='Posições Atuais', index=False)
            
            conn.close()
        
        logger.info(f"Relatório gerado: {report_file}")
        return report_file
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Remove dados antigos
        
        Args:
            days_to_keep: Dias para manter
        """
        cutoff_date = datetime.now() - pd.Timedelta(days=days_to_keep)
        
        # Limpar arquivos antigos
        for path in [self.raw_data_path, self.processed_data_path]:
            for file in path.glob('*.pkl'):
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff_date:
                    file.unlink()
                    logger.info(f"Arquivo removido: {file}")
        
        # Limpar registros do banco
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM positions
            WHERE capture_id IN (
                SELECT id FROM captures
                WHERE capture_date < ?
            )
        ''', (cutoff_date,))
        
        cursor.execute('''
            DELETE FROM captures
            WHERE capture_date < ?
        ''', (cutoff_date,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Limpeza concluída. Dados anteriores a {cutoff_date} removidos.")


def main():
    """Função de teste"""
    storage = PortfolioDataStorage()
    
    # Testar salvamento
    storage.save_portfolio_info('test_portfolio', {
        'name': 'Portfolio de Teste',
        'type': 'fund',
        'cnpj': '12345678901234'
    })
    
    # Listar portfolios
    portfolios = storage.get_all_portfolios()
    print("Portfolios cadastrados:")
    print(portfolios)


if __name__ == '__main__':
    main()