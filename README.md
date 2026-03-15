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

## Stochastic Logic & Macro Framework

The scanner has transitioned from Static Logic to **Stochastic/Adaptive Logic**, allowing it to handle market shocks and macro-economic regime shifts.

### 1. Jump-Diffusion Watchdog (Lévy Process)
A high-frequency 1-minute "Watchdog" monitors market shocks in real-time.
- **Circuit Breaker**: If price moves > 3-4.5 Standard Deviations (Z-Score) in 1 minute, the bot pauses all trading for 15 minutes.
- **Asset Specificity**: Thresholds are calibrated by asset (FX: 3.0, Gold: 3.5, Oil: 4.5) to account for natural volatility.

### 2. Macro-Weighted Confidence
Technical signals from the HMM are weighted by multi-dimensional macro factors before execution:
- **Policy Rate Differentials**: Signal confidence is boosted (+20%) or penalized (-20%) based on Central Bank hawkishness/dovishness (FRED Data).
- **DXY Inverse Coupling**: Oil (`CL=F`) signals are weighted against US Dollar momentum to avoid "Macro Traps."
- **Confidence Threshold**: Any signal with an adjusted probability < 0.6 is automatically vetoed (labeled with ⚠️ in output).

### 3. Data Sources (FRED & Yahoo Hybrid)
We use a robust fetching architecture to bypass Yahoo Finance yield instability:
- **Central Bank Rates (FRED)**: `FEDFUNDS` (USD), `ECBMRRFR` (EUR), `IRSTCI01JPM156N` (JPY), etc.
- **10Y Yields (FRED)**: `IRLTLT01DEM156N` (GER), `IRLTLT01GBM156N` (UK), `IRLTLT01NZM156N` (NZ).
- **Technical/Volatility (Yahoo)**: 1h price bars for technical clustering and HMM modeling.

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
