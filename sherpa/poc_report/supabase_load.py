import yfinance as yf
import pandas as pd
from supabase import create_client

sb = create_client(
    "https://zpfjprlbvkvwvobijznt.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwZmpwcmxidmt2d3ZvYmlqem50Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk2MDI5OTIsImV4cCI6MjA2NTE3ODk5Mn0.oK0k1cMerMUkvwLyggu-vJfdixPhZLvWW39MbQLFDyI"
)


asset = 'BIL'

# Salvar
df = yf.download(asset, start='2020-01-01')
df.columns = df.columns.get_level_values(0)
df.columns.name = None
df.index = pd.to_datetime(df.index)
df['Volume'] = pd.to_numeric(df['Volume']).astype('int64')

json_data = {}
for date in df.index:
    json_data[str(date)] = {
        'open': float(df.loc[date, 'Open']),
        'high': float(df.loc[date, 'High']),
        'low': float(df.loc[date, 'Low']),
        'close': float(df.loc[date, 'Close']),
        'volume': int(df.loc[date, 'Volume'])
    }

sb.table('json_data').upsert({
    'id': asset,
    'data': json_data
}).execute()


# Buscar
seek_asset = 'U03A'
r = sb.table('json_data').select('data').eq('id', seek_asset).execute()
prices = r.data[0]['data']
