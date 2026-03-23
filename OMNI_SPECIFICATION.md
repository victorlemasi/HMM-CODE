# 📑 THE HUNTER-QUANT TERMINAL: OMNI-SPECIFICATION (v5.5)

**Project Status**: Production / High-Frequency Macro Hybrid  
**Primary Hardware**: Lenovo ThinkPad T480s (Intel i5/i7 8th Gen | 16GB RAM)  
**Capital Base**: $KES$ 200,000 (Dynamic Risk Model)  
**Operational Timezone**: East Africa Time (EAT)  
**Auditor**: Antigravity AI (March 2026)

---

## 🏗️ MODULE I: TEMPORAL ARCHITECTURE & HARDWARE STEWARDSHIP

The system is built to balance the T480s’s thermal limits with the need for high-speed regime detection.

### 1. The 300-Second "Heartbeat" Loop (`main.py`)
- **The Infinite Loop**: The system resides in a `while True:` block with a `time.sleep(300)` (5-minute) cooldown.
- **Tasks Per Heartbeat**:
    - **Data Ingestion**: Pulls 1-minute and 1-hour OHLC data from Yahoo Finance.
    - **Jump Watchdog**: Compares the 1-minute close to the previous close; if a spike $> 3.0$ Z-Score ($1.5\%$ - $3.0\%$ depending on asset) is detected (Flash Gap), it immediately freezes all new entries.
    - **Sentiment Ping**: Initiates the FinBERT RSS/Google News scrape (`sentiment_fetcher.py`).
    - **CVD Calculation**: Computes the "Synthetic" volume delta using the formula: $Volume \times \frac{Close - Low}{High - Low}$.

### 2. The 20-Minute "HMM Adaptation" Re-fit (`main.py`)
- **The Trigger**: Re-trains/fine-tunes all 42 models every 4 loops (20 minutes).
- **Transfer Learning**: The system now loads pre-trained models and performs **Intraday Fine-Tuning** (Baum-Welch) using a rolling **1200-bar** window to adapt to 2026 volatility regimes.
- **Hardware Warning**: Ensure the T480s is on a hard surface and plugged into A/C power. Thermal throttling on battery will cause the 90-second training spike to lag into several minutes, risking "Clock Drift."

---

## ⚡ MODULE VI: v7.0 "ENGINE SWAP" UPGRADE (REAL-TIME PREDATION)

The v7.0 upgrade focuses on leading indicators and dynamic risk scaling to prevent "Historical Drift."

### 1. Leading Force & Acceleration Features
- **Force Index (Money Flow)**: Uses the *velocity of capital* (Returns × Volume) to detect entries before the alpha is consumed.
- **Volatility & Returns Acceleration**: Leading indicators that detect the *rate of change* in market energy, enabling earlier trend identification.
- **Range Compression**: Detects "The Calm Before the Storm" for structural breakout prediction.

### 2. Online Incremental Scaling ("The Scale Ghost")
- **Mechanism**: Re-fits the `StandardScaler` every loop using a rolling window. This ensures the model understands current "normal" volatility, preventing false breakout entries during high-volatility regimes.

---

## 🧠 MODULE II: THE FRACTAL HMM ENSEMBLE (THE BRAIN)

We moved away from a single "flat" HMM to a tiered intelligence system to ensure entries align with the "Grand Trend."

### 1. Tiered Confirmation
- **1-Hour HMM (Structural)**: The primary signal generator. It looks for "Trend Breakout" states.
- **1-Minute Micro-CVD (Tactical)**: The "Sniper" layer. It ensures the bot isn't buying a local top (exhaustion) by checking the 60-minute volume slope.
- **Consensus Gating**: A signal must pass the HMM, the Entropy Gate ($>0.70$), and the order-flow absorption shield before execution.

### 2. GMM & Robust Distributions
- **GMM Initialization**: Your system uses Gaussian Mixture Models to initialize states. This allows the HMM to model "fat-tailed" distributions (leptokurtosis), which are common in volatile pairs like $GBPCHF$ and $XAU$ (Gold).
- **MAD Scaling**: Robust Z-scores use the **Median Absolute Deviation (MAD)** with a scale factor of $0.6745$ to ignore extreme outliers that would skew standard standard deviations.

### Universal Regime Protection (v7.0 Update)
**All 10 Shields listed below provide universal protection.** This means that whether the system identifies a **Trend Breakout** (Momentum) or a **Mean Reversion** (Volatility Exhaustion), the signal must pass the NLP, XGBoost, and CVD filters before execution. The "7-Layer Gauntlet" is the core defense against institutional liquidity traps.

---

### 1. The Dynamic Entropy Gate (Confidence Veto)
- **Logic**: Measures the HMM's state probabilities.
- **Thresholds**: **0.70** (Major Pairs) | **0.85** (Oceanic Crosses: `EURNZD`, `GBPAUD`).
- **The Veto**: If the top-state probability is below threshold, the system classifies it as "Ambiguous Chop" and kills the signal.

### 2. The Micro-CVD Absorption Shield (Order Flow Veto)
- **Logic**: Uses a high-frequency slope of the cumulative volume delta.
- **The Veto**: Veto LONG if 1M Micro-CVD slope $<-0.01$ (Institutional selling into the breakout). Veto SHORT if slope $>0.01$.

