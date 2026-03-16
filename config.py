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
HMM_N_ITER = 5000   # Increased from 1000 for convergence
HMM_COVARS_PRIOR = 1e-2 # Bayesian prior for stability
HMM_MIN_COVAR = 1e-2    # Prevent numerical instability/collapse
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
    'DXY': 'DX-Y.NYB',
    'NZ10Y_LIVE': '^NZ10'
}

FRED_TICKERS = {
    'NZ10Y': 'IRLTLT01NZM156N',
    'NZ_OCR': 'IRSTCI01NZM156N',
    'UK10Y': 'IRLTLT01GBM156N',  # UK Government Bond Yield (Long-term)
    'GER10Y': 'IRLTLT01DEM156N', # Germany Government Bond Yield (Long-term)
    'UK_GILT_2Y': 'IUKG2',       # 2Y Gilt proxy
    'US_TIPS_10Y': 'DFII10',      # 10Y Real Yield
    'AUD10Y': 'IRLTLT01AUM156N'  # Australia 10Y Bond Yield
}

# Macro Filter Settings
MAJORS_MACRO_ENABLE = True
YIELD_THRESHOLD = 0.05  # Minimum bps change to consider it a "Macro Trend"

# Central Bank Policy Rates (FRED Tickers)
POLICY_RATE_TICKERS = {
    'USD': 'FEDFUNDS',
    'EUR': 'ECBMRRFR',
    'GBP': 'IRLTLT01GBM156N',
    'JPY': 'IRSTCI01JPM156N',
    'AUD': 'IRSTCI01AUM156N',
    'CAD': 'IRSTCI01CAM156N',
    'NZD': 'IRSTCI01NZM156N'
}

FRED_2Y_TICKERS = {
    'US2Y': 'GS2',        
    'GER2Y': 'IRLTLT01DEM156N', 
    'UK2Y': 'IRLTLT01GBM156N'
}

FRED_2Y_TICKERS = {
    'US2Y': 'GS2',        
    'GER2Y': 'IRLTLT01DEM156N', 
    'UK2Y': 'IRLTLT01GBM156N'
}

# 1-minute Watchdog Tickers
WATCHDOG_TICKERS = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'GC=F', 'CL=F']
WATCHDOG_JUMP_THRESHOLDS = {
    'CL=F': 4.5,   # Oil is more volatile, higher threshold
    'GC=F': 3.5,   # Gold threshold
    'DEFAULT': 3.0 # FX default
}

ASSET_MAPPINGS = {
    'USDCAD=X': {'type': 'commodity', 'key': 'OIL'},
    'USDJPY=X': {'type': 'yield', 'key': 'US10Y'},
    'EURUSD=X': {'type': 'macro', 'base': 'GER10Y', 'quote': 'US10Y'},
    'GBPUSD=X': {'type': 'macro', 'base': 'UK10Y', 'quote': 'US10Y'},
    'CL=F':     {'type': 'commodity_inverse', 'key': 'DXY'} # Oil inverse to Dollar
}

# Asset-Specific HMM Components
ASSET_N_COMPONENTS = {
    'GC=F': 4,   # Gold: Consolidation, Mean Reversion, Trend, Safe Haven Spike
    'DEFAULT': 3
}

# 1.2 Candle Logic for Majors
MAJORS_FIX_LIST = ['EURUSD=X', 'GBPUSD=X']
EURUSD_FIX_LIST = ['EURUSD=X']
CONFIRMATION_BUFFER = 0.2
MAJORS_TP_MULTIPLIER = 3.0
BB_SQUEEZE_THRESHOLD = 0.05 # EURUSD only breakouts if squeeze < 5% of price
TIPS_TICKER = 'DFII10' # FRED Real Yield
COMMODITY_MACRO_ENABLE = True

# EFFICIENCY EQUILIBRIUM OVERRIDES
MAJORS_MIN_CONFIDENCE = 0.85
MAJORS_SL_ATR = 2.5
SAR_PARAMS = {'start': 0.02, 'max': 0.2}

# Kill Zone Windows (UTC)
KILL_ZONES = [
    (7, 11),  # London Open
    (13, 17)  # NY Open / Overlap
]
LUNCH_ZONE = (11, 13) # London Lunch (Lull Penalty)
