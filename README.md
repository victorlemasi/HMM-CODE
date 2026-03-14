# Currency Pair Scanner & Analysis

A quantitative tool to scan multiple currency pairs using Clustering for asset grouping and Hidden Markov Models (HMM) for breakout state detection.

## Features
- **Data Acquisition**: Fetches 70 days of hourly historical data via `yfinance`.
- **Clustering**: Groups assets with similar price action using Hierarchical Clustering.
- **Breakout Detection**: Uses a 3-state Gaussian HMM (Consolidation, Mean Reversion, Trend Breakout) for regime detection.
- **Daily Retraining**: Automatically fits a new model every 24 hours (or per run) using a 1,200-bar "Goldilocks" window to stay relevant to current market conditions.
- **Dynamic ATR Thresholds**: Adaptive volatility filters that scale based on the asset type (FX vs Commodities).
- **Geopolitical Risk (GPR) Overlay**: Integrates the Geopolitical Risk Index to adjust risk thresholds.
- **Visualization**: Generates a correlation heatmap of the clusters.
13: 
14: ## Macro Intelligence (War-Time Strategy)
15: 
16: The scanner utilizes a "Macro-First" approach to filter technical signals based on global market conditions, specifically tuned for the volatile March 2026 environment.
17: 
18: ### 1. The Majors (EURUSD & GBPUSD)
19: - **Yield Spread Momentum**: Blocks long signals if US 10-Year yields are rising faster than European/UK counterparts, anticipating USD dominance.
20: - **DXY Velocity Switch**: A panic-mode filter that locks majors to "Bearish Only" if the US Dollar Index (DXY) spikes >0.25% in a single day.
21: 
22: ### 2. Gold (GC=F) — War_Scalp_4H
23: - **Real Yield Filter**: Detects "Liquidity Traps" by blocking longs if yields (^TNX) and DXY are rising simultaneously.
24: - **4-Hour Hard Exit**: Mandatory exit after 4 hours to capture geopolitical risk spikes while avoiding subsequent yield pressure reversals.
25: 
26: ### 3. Oil (CL=F) — Geopolitical Sensor
27: - **DXY Stress Mode**: Automatically switches to "Scalp Mode" (1:1 Risk/Reward) if DXY > 100.50.
28: - **Time-Decay Exit**: 4-hour hard exit limit to protect against "Strategic Reserve Release" flash gaps.
29: - **Energy-Yen Correlation Filter**: Vetos "Long JPY" trades (Short USDJPY, EURJPY, etc.) if Oil ATR spikes > 2% in 4 hours.
29: 
30: ### 4. Global Risk Sensors
31: - **DXY Master Pivot**: Defensive stance triggered if DXY crosses the 100.40 psychological wall.
32: - **Brent Oil Gauge**: Tightens stops across the portfolio if Brent Crude exceeds $98/bbl.
33: - **Sentiment Filter**: Integrates Real-time Fear & Greed sentiment to suppress reversal signals during extreme panic.
- **RBNZ Bias Filter (Automated Carry Protection)**: Uses **FRED (St. Louis Fed)** data to fetch real NZ 10Y Yields (`IRLTLT01NZM156N`). If yields indicate a hawkish regime (>3.0%), the system automatically blocks high-cost "Short NZD" signals (e.g., Short NZDJPY) to avoid negative carry and capitalize on yield-attraction flows.
34: 

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory.

2. **Set up a Virtual Environment (Recommended)**:
   We recommend using Python 3.12 to avoid compilation issues with `hmmlearn`.
   ```powershell
   # Use the Python Launcher to specify version 3.12
   py -3.12 -m venv .venv312
   .\.venv312\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

1. **Activate the virtual environment**:
   ```powershell
   .\.venv312\Scripts\Activate.ps1
   ```

2. **Run the analysis**:
   ```powershell
   python main.py
   ```

## Training

The HMM model is designed for **Daily Retraining** to prevent model drift.

### Automatic Training
The training process is fully automated. Every time you run `python main.py`:
1.  The scanner fetches the last 70 days of hourly data.
2.  It slices the data to the most recent **1,200 hourly bars** (approx. 2 months).
3.  A new Gaussian HMM is fitted to this data for each currency pair.

### Manual Retraining / Backtesting
To evaluate the model's training performance on historical data, run the walk-forward backtester:
```powershell
python backtest.py
```
This script simulates the daily retraining process over 6 months of historical data.

## Troubleshooting

### `hmmlearn` Installation Error
If you see an error like `Microsoft Visual C++ 14.0 or greater is required` when installing `hmmlearn`, it means there is no pre-built binary wheel for your Python version (likely Python 3.13 or 3.14), and `pip` is trying to compile it from source.

**Recommended Fixes:**
1. **Use Python 3.12**: This is the most stable version for data science libraries. Pre-built wheels are available, so you won't need to compile anything.
   - Create a new environment with Python 3.12: `python3.12 -m venv .venv`
2. **Install Microsoft C++ Build Tools**:
   - Download them from [here](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
   - Select "Desktop development with C++" during installation.
3. **Try a pre-built wheel**:
   - For some versions, you might find a wheel on [conda-forge](https://anaconda.org/conda-forge/hmmlearn) if you use Conda.

### `xlrd` Missing Dependency
If you see an error like `Missing optional dependency 'xlrd'`, ensure you have installed all requirements:
```powershell
pip install xlrd
```
This is required for reading the Geopolitical Risk data in Excel format.

## Output
- `correlation_clusters.png`: A heatmap showing the correlation between currency pairs, ordered by clusters.
- `analysis_summary.csv`: A CSV file containing the cluster ID and the HMM state (BREAKOUT or Normal) for each pair.
- Console output: Detailed summary of the scan results.

## Configuration
You can modify `config.py` to change the list of currency pairs, the timeframe (`INTERVAL`, `PERIOD`), or the model parameters (`N_CLUSTERS`, `HMM_COMPONENTS`).
