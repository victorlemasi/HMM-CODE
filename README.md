# 🌐 Institutional HMM-Quant Phase 7 Node (March 2026)

This repository contains an ultra-advanced, multi-layer AI trading node. The system is architected to operate with a **v7.0 "ENGINE SWAP"** architecture, specifically designed to solve the structural "Information Asymmetry" between historical models and the 2026 volatility regime.

## 🚀 v7.0 "THE ENGINE SWAP" (Architecture Refactor)

The v7.0 upgrade represents a fundamental shift from "Historical Observation" to **"Real-Time Predation"** by resolving three critical architectural flaws identified in previous versions:

### 👻 1. Exorcising the "Scale Ghost" (Dynamic Normalization)
*   **Problem**: Previous versions used a "Frozen" `StandardScaler` from 2024. In the high-volatility 2026 market, this caused the bot to perpetually mislabel normal price action as "Extreme Trends."
*   **Fix**: **Online Incremental Scaling**.
*   **Mechanism**: The system now re-fits its mathematical "glasses" (StandardScaler) every loop using a **Rolling 500-bar Window**. The HMM now understands that 20 pips of volatility in 2026 is "normal," preventing false breakout entries.

### 📉 2. Leading Force Features (Money Flow Acceleration)
*   **Problem**: RSI and Momentum are lagging indicators (15-20 hour horizons). By the time they triggered, the "Alpha" of the move was already 70% consumed.
*   **Fix**: **Leading Force & Acceleration Features**.
*   **Mechanism**: Swapped RSI/Momentum for **Force Index (Money Flow)** and **Volatility Acceleration**. These features react to the *velocity of capital* rather than the *history of price levels*, enabling earlier entries with higher precision.

### ⚖️ 3. Solving the "Kelly Fallacy" (Risk-Parity Sizing)
*   **Problem**: Using HMM Confidence for position sizing created a "Negative Selection" bias—the bot bet the most exactly when a trend was at its most obvious (and thus most exhausted).
*   **Fix**: **Volatility-Adjusted Risk Parity**.
*   **Mechanism**: Decoupled sizing from HMM Confidence. Implementation of a **"Confidence Inverse" Cap**: If Confidence is $>0.92$, the bot de-risks ($0.7x$ size) to protect against exhaustion spikes. Final size is determined by **ATR Volatility Parity**, ensuring every trade risks equal "Account Intensity."

### 📡 4. Synchronic Macro Sync (1H Intraday Proxies)
*   **Problem**: Daily FRED data created a 24-hour lag between macro-filters and technical-entries.
*   **Fix**: **Intraday Macro Proxies**.
*   **Mechanism**: Total transition to 1-Hour intraday proxies for yields (DXY, TLT Slopes, and Futures Spreads), ensuring the "Macro Bouncer" breathes at the same pace as the "Technical Hunter."

---

## 🛡️ The 7-Layer Veto Shield: v7.0 Security

A signal must survive all 7 layers of the updated Veto Shield before execution:

### Layer 1: The Entropy Gate (Contextual Confidence)
*   **Standard Floor**: $>0.70$ Confidence.
*   **Session Lull Extension**: Confidence floor raised to **0.85** during the "Asian Lull" (21:00 - 07:00 UTC) for European pairs.

### Layer 2: The Carry-Trade Gravity (Yield Bias)
*   **Logic**: If the Interest Rate Differential (IRD) is $>1.5%$, the Z-score entry threshold shifts to **1.2** for carry-positive trades and **2.0** for anti-carry trades. Don't fight the yield.

### Layer 3: The Autocorrelation Filter (Trend persistence)
*   **Threshold**: $\text{Lag-1 Autocorr} (\rho_1) > 0.25$.
*   **Function**: Vetoes "Flash Spikes" that lack the structural persistence needed for a sustained trend breakout.

### Layer 4: The PDE Absorption Filter (Institutional Churn)
*   **Metric**: $\text{PDE} = |\text{Return}| / \text{Volume}$.
*   **Function**: Vetoes trades where volume is massive but price progress is minimal (indicating institutional "Iceberg" absorption).

### Layer 5: The Micro-CVD Slope (Limit Order Absorption)
*   **Threshold**: $|\text{Slope}| > 0.01$ over most recent 60 minutes.
*   **Veto Logic**: Vetoes **LONG** if institutions are absorbing with limit-selling; Vetoes **SHORT** if limit-buying is trapping sellers.

