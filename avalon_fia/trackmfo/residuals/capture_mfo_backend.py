#!/usr/bin/env python3
"""
Script para capturar e processar dados MFO apenas no backend
Sem necessidade de servidor web
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Adicionar imports necessários
sys.path.append(str(Path(__file__).parent.parent / 'trackfia'))

from capture_mfo_clients_v2 import MFOClientCaptureV2
from mfo_data_receiver import MFODataReceiver
from data_storage import PortfolioDataStorage
from website_integration import WebsiteDataProcessor

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Executa captura e processamento sem servidor web"""
    
    print("=" * 60)
    print("Captura MFO Backend - Sem Interface Web")
    print("=" * 60)
    
    # 1. Capturar dados
    print("\n1. Capturando dados dos clientes...")
    capture = MFOClientCaptureV2()
    clients_data = capture.capture_all_clients(use_cache=False)
    
    if not clients_data:
        print("❌ Nenhum dado capturado")
        return
    
    print(f"✅ {len(clients_data)} clientes capturados")
    
    # 2. Preparar dados
    print("\n2. Preparando dados...")
    formatted_data = capture.prepare_data_for_app(clients_data)
    
    # 3. Processar dados (sem enviar para web)
    print("\n3. Processando dados...")
    storage = PortfolioDataStorage()
    receiver = MFODataReceiver(storage)
    
    # Processar como se tivesse recebido via POST
    result = receiver.receive_data(formatted_data)
    
    if result['status'] == 'success':
        print(f"✅ Dados processados: {result['clients_processed']} clientes")
    else:
        print(f"❌ Erro no processamento: {result.get('message')}")
        return
    
    # 4. Gerar relatórios
    print("\n4. Gerando relatórios...")
    
    # Resumo geral
    summary = receiver.get_processed_summary()
    print("\nResumo do Processamento:")
    print(f"- Total de clientes: {summary['total_clients']}")
    print(f"- Clientes processados: {summary['processed_clients']}")
    print(f"- Patrimônio total: R$ {summary['total_equity']:,.2f}")
    print(f"- Taxa mensal total: R$ {summary['total_monthly_fees']:,.2f}")
    
    # 5. Exportar dados
    print("\n5. Exportando dados...")
    
    # Exportar para Excel
    export_to_excel(receiver, storage)
    
    # Exportar JSONs para análise
    export_to_json(formatted_data, summary)
    
    # 6. Gerar análise de cobranças
    print("\n6. Análise de Cobranças:")
    analyze_fees(receiver, formatted_data)
    
    print("\n" + "=" * 60)
    print("✅ Processo concluído!")
    print(f"Dados salvos em: {storage.base_path}")
    print("=" * 60)


def export_to_excel(receiver, storage):
    """Exporta dados para Excel"""
    try:
        # Criar diretório de saída
        output_dir = Path.home() / 'Desktop' / 'MFO_Reports'
        output_dir.mkdir(exist_ok=True)
        
        # Nome do arquivo com data
        filename = f"MFO_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = output_dir / filename
        
        # Processar dados
        processed_data = receiver._process_all_clients(
            receiver.current_data['clients'],
            receiver.current_data['data_btg']
        )
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Aba 1: Resumo Geral
            summary_data = []
            for client_id, data in processed_data.items():
                if data.get('success'):
                    summary_data.append({
                        'Cliente ID': client_id,
                        'Patrimônio Total': data['total_equity'],
                        'Taxa Gestão (%)': data['tx_gestao'],
                        'Cobrança Mensal': data['cobranca_info']['tx_mes'],
                        'Tem Avalon FIA': 'Sim' if data['cobranca_info']['tem_avalon_fia'] else 'Não',
                        'Valor Avalon FIA': data['cobranca_info'].get('investimento_avalon_fia', 0)
                    })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Aba 2: Detalhamento por Cliente
            for client_id, data in processed_data.items():
                if data.get('success') and len(str(client_id)) < 31:  # Excel limit
                    client_sheet = f"Cliente_{client_id}"[:31]
                    
                    # Criar DataFrame com posições
                    positions = []
                    
                    # Processar cada tipo de ativo
                    for asset_type, df in data['dataframes'].items():
                        if isinstance(df, pd.DataFrame) and not df.empty:
                            for _, row in df.iterrows():
                                positions.append({
                                    'Tipo': asset_type,
                                    'Nome': row.get('FundName', row.get('Issuer', row.get('Ticker', 'N/A'))),
                                    'Valor': row.get('GrossAssetValue', row.get('GrossValue', row.get('Value', 0)))
                                })
                    
                    if positions:
                        positions_df = pd.DataFrame(positions)
                        positions_df.to_excel(writer, sheet_name=client_sheet, index=False)
        
        print(f"✅ Relatório Excel salvo em: {filepath}")
        
    except Exception as e:
        print(f"❌ Erro ao exportar Excel: {e}")


def export_to_json(formatted_data, summary):
    """Exporta dados para JSON"""
    try:
        output_dir = Path.home() / 'Desktop' / 'MFO_Reports'
        output_dir.mkdir(exist_ok=True)
        
        # Dados completos
        full_data_file = output_dir / f"MFO_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(full_data_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, ensure_ascii=False, indent=2)
        
        # Resumo
        summary_file = output_dir / f"MFO_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Dados JSON salvos em: {output_dir}")
        
    except Exception as e:
        print(f"❌ Erro ao exportar JSON: {e}")


def analyze_fees(receiver, formatted_data):
    """Analisa cobranças e taxas"""
    try:
        # Processar dados
        processed_data = receiver._process_all_clients(
            formatted_data['clients'],
            formatted_data['data_btg']
        )
        
        # Calcular totais
        total_patrimonio = 0
        total_cobranca = 0
        total_avalon = 0
        clientes_com_avalon = 0
        
        for client_id, data in processed_data.items():
            if data.get('success'):
                total_patrimonio += data['total_equity']
                total_cobranca += data['cobranca_info']['tx_mes']
                
                if data['cobranca_info']['tem_avalon_fia']:
                    clientes_com_avalon += 1
                    total_avalon += data['cobranca_info']['investimento_avalon_fia']
        
        print(f"\nTotais:")
        print(f"- Patrimônio total sob gestão: R$ {total_patrimonio:,.2f}")
        print(f"- Cobrança mensal total: R$ {total_cobranca:,.2f}")
        if total_patrimonio > 0:
            print(f"- Taxa média: {(total_cobranca * 12 / total_patrimonio * 100):.2f}% ao ano")
        else:
            print(f"- Taxa média: N/A (sem patrimônio)")
        print(f"\nAvalon FIA:")
        print(f"- Clientes investidos: {clientes_com_avalon}")
        print(f"- Total investido: R$ {total_avalon:,.2f}")
        if total_patrimonio > 0:
            print(f"- % do patrimônio total: {(total_avalon / total_patrimonio * 100):.2f}%")
        else:
            print(f"- % do patrimônio total: N/A")
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")


if __name__ == '__main__':
    main()