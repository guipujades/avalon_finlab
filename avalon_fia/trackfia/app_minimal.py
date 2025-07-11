#!/usr/bin/env python3
"""
Aplicação minimal para visualização dos dados do fundo AVALON FIA
Funciona sem pandas/numpy/flask - apenas com bibliotecas Python padrão
"""

import os
import sys
import json
import pickle as pkl
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
import threading
import time

# Adicionar o diretório ao path
sys.path.append(str(Path(__file__).parent))

class AvalonFIATrackerMinimal:
    """Classe minimal para tracking do fundo Avalon FIA"""
    
    def __init__(self):
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        # Usar caminho correto para WSL
        self.pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
        
    def get_fund_data(self):
        """Obtém dados do fundo dos arquivos pickle"""
        # Caminhos dos arquivos pickle
        data_xml_path = self.pickle_dir / f'data_xml_{self.current_date}.pkl'
        header_path = self.pickle_dir / f'header_{self.current_date}.pkl'
        
        # Verifica se arquivos existem
        if header_path.exists() and data_xml_path.exists():
            print(f'📂 Carregando dados do cache para {self.current_date}...')
            with open(data_xml_path, 'rb') as f:
                data_xml = pkl.load(f)
            with open(header_path, 'rb') as f:
                header = pkl.load(f)
            return data_xml, header
        else:
            print(f'❌ Arquivos não encontrados para {self.current_date}')
            return [], {}
                
    def process_portfolio_data_minimal(self):
        """Processa dados do portfolio de forma minimal"""
        # Obter dados do fundo
        data_xml, header = self.get_fund_data()
        
        if not header:
            # Retornar dados padrão se não houver dados
            return self.get_default_data()
        
        # Extrair informações do header
        pl_fundo = header.get('patliq', 0)
        data_dados_raw = header.get('dtposicao', datetime.now())
        
        # Converter data se necessário
        if isinstance(data_dados_raw, str):
            try:
                # Tentar formato YYYYMMDD
                if len(data_dados_raw) == 8:
                    data_dados = datetime.strptime(data_dados_raw, '%Y%m%d').strftime('%d/%m/%Y')
                else:
                    data_dados = data_dados_raw
            except:
                data_dados = data_dados_raw
        else:
            try:
                data_dados = data_dados_raw.strftime('%d/%m/%Y')
            except:
                data_dados = str(data_dados_raw)
        
        cota_fia = header.get('valorcota', 0)
        a_receber = header.get('valorreceber', 0)
        a_pagar = header.get('valorpagar', 0)
        
        # Processar ativos do data_xml
        portfolio_summary = {}
        df_assets = []
        total_ativos_valor = 0
        
        if isinstance(data_xml, list):
            for item in data_xml:
                if isinstance(item, dict):
                    # Extrair dados do ativo
                    codigo = item.get('codigo', 'N/A')
                    tipo = item.get('tipo', 'N/A')
                    quantidade = item.get('quantidade', 0)
                    preco_medio = item.get('preco_medio', 0)
                    valor_fin = item.get('valorfindisp', 0)
                    
                    # Converter para números se forem strings
                    try:
                        quantidade = float(quantidade) if quantidade else 0
                        preco_medio = float(preco_medio) if preco_medio else 0
                        valor_fin = float(valor_fin) if valor_fin else 0
                    except:
                        quantidade = 0
                        preco_medio = 0
                        valor_fin = 0
                    
                    # Adicionar ao resumo por tipo
                    if tipo not in portfolio_summary:
                        portfolio_summary[tipo] = {
                            'count': 0,
                            'total_value': 0
                        }
                    
                    portfolio_summary[tipo]['count'] += 1
                    portfolio_summary[tipo]['total_value'] += valor_fin
                    total_ativos_valor += valor_fin
                    
                    # Adicionar aos ativos individuais
                    df_assets.append({
                        'codigo': codigo,
                        'tipo': tipo,
                        'quantidade': quantidade,
                        'preco_medio': preco_medio,
                        'valorfindisp': valor_fin
                    })
        
        # Calcular métricas básicas
        enquadramento = total_ativos_valor / pl_fundo if pl_fundo > 0 else 0
        
        # Preparar dados finais
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        portfolio_data = {
            'current_time': current_time,
            'data': data_dados,
            'current_pl': float(pl_fundo),
            'cota': float(cota_fia),
            'receber': float(a_receber),
            'pagar': float(a_pagar),
            'enquadramento': float(enquadramento),
            'total_ativos': len(df_assets),
            'total_ativos_valor': float(total_ativos_valor),
            'portfolio_summary': portfolio_summary,
            'df_assets': df_assets,
            # Métricas simplificadas (sem cálculos complexos)
            'limits_der': 0,
            'portfolio_change': 0,
            'portfolio_change_stocks': 0,
            'portfolio_daily_change': 0,
            'portfolio_weekly_change': 0,
            'portfolio_var_1_week': [0, 0, 0],
            'portfolio_var_1_month': [0, 0, 0]
        }
        
        return portfolio_data
        
    def get_default_data(self):
        """Retorna dados padrão quando não há dados disponíveis"""
        return {
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': datetime.now().strftime('%d/%m/%Y'),
            'current_pl': 0,
            'cota': 0,
            'receber': 0,
            'pagar': 0,
            'enquadramento': 0,
            'total_ativos': 0,
            'total_ativos_valor': 0,
            'portfolio_summary': {},
            'df_assets': [],
            'limits_der': 0,
            'portfolio_change': 0,
            'portfolio_change_stocks': 0,
            'portfolio_daily_change': 0,
            'portfolio_weekly_change': 0,
            'portfolio_var_1_week': [0, 0, 0],
            'portfolio_var_1_month': [0, 0, 0]
        }


