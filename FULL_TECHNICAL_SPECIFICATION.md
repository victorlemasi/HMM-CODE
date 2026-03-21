# ⚖️ Institutional HMM-Quant Technical Specification (v5.0)

**Date**: March 21, 2026  
**Status**: Institutional Production Ready  
**Scope**: Full 42-Module Suite

---

## CHAPTER 1: INDUSTRIAL CONTEXT & VISION

In the high-frequency quantitative landscape of March 2026, simple technical indicators are no longer sufficient to navigate the "New Normal" volatility. This system, established as a **Phase 5 Institutional Node**, was engineered to solve the "Paradox of Choice" in multi-asset trading.

Instead of following a single model, this architecture employs a **Multi-Model Consensus Mechanism**. It treats every trade as a hypothesis that must survive a 7-layer "Veto Shield" before capital is allocated. The goal is not just "High Yield," but **Sustainable Institutional Yield** through aggressive risk suppression and statistical pruning.

---

## CHAPTER 2: THE "TRIPLE-LOCK" SHIELD (ARCHITECTURE)

The system architecture is divided into three distinct verification tiers:

### 1. Structural Verification (Unsupervised)
The system uses **Hidden Markov Models (HMM)** to detect the underlying "regime" of the market (Breakout vs. Consolidation). This tier operates on the principle that market behavior is non-stationary and requires constant adaptation.

### 2. Temporal Verification (Real-Time)
The system integrates **FRED (Macro)** and **SerpApi (NLP)** to ensures that technical signals are aligned with the fundamental events of the last **6 hours**.

### 3. Historical Verification (Supervised)
The **XGBoost AI Veto** acts as the final judge. It compares the current HMM signal against 700 days of historical successes and failures to determine if the pattern is a "Ghost" or a "Reality."

---

## CHAPTER 3: DATA INGESTION ENGINE (`data_fetcher.py`)

The integrity of the "Brain" depends entirely on the fidelity of the "Eyes."

### 3.1 The Yahoo Finance Bridge
The system utilizes the `yfinance` library but implements a custom **Resiliency Wrapper**:
*   **Retry Logic**: 3-attempt exponential backoff.
*   **Log Returns**: All price data is converted to Log-Returns ($\ln(P_t / P_{t-1})$) to ensure statistical stationarity for the HMM Baum-Welch algorithm.
*   **Multi-Index Alignment**: Special handlers for Yahoo's varying MultiIndex headers across different asset classes (Majors vs. Commodities).

### 3.2 The FRED Macro Engine
Unlike standard APIs, the FRED engine in this node uses a **CSV-Direct Pattern**:
*   Downloads directly from `fred.stlouisfed.org/graph/fredgraph.csv`.
*   **Temporal Scaling**: Handles disparate publication schedules (Daily 10Y yields vs. Monthly Fed Funds) using a custom `ffill()` and `bfill()` alignment strategy in `macro_bouncer.py`.

---

## CHAPTER 4: THE MATHEMATICAL ENGINE (`hmm_analysis.py`)

This is the central processing unit of the bot.

### 4.1 The 7-Pillar Feature Vector
Every asset is analyzed through a fixed, 7-dimensional vector:
1.  **Returns**: 1-hour log returns.
2.  **Volatility**: 10-period rolling standard deviation.
3.  **Range**: $\frac{High - Low}{Close}$ (Intra-candle stretch).
4.  **Momentum**: 5-period vs. 20-period moving average distance.
5.  **RSI**: 14-period Relative Strength Index.
6.  **Spec_Feat**: 
    - **JPY Pairs**: Multi-variate correlation to **DXY**.
    - **Commodities**: Multi-variate correlation to **OIL** or **GOLD**.
7.  **Yield_Spread**: Momentum of the associated sovereign yield spread.

### 4.2 Baum-Welch Adaptation
The bot re-fits every model every 20 minutes. 
*   **Initialization**: Uses a **Gaussian Mixture Model (GMM)** to find the "warm" starting clusters.
*   **Diagnostics**: Models that produce NaNs or degenerate transition matrices are automatically rejected and fell back to the previous "Stable" model saved in `hmm_models/`.

