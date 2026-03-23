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
PERIOD = '70d'   # Lookback for live fitting (~1000-1200 bars)
HMM_TRAIN_PERIOD = '365d' # Shortened to 1 year for better recent regime adaptation
HMM_TRAIN_CORES = 4    # Parallel training workers

# Clustering settings
N_CLUSTERS = 4

# HMM settings
HMM_COMPONENTS = 3  # Consolidation, Mean Reversion, Trend Breakout
HMM_N_ITER = 1000   # Reset to 1000 now that covar floor is lowered
HMM_FINE_TUNE_ITER_FX = 15 # Baseline stability for FX
HMM_FINE_TUNE_ITER_COMM = 10 # Adaptability for Commodities
HMM_COVARS_PRIOR = 1e-2
HMM_MIN_COVAR = 1e-2
ATR_MULTIPLIER_FX = 0.25 # Lowered for discovery (was 0.50)
ATR_MULTIPLIER_GOLD = 0.40 # Lowered for discovery (was 0.75)

# HMM Persistence
HMM_MODELS_PATH = 'hmm_models'
HMM_USE_PRETRAINED = True # Set to False to rely on live fitting

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
    'DXY': 'DX-Y.NYB',
    'TLT': 'TLT'         # 20+ Year Treasury Bond ETF (Real-time Yield Proxy)
}

FRED_TICKERS = {
    'US10Y': 'DGS10',            # USA 10Y (Daily)
    'GER10Y': 'IRLTLT01DEM156N', # Germany 10Y (Monthly)
    'UK10Y': 'IRLTLT01GBM156N',  # UK 10Y (Monthly)
    'JPY10Y': 'IRLTLT01JPM156N', # Japan 10Y (Monthly)
    'CHF10Y': 'IRLTLT01CHM156N', # Switzerland 10Y (Monthly)
    'AUD10Y': 'IRLTLT01AUM156N', # Australia 10Y (Monthly)
    'CAD10Y': 'IRLTLT01CAM156N', # Canada 10Y (Monthly)
    'NZ10Y': 'IRLTLT01NZM156N',  # NZ 10Y (Monthly)
    'US_TIPS_10Y': 'DFII10',     # 10Y Real Yield
}

# Macro Filter Settings
MAJORS_MACRO_ENABLE = True
YIELD_THRESHOLD = 0.15  # Drastically widened to ignore US yield noise

# Central Bank Policy Rates (FRED Tickers — only reliably accessible series)
# Tickers that 404 or timeout are omitted; those pairs default to ALLOW for rate bias.
POLICY_RATE_TICKERS = {
    'USD': 'FEDFUNDS',  # Federal Reserve (reliable daily)
    'EUR': 'ECBMRRFR', # ECB Main Refinancing Operations Rate (reliable)
    'GBP': 'CH0000000100', # UK Rate Proxy
    'AUD': 'RBATCTR',      # Australia Cash Rate
    'NZD': 'NZDRINTERNET', # NZ Cash Rate
    'JPY': 'IRSTCI01JPM156N' # Japan Short-Term Rate
}

# --- v6.1 TACTICAL: FIXED RATES (2026 Calibrated) ---
POLICY_RATES_2026 = {
    'USD': 5.25, 'EUR': 4.00, 'GBP': 5.00, 'AUD': 4.35,
    'NZD': 5.50, 'JPY': 0.10, 'CHF': 1.50, 'CAD': 5.00
}

# --- VERSION CONTROL ---
STRATEGY_VERSION = "v7.0"
STRATEGY_CODENAME = "THE ENGINE SWAP"

# v7.0 ENGINE SPECIFICATIONS
V7_DYNAMIC_SCALING = True
V7_ROLLING_WINDOW = 500
V7_FORCE_LOOKBACK = 5

# --- v6.1 TACTICAL: LIQUIDITY MAPPING (UTC) ---
LIQUIDITY_MAP = {
    'EURUSD=X': {'active': (7, 18), 'floor': 0.45},
    'GBPUSD=X': {'active': (7, 18), 'floor': 0.45},
    'USDJPY=X': {'active': (0, 9),  'floor': 0.45},
    'AUDUSD=X': {'active': (22, 7), 'floor': 0.45},
    'DEFAULT':  {'active': (0, 24), 'floor': 0.40}
}


FRED_2Y_TICKERS = {
    'US2Y': 'GS2',        
    'GER2Y': 'IRLTLT01DEM156N', # Proxy (10Y) if 2Y is not available daily
    'UK2Y': 'IRLTLT01GBM156N'  # UK 10Y (Placeholder proxy, better than 404)
}

# 1-minute Watchdog Tickers
WATCHDOG_TICKERS = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'GC=F', 'CL=F']
WATCHDOG_JUMP_THRESHOLDS = {
    'CL=F': 4.5,   # Oil is more volatile, higher threshold
    'GC=F': 3.5,   # Gold threshold
    'DEFAULT': 3.0 # FX default
}