# Instância global do tracker
tracker = AvalonFIATrackerMinimal()


class PortfolioHandler(BaseHTTPRequestHandler):
    """Handler HTTP para servir dados do portfolio"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.serve_dashboard()
        elif parsed_path.path == '/api/portfolio_data':
            self.serve_portfolio_data()
        elif parsed_path.path == '/api/refresh':
            self.refresh_data()
        else:
            self.send_error(404)
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html_content = self.get_dashboard_html()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_portfolio_data(self):
        """Serve portfolio data as JSON"""
        try:
            portfolio_data = tracker.process_portfolio_data_minimal()
            json_data = json.dumps(portfolio_data, indent=2, ensure_ascii=False)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json_data.encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def refresh_data(self):
        """Force refresh of data"""
        try:
            # Limpar cache seria aqui, mas vamos apenas reprocessar
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'status': 'success', 'message': 'Dados atualizados'}
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def get_dashboard_html(self):
        """Generate dashboard HTML"""
        return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Avalon FIA - Dashboard Minimal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333; 
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
        }
        .header {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .title { 
            font-size: 2.5em; 
            font-weight: 700; 
            color: #2c3e50; 
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle { 
            text-align: center; 
            color: #7f8c8d; 
            font-size: 1.1em;
        }
        .metrics-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 20px; 
            margin: 20px 0;
        }
        .metric-card { 
            background: rgba(255,255,255,0.95);
            padding: 25px; 
            border-radius: 15px; 
            text-align: center;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
            transition: transform 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .metric-title { 
            font-size: 0.9em; 
            color: #7f8c8d; 
            margin-bottom: 10px; 
            text-transform: uppercase; 
            letter-spacing: 1px;
        }
        .metric-value { 
            font-size: 2em; 
            font-weight: 700; 
            color: #2c3e50;
        }
        .portfolio-section {
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .section-title { 
            font-size: 1.5em; 
            margin-bottom: 20px; 
            color: #2c3e50; 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 10px;
        }
        .asset-table { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
        }
        .asset-table th, .asset-table td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #ecf0f1;
        }
        .asset-table th { 
            background: #f8f9fa; 
            font-weight: 600; 
            color: #2c3e50;
        }
        .asset-table tr:hover { 
            background: #f8f9fa;
        }
        .loading { 
            text-align: center; 
            padding: 50px; 
            font-size: 1.2em; 
            color: #7f8c8d;
        }
        .error { 
            background: #e74c3c; 
            color: white; 
            padding: 20px; 
            border-radius: 10px; 
            margin: 20px 0;
        }
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin: 10px;
            transition: background 0.3s ease;
        }
        .refresh-btn:hover { background: #2980b9; }
        .timestamp {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🏦 AVALON FIA</h1>
            <p class="subtitle">Dashboard de Acompanhamento - Versão Minimal</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Atualizar Dados</button>
        </div>
        
        <div id="loading" class="loading">
            Carregando dados do portfolio...
        </div>
        
        <div id="error" class="error" style="display: none;">
            Erro ao carregar dados do portfolio.
        </div>
        
        <div id="content" style="display: none;">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">Patrimônio Líquido</div>
                    <div class="metric-value" id="current-pl">R$ 0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Valor da Cota</div>
                    <div class="metric-value" id="cota-value">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Total de Ativos</div>
                    <div class="metric-value" id="total-assets">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Enquadramento</div>
                    <div class="metric-value" id="enquadramento">0%</div>
                </div>
            </div>
            
            <div class="portfolio-section">
                <h2 class="section-title">📊 Resumo por Tipo de Ativo</h2>
                <div id="portfolio-summary"></div>
            </div>
            
            <div class="portfolio-section">
                <h2 class="section-title">📈 Posições Detalhadas</h2>
                <div id="assets-table"></div>
            </div>
            
            <div class="timestamp" id="timestamp"></div>
        </div>
    </div>

    <script>
        let portfolioData = null;
        
        function formatCurrency(value) {
            return new Intl.NumberFormat('pt-BR', { 
                style: 'currency', 
                currency: 'BRL' 
            }).format(value);
        }
        
        function formatNumber(value) {
            return new Intl.NumberFormat('pt-BR').format(value);
        }
        
        function formatPercentage(value) {
            return (value * 100).toFixed(2) + '%';
        }
        
        async function loadPortfolioData() {
            try {
                document.getElementById('loading').style.display = 'block';
                document.getElementById('error').style.display = 'none';
                document.getElementById('content').style.display = 'none';
                
                const response = await fetch('/api/portfolio_data');
                if (!response.ok) throw new Error('Erro na requisição');
                
                portfolioData = await response.json();
                displayPortfolioData();
                
            } catch (error) {
                console.error('Erro ao carregar dados:', error);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('error').style.display = 'block';
                document.getElementById('content').style.display = 'none';
            }
        }
        
        function displayPortfolioData() {
            if (!portfolioData) return;
            
            // Atualizar métricas principais
            document.getElementById('current-pl').textContent = formatCurrency(portfolioData.current_pl);
            document.getElementById('cota-value').textContent = portfolioData.cota.toFixed(8);
            document.getElementById('total-assets').textContent = portfolioData.total_ativos;
            document.getElementById('enquadramento').textContent = formatPercentage(portfolioData.enquadramento);
            
            // Mostrar resumo por tipo
            displayPortfolioSummary();
            
            // Mostrar tabela de ativos
            displayAssetsTable();
            
            // Timestamp
            document.getElementById('timestamp').textContent = 
                `Última atualização: ${portfolioData.current_time} | Data posição: ${portfolioData.data}`;
            
            // Mostrar conteúdo
            document.getElementById('loading').style.display = 'none';
            document.getElementById('content').style.display = 'block';
        }
        
        function displayPortfolioSummary() {
            const summaryDiv = document.getElementById('portfolio-summary');
            let html = '<div class="metrics-grid">';
            
            for (const [tipo, info] of Object.entries(portfolioData.portfolio_summary)) {
                html += `
                    <div class="metric-card">
                        <div class="metric-title">${tipo.toUpperCase()}</div>
                        <div class="metric-value">${info.count} posições</div>
                        <div style="font-size: 0.9em; color: #7f8c8d; margin-top: 5px;">
                            ${formatCurrency(info.total_value)}
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            summaryDiv.innerHTML = html;
        }
        
        function displayAssetsTable() {
            const tableDiv = document.getElementById('assets-table');
            
            if (!portfolioData.df_assets || portfolioData.df_assets.length === 0) {
                tableDiv.innerHTML = '<p>Nenhum ativo encontrado.</p>';
                return;
            }
            
            let html = `
                <table class="asset-table">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Tipo</th>
                            <th>Quantidade</th>
                            <th>Preço Médio</th>
                            <th>Valor Financeiro</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            // Ordenar por valor financeiro (maior primeiro)
            const sortedAssets = portfolioData.df_assets.sort((a, b) => b.valorfindisp - a.valorfindisp);
            
            for (const asset of sortedAssets) {
                html += `
                    <tr>
                        <td><strong>${asset.codigo}</strong></td>
                        <td>${asset.tipo}</td>
                        <td>${formatNumber(asset.quantidade)}</td>
                        <td>${formatCurrency(asset.preco_medio)}</td>
                        <td>${formatCurrency(asset.valorfindisp)}</td>
                    </tr>
                `;
            }
            
            html += '</tbody></table>';
            tableDiv.innerHTML = html;
        }
        
        async function refreshData() {
            await loadPortfolioData();
        }
        
        // Carregar dados quando a página carrega
        window.addEventListener('load', loadPortfolioData);
        
        // Auto-refresh a cada 5 minutos
        setInterval(loadPortfolioData, 5 * 60 * 1000);
    </script>
</body>
</html>'''

    def log_message(self, format, *args):
        """Override to reduce noise in logs"""
        pass


def run_server(port=5000):
    """Run the HTTP server"""
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, PortfolioHandler)
    print(f"🚀 Servidor iniciado em http://localhost:{port}")
    print("📊 Acesse o dashboard no navegador")
    print("Press Ctrl+C to stop the server")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
        httpd.shutdown()


if __name__ == '__main__':
    print("🏦 Avalon FIA Tracker - Versão Minimal")
    print("=" * 50)
    
    # Testar processamento antes de iniciar servidor
    print("🔍 Testando processamento de dados...")
    try:
        data = tracker.process_portfolio_data_minimal()
        print("✅ Dados processados com sucesso!")
        print(f"  PL: {data['current_pl']:,.2f}")
        print(f"  Total ativos: {data['total_ativos']}")
        print(f"  Tipos: {list(data['portfolio_summary'].keys())}")
        
        # Iniciar servidor
        run_server()
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()