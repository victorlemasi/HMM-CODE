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

## Fundamental Gatekeepers (The Bouncer System)

The scanner utilizes a "Macro-First" approach to filter technical signals. Every technical breakout is passed through the `Fundamental Gatekeeper` in `backtest.py` to ensure it aligns with global market regimes.

### 1. Currency Gatekeepers
| Filter | Logic | Trigger | Action |
| :--- | :--- | :--- | :--- |
| **DXY Velocity** | Inter-day Dollar strength | DXY > 100.40 OR Daily Spike > 0.25% | Blocks all **LONG** Majors (EUR, GBP, AUD) |
| **RBNZ Bias** | Automated Carry Protection | NZ 10Y Yield > 3.0% (Hawkish) | Blocks **SHORT** NZD positions (e.g. NZDJPY Short) |
| **Yield Spread Gate** | Base vs US Yield Momentum | Δ-Spread > 5bps (5-day window) | Blocks trades if spread moves against technical signal |
| **Oil-JPY ATR** | Energy-driven Yen shocks | Oil ATR Spike > 2% (4-hour window) | Blocks **LONG JPY** positions (e.g. Short USDJPY) |

### 2. Commodity Gatekeepers
| Asset | Filter | Logic | Action |
| :--- | :--- | :--- | :--- |
| **Gold (GC=F)** | **Real Yield Trap** | DXY > 100.20 AND Yields Rising | Blocks Gold **LONGS** |
| **Gold (GC=F)** | **Time Constraint** | Period > 4 Hours | **Hard Exit** (Capture geopolitical spikes only) |
| **Oil (CL=F)** | **DXY Stress Mode** | DXY > 100.50 | Switches to **Scalp Mode** (1:1 Risk/Reward) |
| **Oil (CL=F)** | **Energy Wall** | Brent Crude > $98/bbl | Portfolio-wide Stop tightening |

### 3. Data Sources & Fallbacks
To ensure the Bouncer always has data, we use a hybrid fetching system:
- **Priority 1 (Live)**: Yahoo Finance Tickers (`^NZ10`, `^TNX`, `DX-Y.NYB`).
- **Priority 2 (Proxies)**: Bond ETFs for UK/GER yields (`IGLT.L`, `IEGA.DE`) where direct yield tickers are unstable.
- **Priority 3 (Historical)**: Direct **FRED CSV** downloads for robust backtesting coverage (e.g. `IRLTLT01NZM156N`).

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
