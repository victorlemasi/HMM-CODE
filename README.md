# Currency Pair Scanner & Analysis (War-Time Edition)

A high-sophistication quantitative scanner designed for the volatility of the 2026 market regime. It uses multi-dimensional Hidden Markov Models (HMM), Macro-Economic Filtering (FRED), and Multi-Variate Jump Detection to identify and trade high-conviction breakout regimes.

## 🚀 Key Features

- **War-Time Asset Strategy**: Treats Gold (`GC=F`) and Oil (`CL=F`) as "War Sensors" with unique safety filters and extended holding periods.
- **4-State HMM (Gold)**: Advanced state separation for Gold to isolate standard trends from explosive "Safe Haven Spikes."
- **Mahalanobis Jump Watchdog**: Multi-dimensional safety layer monitoring Price, Volatility, and Macro spreads to detect structural market shocks.
- **Volatility Squeeze Filter (EURUSD)**: Bollinger Band Width contraction requirements to filter "efficiency traps" in major pairs.
- **Real Yield (TIPS) Overlay**: Fundamental filtering for Gold longs based on 10-Year Real Interest Rates (FRED: `DFII10`).
- **Robust Stochastic Logic**: All statistical calculations (Z-Scores, Regimes) use Median Absolute Deviation (MAD) for resilience against fat-tailed financial distributions.
- **Regime-Shift Protection**: Automatic "Flatten" logic in the backtester/exec engine when HMM detects a transition out of tradeable states.

## 🧠 Sophisticated Logic Framework

### 1. The Fundamental Bouncer (Macro Gatekeeper)
Every technical signal must pass a series of global fundamental checks:
- **DXY Wall**: Prevents Longs in major currencies and Commodities if the US Dollar Index is in an aggressive trend.
- **Yield Spread Momentum**: Forces alignment with base symbol interest rate momentum (10Y Yield shifts).
- **RBNZ/CB Bias**: Automated hawkish/dovish scoring for commodity currencies (AUD, NZD) using policy rate data.

### 2. Bayesian Confidence Weighting
Technical HMM probabilities are adjusted by **Macro Momentum**:
- **Confidence Threshold**: 0.70 (Post-Adjustment).
- **Policy Differentials**: Signals are weighted by the interest rate carry advantage of the base currency.

### 3. Integrated Watchdog (Circuit Breakers)
- **1-Minute Pulse**: Real-time monitoring of jumps (> 3.5 MAD sigma).
- **15-Minute Cooldown**: Automatic trading pause on detection of idiosyncratic shocks.

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
