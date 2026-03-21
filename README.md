# 🌐 Institutional HMM-Quant Phase 5 Node (March 2026)

This repository contains a high-conviction, multi-layer AI trading node designed for institutional-grade currency and commodity scanning. The system utilizes a **"Triple-Lock" Audit Architecture**, combining Unsupervised Learning (HMM), Supervised Ensembling (XGBoost), and Real-Time Sentiment (NLP) to detect and trade regime-shifts while aggressively vetoing liquidity traps.

---

## 🏗️ System Architecture: The "Triple-Lock" shield

The app operates via six distinct decision layers, ensuring that only the highest quality signals reach execution.

### 1. The Core Brain: HMM Regime Detection (`hmm_analysis.py`)
*   **Technology**: Gaussian Hidden Markov Models (Baum-Welch algorithm).
*   **Function**: Analyzes a 7-pillar feature vector (Returns, Volatility, RSI, Momentum, Range, Spec-Correlations, and Yield Spreads) to identify the "Hidden State" of the market.
*   **Regimes**: Categorizes price action into *Consolidation*, *Mean Reversion*, or *Trend Breakout*.

### 2. The AI Veto: XGBoost Ensemble Filter (`train_xgboost.py`)
*   **Technology**: Gradient Boosting Decision Trees.
*   **Function**: A supervised layer trained on 700 days of historical HMM performance. It predicts the "Success Probability" of a breakout.
*   **Utility**: If the HMM predicts a breakout but the XGBoost model identifies a signature of "Exhaustion," the trade is **Vetoed** to prevent trapping.

### 3. The Order Flow: Micro-CVD Engine (`micro_cvd_engine.py`)
*   **Technology**: High-Frequency Limit-Order Proxy (1-Minute Granularity).
*   **Function**: Calculates the slope of the Cumulative Volume Delta (CVD) over the last 60 minutes.
*   **Utility**: Detects "Hidden Selling" or "Hidden Buying" where institutional limit orders are absorbing aggressor volume, signaling an imminent reversal.

### 4. The Sentiment Gate: NLP FinBERT (`sentiment_fetcher.py`)
*   **Technology**: ProsusAI/FinBERT (Transformer Architecture).
*   **Function**: Scrapes real-time headlines via SerpApi (Google News) and scores them for sentiment.
*   **Constraint**: **Ultra-Freshness Filter** — Only news from the **last 6 hours** is considered to ensure the bot ignores stale narratives.

### 5. The Macro Bouncer: The Gravity Curve (`macro_bouncer.py`)
*   **Technology**: FRED Economic API integration.
*   **Function**: Tracks the **US 2s10s Yield Curve**.
*   **Veto Logic**: Detects "Bull-Steepeners" (recession signals) and applies the **Gravity Curve** multiplier to position sizes based on yield momentum.

### 6. The Execution Guard: Markowitz Rebalancer (`rebalancer.py`)
*   **Technology**: scipy-optimized Mean-Variance Optimization.
*   **Function**: If multiple pairs show signals, the bot calculates the **Efficient Frontier** to allocate weights that maximize the Sharpe Ratio and penalize covariance.

---

## 🛠️ Global Library Dependencies

| Library | Role |
| :--- | :--- |
| `hmmlearn` | The engine for regime detection and Baum-Welch training. |
| `xgboost` | The supervised ensemble layer for breakout verification. |
| `transformers` | Runs the **FinBERT** NLP model for sentiment analysis. |
| `torch` | Underlying backend for the Transformer models. |
| `yfinance` | Primary source for high-frequency OHLCV price data. |
| `fredapi` | Direct bridge to the Federal Reserve Economic Data (FRED). |
| `scipy` | Powers the Markowitz Portfolio Optimization (SLSQP solver). |
| `scikit-learn` | Used for feature scaling and GMM initialization of the HMM. |
| `pandas`/`numpy` | Core vectorization and data manipulation. |

---

## 🚀 Deployment & Installation

### 1. Clone & Environment
```bash
git clone https://github.com/[your-repo]/Currency-Pair-Scanner-Analysis
cd Currency-Pair-Scanner-Analysis
pip install -r requirements.txt
```

### 2. Secrets Management
Rename `.env.example` to `.env` and provide your keys:
- `FRED_API_KEY`: Required for Yield Curve and GPR monitoring.
- `SERPAPI_KEY`: Required for the 6-hour NLP news filter.

### 3. Training the Node
To sync the AI brain with the current 2026 market dynamics:
```bash
python train_hmm.py       # Trains the regime brain
python train_xgboost.py   # Trains the AI Veto layer
```

### 4. Execution
```bash
python main.py
```

---

## 🔍 Institutional Audit Summary (March 2026)
- **Time Sync**: Verified 100% temporal alignment with 2026 FRED and Yahoo feeds.
- **Traceability**: All NLP/XGBoost events are saved to `analysis_summary.csv` for remote auditing.
- **Stability**: Confirmed stable 300-second 42-asset duty cycle.

**Disclaimer**: *This node is a quantitative research tool. Trading involves significant risk of loss.*