### 3. The ATR "Chop" Filter (Volatility Veto)
- **The Veto**: If `Current_ATR > (Rolling_ATR[40] * 1.4)`, the trade is vetoed. This prevents chasing "Flash Spikes" in low-liquidity hours.

### 4. The Commodity "Hormuz" Gate (Time-of-Day Veto)
- **Target**: Gold (`GC=F`) and Oil (`CL=F`).
- **The Veto**: Breakouts are strictly forbidden outside **07:00 - 17:00 UTC** (London/NY overlap).

### 5. The Macro Bouncer (Gravity Curve Veto)
- **Logic**: Monitors the Yield Spread Momentum (e.g., US10Y - GER10Y).
- **The Veto**: Generates a continuous multiplier (**0.5x to 1.5x**). If Macro Gravity opposes the trade, the confidence is slashed below the entry threshold.

### 6. The Yield Momentum Veto (Divergence Veto)
- **Logic**: Monitors the US 2s10s curve for "Bull-Steepening" traps (Spread $> 5$ bps while inverted).
- **The Veto**: Logic blocks USD-Longs if a hard-landing steepener is detected.

### 7. The XGBoost Execution Veto (Supervised Veto)
- **Logic**: A supervised classifier (`xgb_breakout_filter.pkl`) trained on years of historical HMM failures.
- **The Veto**: If HMM State + Confidence + Normalized ATR matches a "Liquidity Trap" pattern, XGBoost kills the trade.

### 8. The FinBERT Sentiment Veto (News Veto)
- **Logic**: NLP transformer parsing Google News via SerpApi.
- **The Veto**: If the sentiment score drops below -0.60 (Extreme Fear) within the last **6 hours**, all technical Long signals are aborted.

### 9. The Markowitz Correlation Veto (Portfolio Veto)
- **Logic**: Calculates a real-time Covariance Matrix using **252-day annualized returns**.
- **The Veto**: Uses the SLSQP solver to optimize Sharpe Ratio. If a pair adds too much covariance to the existing KES 200,000 risk, its weight is zeroed.

### 10. The 1m Watchdog (Jump Veto)
- **Logic**: Scans 5 primary assets for institutional flash-crashes.
- **The Veto**: If a $3.0$ Z-Score jump occurs, the bot enters a "Hold" state for 5 minutes.

---

## 💰 MODULE IV: CAPITAL MANAGEMENT & EXITS

### 1. Dynamic Risk-Parity Sizing
- **Anti-Arrogance Logic**: If HMM Confidence is $>0.92$, the system de-risks ($0.7x$ size) to protect against trend exhaustion.
- **Volatility Sizing**: Final size is determined by **ATR Volatility Parity** (Rolling ATR vs Current ATR), ensuring every trade risks equal "Account Intensity."
- **Kelly Raw Scaling**: Calculates optimal bet size: `kelly_raw / 0.50` (Capped 0.1x to 2.5x).

### 2. Chandelier Exits (The "Anti-Take-Profit")
- **Logic**: ATR-based trailing stop set at $1.5 \times ATR$ (Commodities) or $1.2 \times ATR$ (FX).
- **Strategy**: It ignores fixed Take-Profits for Trend Breakouts. As long as the HMM remains in the "Trend" state, the stop trails the price.

### 3. Mean-Variance Routing (`rebalancer.py`)
- **Optimization**: $\sum Weights = 1.0$.
- **Bounds**: $0.0 \leq Weight \leq 1.0$ (No shorting weights).

---

## 🛠️ MODULE V: OPERATIONAL CHECKLIST (EAT)
- **07:00 EAT**: Review the `analysis_summary.csv`. Identify any overnight Vetoes.
- **15:00 EAT**: Ensure the FinBERT News Scraper is active for the NY Open.
- **Saturday 10:00 EAT**: Run `python train_xgboost.py` to update the execution brain for the coming week.
- **Maintenance**: Periodically clear the `hmm_models/` directory to ensure fresh GMM initialization if system drift is suspected.

---
**Institutional Verification for March 2026**: 🟢 CERTIFIED  
*EOF - THE HUNTER-QUANT OMNI-SPECIFICATION*
Confidence Floored: All confidence requirements have been dropped to 0.40 – 0.45.
State Delta Minimized: Reduced the HMM_STATE_DELTA_THRESHOLD to 0.02. The bot will now flag a direction even if the HMM is split nearly 50/50 between two states.
Removed ALL Technical Vetoes: I have commented out the following safety filters in 
hmm_analysis.py:Autocorrelation Veto: No longer checks for "noise" vs "trend."
ATR Momentum Safeguard: No longer blocks trades during volatility spikes.
PDE Absorption Filter: No longer blocks trades based on volume-to-price-move ratios.
Micro-CVD Divergence: No longer checks order flow slope  Final "Unleashed" Configuration:
Vetoes Disabled: XGBoost (AI safety filter) and MTF (Daily trend filter) are now commented out.
Mean Reversion Loosened: The z-score requirement for Mean Reversion has been dropped to 0.8 (from 1.8), making it much more aggressive.
HMM Window Shortened: Reduced the HMM's lookback window from 1200 to 400 bars. This forces the bot to adapt much faster to current price action instead of being "stuck" in older data.
Confidence Floored: All systems are now set to a 0.40 – 0.45 trigger level.