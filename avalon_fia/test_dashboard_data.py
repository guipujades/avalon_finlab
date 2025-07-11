#!/usr/bin/env python3
"""
Testar se o dashboard agora mostra dados de ações
"""

import sys
from pathlib import Path

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent))

def test_dashboard_analytics():
    """Testar os dados que o dashboard receberá"""
    print("🧪 Testando Dados do Dashboard")
    print("=" * 50)
    
    try:
        from trackfia.app_complete import AvalonFIAAnalytics
        
        # Criar instância do analytics
        analytics = AvalonFIAAnalytics()
        
        # Processar dados completos
        data = analytics.process_complete_analytics()
        
        print(f"✅ Analytics processado!")
        print(f"📊 Informações do fundo:")
        print(f"  PL: R$ {data['fund_info']['pl']:,.2f}")
        print(f"  Cota: R$ {data['fund_info']['quota_value']:.8f}")
        print(f"  Data: {data['fund_info']['data_position']}")
        
        print(f"\n📈 Resumo do portfolio:")
        print(f"  Valor total: R$ {data['portfolio_summary']['total_value']:,.2f}")
        print(f"  P&L total: R$ {data['portfolio_summary']['total_pl']:,.2f}")
        print(f"  Retorno: {data['portfolio_summary']['total_return']:.2f}%")
        print(f"  Ações: {data['portfolio_summary']['stocks_count']}")
        print(f"  Opções: {data['portfolio_summary']['options_count']}")
        
        # Verificar ações
        stocks = data.get('stocks', {})
        print(f"\n🎯 Ações no portfolio: {len(stocks)}")
        
        if stocks:
            print("  Top 5 ações por valor:")
            stocks_sorted = sorted(stocks.items(), key=lambda x: x[1].get('current_value', 0), reverse=True)
            for i, (ticker, info) in enumerate(stocks_sorted[:5]):
                valor = info.get('current_value', 0)
                pct = info.get('pcts_port', 0)
                print(f"    {i+1}. {ticker}: R$ {valor:,.2f} ({pct:.2f}%)")
        
        # Verificar se dados chegam limpos (sem NaN)
        print(f"\n🔍 Verificação de dados:")
        sample_stock = next(iter(stocks.values())) if stocks else None
        if sample_stock:
            for key, value in sample_stock.items():
                value_str = str(value).lower()
                if 'nan' in value_str or 'inf' in value_str:
                    print(f"    ⚠️ {key}: {value} (contém NaN/Inf)")
                else:
                    print(f"    ✅ {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_dashboard_analytics()