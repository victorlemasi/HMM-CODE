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
INTERVAL = '1h'  # Hourly data
PERIOD = '60d'   # 60 days lookback

# Clustering settings
N_CLUSTERS = 4

# HMM settings
HMM_COMPONENTS = 3  # Consolidation, Mean Reversion, Trend Breakout
ATR_THRESHOLD_MULTIPLIER = 0.3 # Scale the ATR for thresholding (lowered for less strict guard)

# GPR Integration Settings
GPR_SPIKE_THRESHOLD = 2.0  # Std deviations for a spike
SAFE_HAVEN_TICKER = 'GC=F' # Gold Futures for Safe Haven mode
CORE_ENERGY_TICKER = 'CL=F' # Crude Oil for context

# Asset-Specific HMM Features
COMMODITY_TICKERS = {
    'OIL': 'CL=F',
    'COPPER': 'HG=F',
    'GOLD': 'GC=F'
}
YIELD_TICKERS = {
    'US10Y': '^TNX'
}

ASSET_MAPPINGS = {
    'AUDUSD=X': {'type': 'commodity', 'key': 'COPPER'},
    'USDCAD=X': {'type': 'commodity', 'key': 'OIL'},
    'NZDUSD=X': {'type': 'commodity', 'key': 'GOLD'},
    'USDJPY=X': {'type': 'yield', 'key': 'US10Y'},
    'EURUSD=X': {'type': 'yield', 'key': 'US10Y'},
    'GBPUSD=X': {'type': 'yield', 'key': 'US10Y'}
}
