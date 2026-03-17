# Currency Pair Scanner & Analysis (Unified Macro-Quant)

A high-sophistication quantitative scanner designed for the structural volatility of 2026. It integrates multi-dimensional **Hidden Markov Models (HMM)**, real-time **Macro-Economic Intelligence (FRED)**, and **Regime-Aware Risk Protection** to identify and validate high-conviction breakout opportunities.

## 🚀 Key Features

- **End-to-End Macro Pipeline**: Automated data fetching from **FRED** (St. Louis Fed) and **Yahoo Finance**. Captures 10Y Benchmark Yields and Central Bank Policy Rates (Fed Funds, ECB Rate).
- **Fundamental Gatekeeper (Bouncer)**: Hybrid filtering using **Yield Spread Momentum** (aligned mixed frequencies) and **Policy Rate Differentials**.
- **Regime Detection (HMM)**: Analyzes Log-Volatility and Returns across 3 states: *Consolidation*, *Mean Reversion*, and *Trend Breakout*.
- **Defensive Strike (1.2 Candle Logic)**: Specialized entry mechanism for major pairs (EURUSD, GBPUSD) that requires 1.2x ATR breakout confirmation to avoid "Trap Phases."
- **War-Time Asset Guard**: Treats Gold (`GC=F`) and Oil (`CL=F`) as macro volatility sensors with strict time-exits (4h/8h) and Mahalanobis jump detection.
- **Diversification Engine**: Automated correlation clustering (K-Means) and rebalancing to prevent over-exposure to linked currency themes.

## 🧠 Sophisticated Logic Framework

### 1. The Macro Gatekeeper (`macro_bouncer.py`)
Technical signals are subjected to a rigorous fundamental validation suite:
- **Yield Spread Momentum**: Compares 10Y benchmark yield differentials (e.g., DE10Y vs US10Y). Aligns mixed-frequency data (daily vs monthly) to calculate **10-day momentum**. Approves signals only if macro trends support the direction.
- **Policy Rate Bias**: Real-time integration of **FEDFUNDS** and **ECBMRRFR**. Generates bullish/bearish overrides if central bank rates diverge by more than 1.5%.
- **Commodity Inverse Filter**: Assets like Oil (`CL=F`) are weighted against DXY momentum to protect against structural dollar-driven reversals.

### 2. Regime-Aware Entry Trigger (`hmm_analysis.py`)
- **Dynamic Exit Levels**: ATR-based TP/SL targets that scale with current market volatility.
- **1.2 Candle Logic**: In "Macro Trap Phases" (yields diverging from price), entries are only permitted if the current candle breaks the previous high/low by 1.2x ATR.
- **Regime-Shift Protection**: Live detection of state transitions; if the HMM shifts from 'Breakout' to 'Consolidation', active trades are flagged for immediate re-evaluation.

### 3. Verification & Stability
- **Walk-Forward Backtest**: An independent `backtest.py` module replicates the live scanner's logic on 6 months of historical data to ensure architectural stability.
- **Bayesian Prior Stability**: Uses `HMM_COVARS_PRIOR` and `HMM_MIN_COVAR` in `config.py` to prevent numerical instability during model training.

## 🛠️ Installation & Setup

1. **Environment**: Recommended Python 3.12 (for `hmmlearn` stability).
2. **Setup**:
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. **Data Requirements**: Requires internet access to `yfinance` and `FRED` (St. Louis Fed) CSV exports.

## 📈 Usage

- **Live Scanner**: `python main.py` (Real-time regime detection + Tracking).
- **Architecture Backtest**: `python backtest.py` (Full 22-pair walk-forward simulation).

## 📁 Output Artifacts
- `analysis_summary.csv`: Real-time signal summary with macro bias warnings.
- `backtest_results.csv`: Comprehensive performance metrics (Sharpe, Max Drawdown).
- `backtest_trade_log.csv`: Detailed log explaining SL/TP triggers and Regime-Shift exits.
- `correlation_clusters.png`: Visual mapping of asset dependencies.

## ⚙️ Configuration
Modify `config.py` to adjust:
- `MAJORS_FIX_LIST`: Activation list for 1.2 Candle Logic.
- `FRED_TICKERS`: Yield and Policy Rate mappings.
- `YIELD_THRESHOLD`: Sensitivity of macro momentum filters.
