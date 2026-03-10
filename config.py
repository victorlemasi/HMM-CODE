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
HMM_COMPONENTS = 3  # Stable, Trend, Breakout

# GPR Integration Settings
GPR_SPIKE_THRESHOLD = 2.0  # Std deviations for a spike
SAFE_HAVEN_TICKER = 'GC=F' # Gold Futures for Safe Haven mode
CORE_ENERGY_TICKER = 'CL=F' # Crude Oil for context