### Layer 6: The XGBoost Hybrid Ensemble (Supervised Veto)
*   **Training Target**: $Forward\_Return > 0.5 \times ATR$ in 24 hours.
*   **Function**: The AI "rejects" the signal if the historical footprint matches a previous liquidity trap.

### Layer 7: The Commodity Liquidity Gate (Time-of-Day)
*   **Window**: 07:00 – 17:00 UTC (London/NY overlap).
*   **Target**: Gold (`GC=F`) and Oil (`CL=F`).

---

---

## 📂 How the Source Code Works (Technical Breakdown)

The Hunter-Quant system is a modular, event-driven trading node. Here is how the individual components interact:

### 1. `main.py` (The Heartbeat)
The central orchestrator. It runs a 5-minute loop (`heartbeat`) on your T480s console.
*   **Orchestration**: It triggers the data fetch, runs the macro filters, calls the HMM brain, and calculates portfolio weights.
*   **Safety Watchdog**: Every loop, it runs a 1-minute "Jump Detection" check on Gold and Oil to pause trading if a geopolitical shock occurs.
*   **Trade Tracker**: Manages entries, Take Profits, and Stop Losses in `trade_tracker.json` to ensure persistence across restarts.

### 2. `data_fetcher.py` (The Eyes)
Handles all inbound market information.
*   **MT5 Bridge**: Connects directly to the MetaTrader 5 terminal to pull zero-delay institutional ticks for `XAUUSD`, `WTI`, and Forex.
*   **Yahoo/FRED Fallback**: Pulls historical daily data for MTF (Multi-Timeframe) consensus and monthly FRED data for central bank rates.
*   **Returns Matrix**: Converts raw price data into the logarithmic returns matrix required for HMM clustering.

### 3. `hmm_analysis.py` (The Brain)
Implements the core Unsupervised Machine Learning logic.
*   **Gaussian HMM States**: Classifies the market into three regimes: `Consolidation` (Chop), `Mean Reversion` (Reversals), and `Trend Breakout` (Momemtum).
*   **Warm-Start Adaptation**: Instead of using old models, it performs "Fine-Tuning" on the last 400 bars to adapt to the last hour's volatility.
*   **Dynamic Exits**: Calculates SL and TP levels based on **ATR Multipliers** (Average True Range).

### 4. `macro_bouncer.py` (The Judge)
The fundamental filter that prevents "Technical Hallucinations."
*   **Gravity Curve Multipliers**: It looks at the **Yield Spread Momentum** (e.g., US10Y vs GER10Y). 
*   **Bias Weighting**: If a technical LONG signal conflicts with the yield trend, this module penalizes the confidence score (e.g., 0.7x weight). If aligned, it boosts it (1.3x).

### 5. `config.py` (The Nervous System)
The single point of truth for the entire bot.
*   **Thresholds**: Sets the HMM confidence floors (0.55), Z-Scores (1.1), and ATR buffers.
*   **Credentials**: Securely stores your MT5 Demo login (`5048601874`) and broker server details.
*   **Symbol Map**: Translates Yahoo tickers to Broker symbols (e.g., `GC=F` -> `XAUUSD`).

### 6. `train_hmm.py` (The Memory)
Handles the "Heavy Lifting" of offline training. 
*   **Baum-Welch Fitting**: Runs multi-threaded training on 1 year of historical data to create the "Base Models" stored in `hmm_models/`. 

### 7. `clustering.py` & `rebalancer.py` (The Strategists)
*   **Clustering**: Groups the 22 pairs into clusters of "Similar Movement" to avoid over-exposure to a single currency (like USD).
*   **Markowitz Optimization**: Uses Modern Portfolio Theory to assign weights to active signals, ensuring the highest Sharpe Ratio.

---

## 🛠️ Performance & Scalability
- **Parallelization**: 8-Core Baum-Welch re-fitting via `joblib`.
- **Latency**: 5-Minute loop (300s) optimized for real-time MT5 ticks.
- **Hardware**: Optimized for Intel i5/i7 (Lenovo T480s) performance.

---
**March 2026 Audit Status**: 🟢 v7.2 UNLEASHED - **Live MT5 Integration Functional.**
