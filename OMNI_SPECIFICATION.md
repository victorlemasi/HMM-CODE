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
- **The Trigger**: Re-trains all 42 models every 4 loops (20 minutes).
- **Baum-Welch Training**: The HMM is completely rebuilt/fine-tuned using a rolling **365-day** lookback for the best recent regime adaptation.
- **Hardware Warning**: Ensure the T480s is on a hard surface and plugged into A/C power. Thermal throttling on battery will cause the 90-second training spike to lag into several minutes, risking "Clock Drift."

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

---

## 🛡️ MODULE III: THE VETO VAULT (THE 10 PROTECTIVE SHIELDS)

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

### 1. Dynamic Kelly Sizing
- **Calculates optimal bet size**: `kelly_raw / 0.50` (Capped 0.1x to 2.5x).
- **Logic**: Correlates the statistical edge to the capital allocation.

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
