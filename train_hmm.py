"""
train_hmm.py - Offline Baum-Welch HMM Training
=================================================
Fetches 2 years of historical data for all pairs, engineers identical
features to hmm_analysis.py, and trains a GaussianHMM for each asset.
Saves model + scaler to hmm_models/.

Usage:
    python train_hmm.py

This script produces .pkl files that are loaded by hmm_analysis.py
during backtesting and live execution via Transfer Learning.
"""
import os
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

from config import (
    CURRENCY_PAIRS, INTERVAL, HMM_TRAIN_PERIOD, HMM_MODELS_PATH,
    HMM_COMPONENTS, HMM_N_ITER, HMM_COVARS_PRIOR, HMM_MIN_COVAR,
    ASSET_N_COMPONENTS, ASSET_MAPPINGS,
    COMMODITY_TICKERS, YIELD_TICKERS, FRED_TICKERS, FRED_2Y_TICKERS
)
from data_fetcher import fetch_data, get_macro_data
from hmm_analysis import calculate_rsi, calculate_atr, prepare_hmm_features

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
N_FEATURES = 6  # MUST match hmm_analysis.py — do not change independently


def prepare_features(df: pd.DataFrame, ticker: str, macro_data: dict) -> np.ndarray | None:
    """
    Wrapper for centralized feature engineering.
    """
    return prepare_hmm_features(df, ticker, macro_data)


from joblib import Parallel, delayed

def train_single_ticker(ticker, price_data, macro_data):
    """
    Trains a single HMM model for a given ticker.
    Returns (success, ticker, n_features, n_components, model_file) or (False, ticker, error_msg).
    """
    if ticker not in price_data or price_data[ticker] is None or price_data[ticker].empty:
        return False, ticker, "No data"

    features = prepare_features(price_data[ticker], ticker, macro_data)

    if features is None or len(features) < 200:
        return False, ticker, f"Insufficient features ({len(features) if features is not None else 0} rows)"

    if features.shape[1] != N_FEATURES:
        return False, ticker, f"Feature count mismatch: got {features.shape[1]}, expected {N_FEATURES}"

    try:
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        n_components = ASSET_N_COMPONENTS.get(ticker, ASSET_N_COMPONENTS.get('DEFAULT', 3))

        model = GaussianHMM(
            n_components=n_components,
            covariance_type="diag",
            n_iter=HMM_N_ITER,
            tol=1e-3,
            random_state=42,
            covars_prior=HMM_COVARS_PRIOR,
            min_covar=HMM_MIN_COVAR,
            init_params="stmc",
            params="stmc",
        )
        model.fit(features_scaled)

        # Validate — reject degenerate models
        if np.isnan(model.transmat_).any() or np.isnan(model.means_).any():
            return False, ticker, "NaN in model params after fit"

        model_file = os.path.join(
            HMM_MODELS_PATH,
            f"{ticker.replace('=X', '').replace('=F', '')}_hmm.pkl"
        )

        with open(model_file, 'wb') as fh:
            pickle.dump({'model': model, 'scaler': scaler, 'n_features': N_FEATURES}, fh)

        return True, ticker, N_FEATURES, n_components, model_file, len(features)

    except Exception as e:
        return False, ticker, str(e)

def train_all_models():
    """
    Main training loop: fetch 2-year history, engineer features, run Baum-Welch,
    and save model + scaler for each asset.
    """
    os.makedirs(HMM_MODELS_PATH, exist_ok=True)
    from config import HMM_TRAIN_CORES
    
    logger.info(f"Fetching {HMM_TRAIN_PERIOD} of historical data for {len(CURRENCY_PAIRS)} pairs...")

    price_data = fetch_data(CURRENCY_PAIRS, interval=INTERVAL, period=HMM_TRAIN_PERIOD)
    macro_data = get_macro_data(interval=INTERVAL, period=HMM_TRAIN_PERIOD)

    logger.info(f"Starting parallel training with {HMM_TRAIN_CORES} cores...")
    
    results = Parallel(n_jobs=HMM_TRAIN_CORES)(
        delayed(train_single_ticker)(ticker, price_data, macro_data) 
        for ticker in CURRENCY_PAIRS
    )

    trained, skipped = 0, 0
    for res in results:
        success = res[0]
        ticker = res[1]
        
        if success:
            _, _, _, n_comp, model_file, n_bars = res
            logger.info(f"  ✓ {ticker}: {n_bars} bars, {n_comp} states → {model_file}")
            trained += 1
        else:
            reason = res[2]
            logger.warning(f"  ✗ {ticker}: {reason}")
            skipped += 1

    logger.info(f"\nDone. Trained: {trained} | Skipped: {skipped}")


if __name__ == "__main__":
    train_all_models()
