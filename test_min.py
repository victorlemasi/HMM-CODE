import yfinance as yf
try:
    print("Testing minimal download...")
    df = yf.download('EURUSD=X', period='1d', interval='1h')
    if not df.empty:
        print("Success! Data received.")
        print(df.tail())
    else:
        print("Failed: Empty DataFrame received even for 1d.")
except Exception as e:
    print(f"Error during minimal download: {e}")
