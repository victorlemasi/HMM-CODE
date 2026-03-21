# Currency Pair Scanner & Analysis (Unified Macro-Quant)

A high-sophistication quantitative scanner designed for the structural volatility of 2026. It integrates multi-dimensional **Hidden Markov Models (HMM)**, real-time **Macro-Economic Intelligence (FRED)**, and **Regime-Aware Risk Protection** to identify and validate high-conviction breakout opportunities.

## 🚀 Key Features

- **End-to-End Macro Pipeline**: Automated fetching from **FRED** and **Yahoo Finance**. Monitors 10Y Yields, Policy Rates, and Geopolitical Risk (GPR) indices.
- **Regime Detection (HMM)**: Uses a 6-feature "Canonical Engine" (Returns, Volatility, RSI, etc.) to classify markets into *Consolidation*, *Mean Reversion*, or *Trend Breakout*.
- **Fundamental Gatekeeper (Bouncer)**: Validates technical breakouts against Yield Spread Momentum and Central Bank Policy Rate differentials.
- **Jump Watchdog**: Real-time 1-minute monitoring using **Mahalanobis Distance** (Gold) and **Z-Scores** (FX) to pause trading during extreme market shocks.
- **War-Time Logic**: Specialized handling for Gold (`GC=F`) and Oil (`CL=F`) with Real Yield filters and strict 4h/8h time-based exits to manage flash-gap risks.
- **Liquidity Awareness**: Implements "Lunch Zone" penalties (London Lunch / NY Pre-Open) by automatically raising confidence thresholds during low-liquidity windows.
- **Dynamic Exit Engine**: ATR-based TP/SL targets that scale with regime intensity (3:1 for Trends, 1.5:1 for Scalps).

## 🧠 Sophisticated Logic Framework

### 1. The Macro Gatekeeper (`macro_bouncer.py`)
Technical signals must pass through a multi-layered fundamental filter:
- **Yield Spread Momentum**: Aligns mixed-frequency data to calculate 10-day momentum. Approves LONGs only when yields support the thematic move.
- **Policy Rate Bias**: Real-time integration of FEDFUNDS and ECB rates. Generates "Macro Vetoes" if central bank stances diverge from technical signals.
- **Geopolitical Risk (GPR)**: Automatically switches to "Safe Haven Mode" (prioritizing Gold/USD) when GPR spikes beyond 2.0 standard deviations.

### 2. Regime-Aware Entry Trigger (`hmm_analysis.py`)
- **Standardized Features**: Maintains a fixed 6-pillar feature vector for HMM compatibility across training and live execution.
- **1.2 Candle Logic**: Requires a breakout magnitude of 1.2x ATR for major pairs to filter out "Whipsaw" noise in macro-congested zones.
- **Regime-Shift Exits**: If the bot detects a transition from 'Trend Breakout' back to 'Consolidation', it identifies an early exit recommendation to preserve capital.

### 3. Execution & Risk Management (`main.py`)
- **Trade Tracker**: Persists active signals in `trade_tracker.json` to manage multi-candle trades and signal expiry (3 bars for FX, 2 for Commodities).
- **Progressive Stops**: Automatically trails SL once PnL reaches 1.5 ATR (Trend) or 0.8 ATR (Mean Reversion).
- **Correlation Hedging**: Identifies "Market Neutral" opportunities where correlated clusters are breaking out in opposite directions.

## 🛠️ Installation & Setup

1. **Environment**: Recommended Python 3.12.
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. **Execution**:
   - **Training**: `python train_hmm.py` (Fits Baum-Welch parameters on 1 year of data).
   - **Live Scanner**: `python main.py` (Runs the infinite analysis loop).
   - **Backtest**: `python backtest.py` (Full walk-forward simulation of the 2026 logic).

## 📁 Output Artifacts
- `analysis_summary.csv`: Real-time signal summary with macro bias warnings.
- `trade_tracker.json`: Active trade state and progressive stop-loss levels.
- `correlation_clusters.png`: Visual mapping of asset dependencies via K-Means clustering.
- `backtest_results.csv`: Comprehensive performance metrics (Sharpe, Max Drawdown).

## ⚙️ Configuration
Adjust parameters in `config.py` for thresholds, ticker mappings, and risk limits.

## 🚀 Verification Results (March 21, 2026)
- **Models Retrained**: All 22 assets successfully updated to the new 7-pillar architecture.
- **System Integrity**: 7-feature vector consistency (Yield Spread, Log Returns, RSI, etc.) verified via sample model metadata.
- **Live Test**: Completed a full loop of `main.py` with zero errors, confirming synchronization between the new macro features and the HMM engine.
