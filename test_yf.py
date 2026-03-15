import yfinance as yf
try:
    df = yf.download('EURUSD=X', interval='1h', period='6mo')
    print("Download Result:")
    print(df.head())
    print("Columns:", df.columns.tolist())
except Exception as e:
    print(f"Error: {e}")