---

## CHAPTER 5: THE MACRO BOUNCER (`macro_bouncer.py`)

### 5.1 The Bull-Steepener Veto
The system monitors the **US 2s10s Yield Curve**. 
*   **The Trap**: If the curve is inverted AND steepening ($Spread_{now} - Spread_{prev} > 0.05$), it signals a recessionary "Hard Landing" shock.
*   **Action**: All USD Long positions are immediately Vetoed to prevent trading into a risk-off dollar dump.

### 5.2 The 1.5% Policy Rate Lock
*   **Logic**: A carry-trade buffer.
*   **Benchmark**: If the interest rate differential between two currencies (e.g., USD vs JPY) is less than 150 basis points, the bot assumes "Chop" and increases the Entropy required for a trade to **0.85**.

---

## CHAPTER 6: THE AI VETO LAYER (`train_xgboost.py`)

The Phase 5 "AI Ensemble" is the bot's ultimate safety switch.

### 6.1 Training Logic
The XGBoost model is trained on a synthetic matrix where:
*   **Features**: `[state_id, hmm_confidence, normalized_atr]`
*   **Target ($y=1$)**: If the price moved **$> 0.5 \times ATR$** in the 24 hours FOLLOWING the HMM signal.
*   **Result**: The bot now "learns" that certain high-confidence HMM states are actually "Bull Traps" based on historical failure patterns.

---

## CHAPTER 7: HIGH-FREQUENCY ORDER FLOW (`micro_cvd_engine.py`)

### 7.1 Intraday Intensity Math
While the bot trades on the 1-hour chart, it "peeks" into the 1-minute chart.
*   **Formula**: $Delta = Volume \times \frac{2 \times Close - High - Low}{High - Low}$.
*   **Veto Logic**: If the 1-minute CVD slope is diverging from the 1-hour price action, the bot blocks the trade. This detects "Selling into a Breakout" (Absorption).

---

## CHAPTER 8: THE NLP SENTIMENT ENGINE (`sentiment_fetcher.py`)

### 8.1 FinBERT Transformation
*   **Model**: `ProsusAI/finbert`.
*   **Freshness Filter**: Strictly bounded to the **Last 6 Hours** of news.
*   **Sentiment Map**: 
    - **Positive News** > Confidence $\times 1.25$
    - **Negative News** > Confidence $\times 0.75$ (Veto Territory)

---

## CHAPTER 9: PORTFOLIO OPTIMIZATION (`rebalancer.py`)

### 9.1 Markowitz Efficient Frontier
*   **Technology**: `scipy.optimize.minimize`.
*   **Goal**: Maximize the Sharpe Ratio of the active trade group.
*   **Penalty**: Assets within the same "Cluster" (e.g., EURUSD and GBPUSD) are algorithmically penalized to prevent over-exposure to a single central bank move.

---

## CHAPTER 10: PERSISTENCE & AUDITING

### 10.1 The CSV Audit Trail
Every loop, the system updates `analysis_summary.csv`.
*   **Warnings Column**: Now includes the exact reason for every veto (e.g., "XGBoost AI Veto", "NLP Sentiment 0.65x").
*   **Trade Tracker**: `trade_tracker.json` maintains the state of active positions, stop losses, and take profits across sessions.

---

## CHAPTER 11: GLOBAL DEPENDENCIES (LIBRARY MANIFEST)

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `hmmlearn` | Latest | Baum-Welch HMM Algorithm |
| `xgboost` | Latest | Supervised AI Veto Ensemble |
| `transformers`| Latest | FinBERT NLP News Scraper |
| `yfinance` | Latest | Price Engine |
| `scipy` | Latest | Portfolio Rebalancer (SLSQP) |
| `joblib` | Latest | Multi-Core Training (8x Parallel) |

---

## CHAPTER 12: SETUP & OPS SOP

