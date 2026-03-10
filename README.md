# Currency Pair Scanner & Analysis

A quantitative tool to scan multiple currency pairs using Clustering for asset grouping and Hidden Markov Models (HMM) for breakout state detection.

## Features
- **Data Acquisition**: Fetches hourly historical data for 20 currency pairs using `yfinance`.
- **Clustering**: Groups assets with similar price action using Hierarchical Clustering.
- **Breakout Detection**: Uses a 3-state Gaussian HMM (Stable, Trend, Breakout) to identify the current market regime for each pair.
- **Visualization**: Generates a correlation heatmap of the clusters.

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

## Output
- `correlation_clusters.png`: A heatmap showing the correlation between currency pairs, ordered by clusters.
- `analysis_summary.csv`: A CSV file containing the cluster ID and the HMM state (BREAKOUT or Normal) for each pair.
- Console output: Detailed summary of the scan results.

## Configuration
You can modify `config.py` to change the list of currency pairs, the timeframe (`INTERVAL`, `PERIOD`), or the model parameters (`N_CLUSTERS`, `HMM_COMPONENTS`).
