#!/usr/bin/env python3
"""
Testar apenas os dados core sem Flask
"""

import sys
from pathlib import Path

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent))

def test_core_data():
    """Testar dados core"""
    print("🧪 Testando Dados Core")
    print("=" * 50)
    
    try:
        from trackfia.portfolio_processor_fixed import process_portfolio_from_api_fixed
        
        # Processar dados
        portfolio_data = process_portfolio_from_api_fixed()
        
        if portfolio_data:
            positions = portfolio_data.get('positions', {})
            stocks = portfolio_data.get('stocks', {})
            header = portfolio_data.get('header', {})
            
            print(f"✅ Dados processados!")
            print(f"📊 PL: R$ {header.get('patliq', 0):,.2f}")
            print(f"📊 Cota: R$ {header.get('valorcota', 0):.8f}")
            print(f"📈 Total posições: {len(positions)}")
            print(f"🎯 Ações: {len(stocks)}")
            
            # Verificar ações com valor > 0
            stocks_with_value = {k: v for k, v in stocks.items() if v.get('current_value', 0) > 0}
            print(f"💰 Ações com valor > 0: {len(stocks_with_value)}")
            
            if stocks_with_value:
                print("\n📋 Top 5 ações:")
                sorted_stocks = sorted(stocks_with_value.items(), 
                                     key=lambda x: x[1].get('current_value', 0), 
                                     reverse=True)
                
                for ticker, data in sorted_stocks[:5]:
                    print(f"  {ticker}:")
                    print(f"    Qtd: {data.get('quantity', 0)}")
                    print(f"    Preço: R$ {data.get('current_price', 0):.2f}")
                    print(f"    Valor: R$ {data.get('current_value', 0):,.2f}")
                    print(f"    % Port: {data.get('pcts_port', 0):.2f}%")
                    
                    # Verificar NaN
                    for key, value in data.items():
                        if str(value).lower() in ['nan', 'inf', '-inf'] or (isinstance(value, float) and str(value) == 'nan'):
                            print(f"    ⚠️ {key} contém NaN!")
                
                return True
            else:
                print("❌ Nenhuma ação com valor encontrada")
                return False
        else:
            print("❌ Falha ao processar dados")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_core_data()