### 1. Cold Start Procedure
1. Verify `.env` contains `FRED_API_KEY` and `SERPAPI_KEY`.
2. Delete `backtest_results.csv` to clear old diagnostics.
3. Execute `python main.py`.

### 2. Monitoring the Pulse
Open `analysis_summary.csv` and check the **Last Updated** column. If the time is within 5 minutes of local time, the Institutional Node is **Active and Healthy**.

---

## CHAPTER 13: MODULE-BY-MODULE REFERENCE (MICRO-DETAIL)

### 13.1 `config.py`
The "Central Nervous System" of the node. 
- **`CURRENCY_PAIRS`**: The active 22-asset universe.
- **`WATCHDOG_JUMP_THRESHOLDS`**: Defines the "Flash-Crash" circuit breakers.
- **`HMM_COMPONENTS`**: Defines the state-resolution for different asset classes (4 for Gold, 3 for FX).

### 13.2 `data_fetcher.py`
- **`fetch_fred_data()`**: Uses a direct `requests.get` to the St. Louis Fed CSV export to bypass API overhead and rate limits.
- **`get_returns_matrix()`**: Calculates the row-aligned log-returns matrix for the HMM Baum-Welch training.

### 13.3 `hmm_analysis.py`
- **`prepare_hmm_features()`**: The critical "Feature Bridge." If you change the order of the 7 features here, you must re-train all models.
- **`detect_breakout()`**: The "Regime Arbiter." It combines Baum-Welch, the Entropy Gate, and the Oceanic Chop Filter.

### 13.4 `macro_bouncer.py`
- **`check_fundamental_gatekeeper()`**: Implements the 2s10s Bull-Steepener trap detection.
- **`get_macro_weight()`**: The "Gravity Curve" calculator. It outputs a continuous confidence multiplier ($0.5x$ to $1.5x$).

### 13.5 `sentiment_fetcher.py`
- **`get_realtime_sentiment_modifier()`**: Handles the SerpApi News engine and the 6-hour ultra-fresh temporal lock.
- **`calculate_nlp_sentiment_multiplier()`**: The FinBERT neural network mapping.

### 13.6 `rebalancer.py`
- **`optimize_portfolio_weights()`**: Uses Markowitz Modern Portfolio Theory (MPT) to find the Global Minimum Variance or Maximum Sharpe allocation among active signals.

---

## CHAPTER 14: THE "COLD BOOT" DIAGNOSTIC WORKFLOW

1.  **GPR Pulse**: Verified. Geopolitical Risk Index is within the $Z < 2.0$ safe zone.
2.  **1m Watchdog**: Verified. No jump events detected for the 100-candle 1-minute window.
3.  **HMM Warm-Start**: Models initialized via GMM to prevent degenerate local optima.
4.  **Signal Synchronization**: Loop 1 complete. `analysis_summary.csv` updated with 2026 temporal vectors.

---

## CHAPTER 15: DATA DICTIONARY & PERSISTENCE SCHEMA

To ensure cross-machine auditability, the system maintains two primary persistence files with the following schemas.

### 15.1 `analysis_summary.csv`
The real-time state of the 22-asset universe.
- **`Pair`**: Yahoo Ticker (e.g., `EURUSD=X`).
- **`Regime`**: {`Consolidation`, `Mean Reversion`, `Trend Breakout`}.
- **`Direction`**: {`LONG`, `SHORT`, `None`}.
- **`Cluster`**: Correlation group index (0-7).
- **`Macro_Weight`**: The "Gravity Curve" multiplier (e.g., `1.05x`).
- **`Warnings`**: A comma-separated list of active Vetoes (e.g., `XGBoost AI Veto`, `NLP Sentiment: 0.72x`).

### 15.2 `trade_tracker.json`
The institutional state-machine for open positions.
- **`entry_price`**: Execution price.
- **`stop_loss`**: Defensive exit (Calculated via 1.5x ATR).
- **`take_profit`**: Objective exit (Calculated via 2.5x ATR).
- **`active_veto`**: Boolean flag indicating if a manual or automated override is in place.

---
*EOF - 2026 Institutional Specification (v5.0-Ultimate)*
