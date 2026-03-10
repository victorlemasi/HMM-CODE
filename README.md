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
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

1. **Activate the virtual environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Run the analysis**:
   ```powershell
   python main.py
   ```

## Output
- `correlation_clusters.png`: A heatmap showing the correlation between currency pairs, ordered by clusters.
- `analysis_summary.csv`: A CSV file containing the cluster ID and the HMM state (BREAKOUT or Normal) for each pair.
- Console output: Detailed summary of the scan results.

## Configuration
You can modify `config.py` to change the list of currency pairs, the timeframe (`INTERVAL`, `PERIOD`), or the model parameters (`N_CLUSTERS`, `HMM_COMPONENTS`).
