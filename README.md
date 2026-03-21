# 🌐 Institutional HMM-Quant Phase 5 Node (March 2026)

This repository contains an ultra-advanced, multi-layer AI trading node. The system is architected to operate with a **"Triple-Lock" Audit Policy**, ensuring every signal is vetted by seven redundant mathematical layers before being logged for execution.

## 📖 Master Documentation: Omni-Specification (v5.5)
For an exhaustive, chapter-by-chapter deconstruction of the **Hunter-Quant Terminal**, including hardware stewardship for the **T480s** and the **$KES$ 200,000** risk model, please refer to the:

**[Hunter-Quant Omni-Specification](file:///C:/Users/lenovo/Downloads/scanner/Currency-Pair-Scanner-Analysis/OMNI_SPECIFICATION.md)** 📑

This document provides 20+ pages of "Micro-Detail" documentation for professional quantitative auditing.

---

## 🚀 The Boot Sequence: System Initialization
When `main.py` is executed, the following "Cold Boot" sequence occurs:
1.  **Environment Loading**: Reads `.env` for FRED and SerpApi credentials.
2.  **Global Risk Pulse (GPR)**: Calculates the Geopolitical Risk Z-Score. If $Z > 2.0$, the system enters "Defensive Mode."
3.  **1m Jump Watchdog**: Fetches 1-minute data for the active universe to detect flash-crashes ($Z > 2.5$) or Gold jumps (Mahalanobis $> 3.0$).
4.  **HMM Re-Fitting**: Every 4 loops (20 mins), the Baum-Welch algorithm re-trains all 42 models on the latest 2-year history to adapt to "New Normal" market dynamics.
5.  **Multi-Layer Analysis**: Iterates through the 7-Layer Veto Shield (detailed below).
6.  **Portfolio Optimization**: Runs the Markowitz Efficient Frontier to allocate weights.
7.  **Audit Persistence**: Updates `analysis_summary.csv` and syncs the entire repository to GitHub.

---

## 🛡️ The 7-Layer Veto Shield: Micro-Technical Details

The system employs a "Defense-in-Depth" strategy. A signal must survive all 7 layers below:

### Layer 1: The Entropy Gate (Contextual Confidence)
*   **Threshold**: $\text{Confidence} > 0.70$ for standard assets.
*   **Hardened Threshold**: $\text{Confidence} > 0.85$ for hyper-volatile crosses (`EURNZD`, `GBPAUD`, `GBPNZD`).
*   **Function**: Prevents state-flipping in low-probability regimes.

### Layer 2: The Oceanic Chop Filter (Volatility Spikes)
*   **Threshold**: $\text{Current ATR} > 1.4 \times \text{Rolling 40-Bar ATR}$.
*   **Target**: AUD and NZD crosses.
*   **Function**: Blocks trades occurring in "Drunken Sailor" volatility spikes common in Oceanic sessions.

### Layer 3: The Micro-CVD Slope (Limit Order Absorption)
*   **Threshold**: $|\text{Slope}| > 0.01$ over most recent 60 minutes.
*   **Granularity**: 1-Minute tick intensity.
*   **Veto Logic**: Vetoes **LONG** if institutions are absorbing with limit-selling. Vetoes **SHORT** if limit-buying is trapping sellers.

### Layer 4: The 6-Hour NLP Freshness (Sentiment Modifier)
*   **Window**: Latest 6 hours of Google News headlines.
*   **Engine**: ProsusAI/FinBERT Transformer.
*   **Impact**: Applies a multiplier ($0.5x$ to $1.5x$) to the final HMM probability. Multipliers below $0.8x$ act as a "Soft Veto."

### Layer 5: The Gravity Curve (Yield Spread Momentum)
*   **Metrics**: US 10Y vs German 10Y, US 2s10s Curve Steepness.
*   **Policy Rate Lock**: A **1.5% (150 bps)** differential between Base/Quote rates triggers a baseline fundamental bias.
*   **Yield Momentum**: Calculates **240-Bar Momentum** of the spread ($Y_{base} - Y_{quote}$).
*   **Veto Logic**: Detects "Bull-Steepener" traps. If the US curve is steepening while inverted, USD Longs are restricted to prevent trading into a hard-landing shock.

### Layer 6: JPY-Specific Safeguards
- **DXY Bridge**: JPY models are automatically correlated to USD Strength (`DX-Y.NYB`) to detect global risk-off yen squeezes.
- **BoJ Sentiment**: NLP strictly targets "Bank of Japan" news within a **private 6-hour window**.

### Layer 6: The XGBoost Hybrid Ensemble (Supervised Veto)
*   **Training Target**: $Forward\_Return > 0.5 \times ATR$ in 24 hours.
*   **Feature set**: HMM State ID + HMM Confidence + Normalized ATR.
*   **Function**: The AI "rejects" the signal if the historical footprint matches a previous liquidity trap.

### Layer 7: The Commodity Liquidity Gate (Time-of-Day)
*   **Window**: 07:00 – 17:00 UTC (London/NY overlap).
*   **Target**: Gold (`GC=F`) and Oil (`CL=F`).
*   **Function**: Blocks breakout attempts during low-liquidity Asian or Sydney hours where price discoveries are often false.

---

## 🛠️ Performance & Scalability
- **Parallelization**: 8-Core Baum-Welch re-fitting via `joblib`.
- **Latency**: 5-Minute loop (300s) optimized for hourly-to-daily trade duration.
- **Portability**: Full CI/CD readiness with `git` auto-push integration.

---

## 🧩 Dependencies & Modules
- **`hmmlearn`**: Core unsupervised math.
- **`transformers`**: NLP sentiment bridge.
- **`fredapi`**: Macro yield curves.
- **`scipy.optimize`**: Portfolio Markowitz weights.
- **`xgboost`**: Supervised ensembling.

---
**March 2026 Audit Status**: 🟢 Certified Structural/Temporal/Execution Integrity.
