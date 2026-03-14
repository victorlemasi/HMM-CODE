# List of 20 major and minor currency pairs
CURRENCY_PAIRS = [
    'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'USDCHF=X', 'AUDUSD=X',
    'USDCAD=X', 'NZDUSD=X', 'EURGBP=X', 'EURJPY=X', 'GBPJPY=X',
    'EURCHF=X', 'GBPCHF=X', 'AUDJPY=X', 'NZDJPY=X', 'CHFJPY=X',
    'EURAUD=X', 'EURNZD=X', 'GBPAUD=X', 'GBPNZD=X', 'AUDNZD=X',
    'GC=F',   # Gold Futures (Safe Haven)
    'CL=F'    # Crude Oil (Geopolitical Context)
]

# Timeframe for analysis
# Timeframe for analysis
INTERVAL = '1h'  # Hourly data
PERIOD = '70d'   # 70 days lookback to ensure ~1000-1200 bars

# Clustering settings
N_CLUSTERS = 4

# HMM settings
HMM_COMPONENTS = 3  # Consolidation, Mean Reversion, Trend Breakout
ATR_MULTIPLIER_FX = 0.15 
ATR_MULTIPLIER_GOLD = 0.2

# GPR Integration Settings
GPR_SPIKE_THRESHOLD = 2.0  # Std deviations for a spike
SAFE_HAVEN_TICKER = 'GC=F' # Gold Futures for Safe Haven mode
CORE_ENERGY_TICKER = 'CL=F' # Crude Oil for context

# Asset-Specific HMM Features
COMMODITY_TICKERS = {
    'OIL': 'CL=F',
    'BRENT': 'BZ=F',
    'COPPER': 'HG=F',
    'GOLD': 'GC=F'
}
YIELD_TICKERS = {
    'US10Y': '^TNX',
    'UK10Y': 'GB10YT=RR',
    'GER10Y': 'DE10YT=RR',
    'DXY': 'DX-Y.NYB',
    'NZ10Y_LIVE': '^NZ10'
}

FRED_TICKERS = {
    'NZ10Y': 'IRLTLT01NZM156N',
    'NZ_OCR': 'IRSTCI01NZM156N'
}

# Macro Filter Settings
MAJORS_MACRO_ENABLE = True
YIELD_THRESHOLD = 0.05  # Minimum bps change to consider it a "Macro Trend"

ASSET_MAPPINGS = {
    'AUDUSD=X': {'type': 'commodity', 'key': 'COPPER'},
    'USDCAD=X': {'type': 'commodity', 'key': 'OIL'},
    'NZDUSD=X': {'type': 'commodity', 'key': 'GOLD'},
    'USDJPY=X': {'type': 'yield', 'key': 'US10Y'},
    'EURUSD=X': {'type': 'macro', 'base': 'GER10Y', 'quote': 'US10Y'},
    'GBPUSD=X': {'type': 'macro', 'base': 'UK10Y', 'quote': 'US10Y'}
}

# 1.2 Candle Logic for Majors
MAJORS_FIX_LIST = ['EURUSD=X', 'GBPUSD=X']
CONFIRMATION_BUFFER = 0.2
MAJORS_TP_MULTIPLIER = 3.0