ASSET_MAPPINGS = {
    # Majors
    'EURUSD=X': {'type': 'macro', 'base': 'GER10Y', 'quote': 'US10Y', 'base_currency': 'EUR', 'quote_currency': 'USD'},
    'GBPUSD=X': {'type': 'macro', 'base': 'UK10Y', 'quote': 'US10Y', 'base_currency': 'GBP', 'quote_currency': 'USD'},
    'USDJPY=X': {'type': 'macro', 'base': 'US10Y', 'quote': 'JPY10Y', 'base_currency': 'USD', 'quote_currency': 'JPY'},
    'USDCHF=X': {'type': 'macro', 'base': 'US10Y', 'quote': 'CHF10Y', 'base_currency': 'USD', 'quote_currency': 'CHF'},
    'AUDUSD=X': {'type': 'macro', 'base': 'AUD10Y', 'quote': 'US10Y', 'base_currency': 'AUD', 'quote_currency': 'USD'},
    'USDCAD=X': {'type': 'macro', 'base': 'US10Y', 'quote': 'CAD10Y', 'base_currency': 'USD', 'quote_currency': 'CAD'},
    'NZDUSD=X': {'type': 'macro', 'base': 'NZ10Y', 'quote': 'US10Y', 'base_currency': 'NZD', 'quote_currency': 'USD'},
    
    # Minors / Crosses
    'EURGBP=X': {'type': 'macro', 'base': 'GER10Y', 'quote': 'UK10Y', 'base_currency': 'EUR', 'quote_currency': 'GBP'},
    'EURJPY=X': {'type': 'macro', 'base': 'GER10Y', 'quote': 'JPY10Y', 'base_currency': 'EUR', 'quote_currency': 'JPY'},
    'GBPJPY=X': {'type': 'macro', 'base': 'UK10Y', 'quote': 'JPY10Y', 'base_currency': 'GBP', 'quote_currency': 'JPY'},
    'EURCHF=X': {'type': 'macro', 'base': 'GER10Y', 'quote': 'CHF10Y', 'base_currency': 'EUR', 'quote_currency': 'CHF'},
    'GBPCHF=X': {'type': 'macro', 'base': 'UK10Y', 'quote': 'CHF10Y', 'base_currency': 'GBP', 'quote_currency': 'CHF'},
    'AUDJPY=X': {'type': 'macro', 'base': 'AUD10Y', 'quote': 'JPY10Y', 'base_currency': 'AUD', 'quote_currency': 'JPY'},
    'NZDJPY=X': {'type': 'macro', 'base': 'NZ10Y', 'quote': 'JPY10Y', 'base_currency': 'NZD', 'quote_currency': 'JPY'},
    'CHFJPY=X': {'type': 'macro', 'base': 'CHF10Y', 'quote': 'JPY10Y', 'base_currency': 'CHF', 'quote_currency': 'JPY'},
    'EURAUD=X': {'type': 'macro', 'base': 'GER10Y', 'quote': 'AUD10Y', 'base_currency': 'EUR', 'quote_currency': 'AUD'},
    'EURNZD=X': {'type': 'macro', 'base': 'GER10Y', 'quote': 'NZ10Y', 'base_currency': 'EUR', 'quote_currency': 'NZD'},
    'GBPAUD=X': {'type': 'macro', 'base': 'UK10Y', 'quote': 'AUD10Y', 'base_currency': 'GBP', 'quote_currency': 'AUD'},
    'GBPNZD=X': {'type': 'macro', 'base': 'UK10Y', 'quote': 'NZ10Y', 'base_currency': 'GBP', 'quote_currency': 'NZD'},
    'AUDNZD=X': {'type': 'macro', 'base': 'AUD10Y', 'quote': 'NZ10Y', 'base_currency': 'AUD', 'quote_currency': 'NZD'},
    
    # Commodities
    'GC=F':     {'type': 'commodity', 'key': 'GOLD'},
    'CL=F':     {'type': 'commodity_inverse', 'key': 'DXY'} # Oil inverse to Dollar
}

# Asset-Specific HMM Components
ASSET_N_COMPONENTS = {
    'DEFAULT': 3,
    'GC=F': 4, # Gold needs 4 states for Safe Haven Spikes
    'CL=F': 3
}

# TIGHTENED THRESHOLDS for v5.8 precision
MAJORS_MIN_CONFIDENCE = 0.45 
MINORS_MIN_CONFIDENCE = 0.50 
HMM_STATE_DELTA_THRESHOLD = 0.02 
ATR_VOL_CEILING = 3.50        
MAJORS_FIX_LIST = ['EURUSD=X', 'GBPUSD=X']
EURUSD_FIX_LIST = ['EURUSD=X']
CONFIRMATION_BUFFER = 0.2
MAJORS_TP_MULTIPLIER = 3.0
ATR_SL_MULTIPLIER = 1.5
ATR_CHANDELIER_TRAIL = 2.5
BB_SQUEEZE_THRESHOLD = 0.05 
TIPS_TICKER = 'DFII10' 
COMMODITY_MACRO_ENABLE = True

# Kill Zone Windows (UTC)
KILL_ZONES = [
    (7, 11),  # London Open
    (13, 17)  # NY Open / Overlap
]
LUNCH_ZONE = (11, 13) 
