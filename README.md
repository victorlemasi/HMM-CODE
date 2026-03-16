# Currency Pair Scanner & Analysis (War-Time Edition)

A high-sophistication quantitative scanner designed for the volatility of the 2026 market regime. It uses multi-dimensional Hidden Markov Models (HMM), Macro-Economic Filtering (FRED), and Multi-Variate Jump Detection to identify and trade high-conviction breakout regimes.

## 🚀 Key Features

- **War-Time Asset Strategy**: Treats Gold (`GC=F`) and Oil (`CL=F`) as "War Sensors" with strict time-limits (4h/8h) and Mahalanobis jump-detection.
- **Fundamental Gatekeeper (Bouncer)**: Hybrid filtering using Yield Curve spreads (2s10s), USD Basket Sync, and Real Yield thresholds.
- **Cache-Less Data Integrity**: Completely disabled local caching to ensure 100% fresh data synchronization with `yfinance` and `FRED`.
- **London Lunch Squeeze**: Automated 90% confidence requirement during low-liquidity midday hours for major FX pairs.
- **Regime-Shift Protection**: Automatic "Flatten" logic triggered by structural HMM state transitions (Stable/Consolidation).

## 🧠 Sophisticated Logic Framework

### 1. The Fundamental Bouncer (Macro Gatekeeper)
Every technical signal must pass a multi-layered global fundamental validation suite:
- **Basket Sync Filter (FX)**: Prevents "Liquidity Sweeps" by ensuring EUR and GBP are moving in the same direction before approving long signals.
- **Yield Curve Divergence (2s10s)**: Compares US 10Y-2Y spreads against domestic (UK/GER) spreads. Vetoes entries if the domestic curve flattens significantly (>10bps) relative to the US.
- **Commodity Convergence Gates**:
    - **Gold (`GC=F`)**: Automated veto on Longs if **TIPS (Real Yields)** or the **DXY** show aggressive upside momentum.
    - **Oil (`CL=F`)**: Blocks Longs during deep US Yield Curve inversion (< -0.30) to protect against recessionary demand shocks.
- **RBNZ/CB Bias**: Real-time yield tracking for NZD/AUD pairs; automated Bullish/Bearish overrides based on policy rate differentials.

### 2. Bayesian Confidence Weighting & Temporal Filters
Technical HMM probabilities are adjusted by **Macro Momentum** and **Liquidity Windows**:
- **Confidence Thresholds**: Base threshold of 0.70, elevated to **0.90** during the **London Lunch Hour** to filter out low-volume noise.
- **Temporal Kill Zones**: Peak liquidity hours are prioritized; new entries are restricted during dead hours to avoid technical breakout traps.
- **Signal Expiry**: Signals expire after 3 bars for FX and 2 bars for Commodities if price handles are not triggered.

### 3. Integrated Watchdog & Risk Overrides
- **War-Time Time Exits**: Strict holding periods to minimize tail-risk exposure (4h for Oil, 8h for Gold).
- **Parabolic Trailing Stops**: SAR-style trailing logic specifically for `EURUSD=X` to lock in profits during trend extensions.
- **Mahalanobis Jump Detection**: Multi-variate outlier detection for Gold using covariance-adjusted distance rather than simple Z-scores.
- **Scalp Mode (Oil)**: Automatic transition to a high-frequency risk profile when `CL=F` macro conditions are volatile but non-trending.
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
- **Architecture Backtest**: `python backtest.py` (Full 22-pair simulation with War-Time overrides).

## 📁 Output Artifacts
- `backtest_results.csv`: Comprehensive metrics (Sharpe, Drawdown, Profit Factor).
- `correlation_clusters.png`: Visual mapping of current market integration.
- `backtest_trade_log.csv`: Per-trade breakdown of entry/exit reasons (incl. SL, TP, Time-Exit, and Regime-Shift).

## ⚙️ Configuration
Modify `config.py` to adjust:
- `ASSET_N_COMPONENTS`: Per-asset HMM state counts.
- `ATR_MULTIPLIER_FX / GOLD`: Sensitivity of regime transition guards.
- `BB_SQUEEZE_THRESHOLD`: Volatility contraction requirements.
