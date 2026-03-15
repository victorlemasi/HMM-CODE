# Stochastic Trading Bot & Macro Scanner

An advanced quantitative trading bot that blends **Hidden Markov Models (HMM)** for regime detection with a **Fundamental Gatekeeper (The Bouncer)** for macro-economic alignment. Optimized for 22 instruments including Majors, Crosses, Gold, and Oil.

## 🚀 Key Features

### 1. Stochastic Regime Logic
- **HMM Breakout Detection**: Uses a 3-state Gaussian HMM (Consolidation, Mean Reversion, Trend Breakout) with a **0.6 Confidence Threshold**.
- **Dynamic Confidence Weighting**: Signals are weighted by central bank policy rate differentials and yield spread momentum.
- **Detailed Signal Warnings**: Signals rejected by the gatekeeper are now tagged with the specific reason (e.g., `SHORT (WARNING: Macro Bias)` or `LONG (WARNING: Low Confidence)`).
- **Statistical Separation Guard**: Rejects weak breakouts if the regime's return separation is less than **0.2x ATR (Gold)** or **0.15x ATR (FX)**.

### 2. The "Jump-Diffusion" Watchdog
- **1-Minute Circuit Breaker**: Polls high-volatility assets every 60 seconds.
- **Lévy Process Filter**: Uses Z-Score analysis to detect market shocks (>3-4.5 SD).
- **Persistent Pause**: Automatically locks trading for 15 minutes via `watchdog_pause.lock` during shocks.

### 3. "War-Time" Strategy Overrides
- **Oil (CL=F)**: Uses DXY-inverse momentum and a **Hard 4-Hour Time Exit** to avoid gap risk.
- **Gold (GC=F)**: Restore Benchmark (+4.72% Verified). Exempt from time limits to allow structural trends to breathe. Uses **DXY as an internal HMM feature**.
- **Scalp Mode**: Automatically tightens Stop Loss and Take Profit to a **1:1 ratio** when the DXY is in a "Neutral Danger Zone."

### 4. FRED Data Unification
- **Zero-Lag Macro**: Fetches yields (UK, GER, US) and Policy Rates (NZ, UK, US, EUR) directly from **FRED** for maximum reliability.
- **Spread Momentum**: Analyzes 10Y yield spreads to distinguish "Win Phases" from "Macro Traps."

## 📈 Audited Performance (6-Month Walk-Forward)
| Asset | Trades | Total Return % | Win Rate % | Sharpe |
| :--- | :--- | :--- | :--- | :--- |
| **GC=F (Gold)** | 3 | **+4.72%** | **66.7%** | 15.30 |
| **EURUSD=X** | 1 | **+0.45%** | 100.0% | 0.00 |
| **GBPUSD=X** | 1 | **+0.11%** | 100.0% | 0.00 |
| **CL=F (Oil)** | 9 | **+2.18%** | 77.8% | 17.47 |

## 📁 System Files
- `watchdog_pause.lock`: Persistent timestamp for jump-detection pauses.
- `trade_tracker.json`: Tracks signal duration for the 4-hour Oil exit.
- `macro_bouncer.py`: The global hybrid gatekeeper logic for all 22 assets.
- `hmm_analysis.py`: Core machine learning and ATR-based filtering.

## 🛠️ Usage
1. **Live Scanner**: `python main.py` (Retrains models every 24 hours).
2. **Backtester**: `python backtest.py` (Runs 6-month walk-forward simulation).

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
