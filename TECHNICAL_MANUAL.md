# 🔬 Institutional HMM-Quant Technical Manual (v5.0)

This manual provides an exhaustive, "micro-detail" specification of every mathematical gate, veto, and architectural decision within the March 2026 Production Node.

---

## 🇯🇵 Special JPY Institutional Vetoes

The Yen is treated with unique "Safe-Haven" logic due to its status as a funding currency.

### 1. The DXY Correlation Bridge
*   **Module**: `hmm_analysis.py` (Line 155)
*   **Logic**: For pairs containing **JPY**, the specialty feature (`Spec_Feat`) in the HMM automatically maps to the **DXY (US Dollar Index)** correlation.
*   **Purpose**: To ensure the HMM understands JPY strength/weakness in the context of global dollar dominance, rather than in isolation.

### 2. The BoJ Sentiment Specialization
*   **Module**: `sentiment_fetcher.py` (Line 89)
*   **Logic**: When analyzing JPY pairs, the SerpApi engine targets: `"Bank of Japan interest rates OR JPY currency"`.
*   **Timing**: Strictly filtered for the **last 6 hours** to capture overnight BoJ "Jawboning" or YCC (Yield Curve Control) shifts.

### 3. JPY Carry-Trade Veto
*   **Module**: `macro_bouncer.py` (Line 58)
*   **Logic**: In the event of a **Bull-Steepener** (US 2s10s curve steepening while inverted), the bot applies a **Bearish Bias** to JPY base pairs (USDJPY) to prevent trading into a risk-off yen squeeze.

---

## 📈 Yield Differential & The "Gravity Curve"

This is the system's most sophisticated fundamental gate, moving beyond binary "Allow/Block" and into continuous weighting.

### 1. The Policy Rate Differential
*   **Module**: `macro_bouncer.py` (Line 154)
*   **Threshold**: **1.5% (150 Basis Points)**.
*   **Logic**: If the gap between the Base Policy Rate (e.g., Fed Funds) and the Quote Policy Rate (e.g., BoJ Rate) exceeds 1.5%, the bot assigns a **Bullish/Bearish Bias** to the pair.
*   **Impact**: Trades aligned with the "Carry" (High Yield vs Low Yield) are given a confidence multiplier.

### 2. Yield Momentum (The Gravity Pull)
*   **Module**: `macro_bouncer.py` (Line 112)
*   **Lookback**: **240-Bar Momentum** (Approx. 10 trading days for hourly data).
*   **Calculation**: $\Delta Spread = (Y_{base} - Y_{quote})_{now} - (Y_{base} - Y_{quote})_{lb}$.
*   **Gravity Multiplier**: `max(-0.30, min(0.30, dp_momentum * 2.0))`.
*   **Effect**: A rising yield spread acts as "Gravity" that pulls the price toward it, resulting in a **0.70x to 1.30x** weight adjustment.

---

## 🛡️ Veto Thresholds & Benchmarks (The "Nitty Gritty")

### 1. Watchdog Jump Detection
*   **Standard Z-Score**: $> 2.5$ (Statistically significant 1-minute outlier).
*   **Gold Mahalanobis**: $> 3.0$ (Multi-dimensional outlier considering Price + Yield + Vol).
*   **Action**: Immediate `VETO` of the 1-hour signal to avoid "catching a falling knife."

### 2. Oceanic Chop Filter
*   **Multiplier**: $1.4 \times$ (40-period rolling ATR).
*   **Pairs**: AUDUSD, NZDUSD, AUDJPY, NZDJPY.
*   **Philosophy**: The "Oceanic session" is prone to low-liquidity volatility spikes that do not represent true trend breaks. This filter suppresses "noise trades."

### 3. Entropy Gate (The "Certainty" Lock)
*   **Standard**: $0.70$ probability.
*   **Triple-Locked Crosses**: $0.85$ probability for `EURNZD`, `GBPAUD`, `GBPNZD`.
*   **Reasoning**: These crosses have high idiosyncratic volatility; the HMM must show extreme predictive dominance (85%+) to override the system's baseline skepticism.

### 4. XGBoost AI Ensemble
*   **Classifier Target**: `target_long_win` | `target_short_win`.
*   **Success Definition**: Future price move $> 0.5 \times ATR$ within 24 hours.
*   **Features**: `state_id`, `hmm_confidence`, `atr_normalized`.
*   **Veto**: Any signal with prediction `0` (Non-Breakout) is killed, even if HMM confidence is high.

---

## ⚙️ The Boot sequence (Standard Operating Procedure)

1.  **GPR Pulse**: Analyzes the Geopolitical Risk index. If risk $> 2.0$ Z-scores, all "Mean Reversion" signals are vetoed in favor of "Safe Haven" Trend Breakouts only.
2.  **Watchdog Sweep**: 1-minute jump detection for 22 assets to ensure no flash-crashes are in progress.
3.  **HMM Warm-Start**: Every 20 minutes, models are initialized with GMM clusters before the Baum-Welch re-fit to prevent "local optima" trapping.
4.  **Markowitz Optimization**:
    *   **Objective**: Maximize $\frac{Return}{Volatility}$.
    *   **Constraint**: Full allocation (Weights sum to 1.0).
    *   **Penalty**: Assets in the same "Cluster" are algorithmically penalized if their covariance is rising.

---

**March 2026 Audit Status**: 🟢 Certified Structural/Temporal/Execution Integrity.
**Data Lifecycle**: **Yahoo (Price) -> FRED (Macro) -> SerpApi (News) -> transformer (NLP) -> HMM (Brain) -> XGBoost (Veto) -> scipy (Alloc) -> CSV (Log).**
