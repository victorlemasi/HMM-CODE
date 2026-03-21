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
from hmm_analysis import calculate_rsi, calculate_atr

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
N_FEATURES = 6  # MUST match hmm_analysis.py — do not change independently


def prepare_features(df: pd.DataFrame, ticker: str, macro_data: dict) -> np.ndarray | None:
    """
    Canonical feature engineering.
    MUST produce exactly N_FEATURES columns — identical to detect_breakout() in hmm_analysis.py.

    Feature layout (fixed order):
      0: Returns      — log price return
      1: Volatility   — 10-bar rolling std of returns
      2: Range        — (High-Low)/Close
      3: Momentum     — 5-bar minus 20-bar rolling return avg
      4: RSI          — 14-period RSI
      5: Spec_Feat    — asset-specific macro signal (zero-padded if unavailable)
    """
    df = df.copy()
    df['Returns']    = np.log(df['Close'] / df['Close'].shift(1))
    df['Range']      = (df['High'] - df['Low']) / df['Close']
    df['Volatility'] = df['Returns'].rolling(window=10).std()
    df['Momentum']   = df['Returns'].rolling(window=5).mean() - df['Returns'].rolling(window=20).mean()
    df['RSI']        = calculate_rsi(df['Close'])
    df['Spec_Feat']  = 0.0  # default — overwritten below if macro available

    features_cols = ['Returns', 'Volatility', 'Range', 'Momentum', 'RSI', 'Spec_Feat']

    # ── Macro enrichment (best-effort, never raises) ─────────────────────────
    if ticker in ASSET_MAPPINGS and macro_data:
        mapping  = ASSET_MAPPINGS[ticker]
        m_type   = mapping['type']
        m_key    = mapping.get('key')

        # Normalise datetime index to tz-naive ns precision for safe reindex
        def _norm_idx(frame: pd.DataFrame) -> pd.DataFrame:
            idx = pd.to_datetime(frame.index)
            if idx.tzinfo is not None:
                idx = idx.tz_localize(None)
            if hasattr(idx, 'as_unit'):
                idx = idx.as_unit('ns')
            frame = frame.copy()
            frame.index = idx
            return frame

        df = _norm_idx(df)
        price_idx = df.index

        try:
            if m_type == 'commodity':
                com_ticker = COMMODITY_TICKERS.get(m_key)
                if com_ticker and com_ticker in macro_data and not macro_data[com_ticker].empty:
                    com = _norm_idx(macro_data[com_ticker]).reindex(price_idx, method='ffill').bfill()
                    com_ret = np.log(com['Close'] / com['Close'].shift(1))
                    df['Spec_Feat'] = com_ret.rolling(20).corr(df['Returns']).fillna(0)

            elif m_type == 'yield':
                y_ticker = YIELD_TICKERS.get(m_key)
                if y_ticker and y_ticker in macro_data and not macro_data[y_ticker].empty:
                    y = _norm_idx(macro_data[y_ticker]).reindex(price_idx, method='ffill').bfill()
                    df['Spec_Feat'] = y['Close'].fillna(0)

            elif m_type == 'macro':
                base_key   = mapping['base']
                quote_key  = mapping['quote']
                base_t     = YIELD_TICKERS.get(base_key)  or FRED_TICKERS.get(base_key)
                quote_t    = YIELD_TICKERS.get(quote_key) or FRED_TICKERS.get(quote_key)
                dxy_t      = YIELD_TICKERS.get('DXY')

                if (base_t  and base_t  in macro_data and not macro_data[base_t].empty and
                    quote_t and quote_t in macro_data and not macro_data[quote_t].empty):
                    base_a  = _norm_idx(macro_data[base_t]).reindex(price_idx, method='ffill').bfill()
                    quote_a = _norm_idx(macro_data[quote_t]).reindex(price_idx, method='ffill').bfill()
                    spread  = base_a['Close'] - quote_a['Close']

                    # Try 2s10s spread ROC (most informative)
                    is_eur   = ticker.startswith("EUR")
                    two_y_t  = FRED_2Y_TICKERS.get('GER2Y' if is_eur else 'UK2Y')
                    if two_y_t and two_y_t in macro_data and not macro_data[two_y_t].empty:
                        two_y_a = _norm_idx(macro_data[two_y_t]).reindex(price_idx, method='ffill').bfill()
                        spread_2s10s = base_a['Close'] - two_y_a['Close']
                        df['Spec_Feat'] = spread_2s10s.diff(5).fillna(0)
                    else:
                        df['Spec_Feat'] = spread.fillna(0)

                elif dxy_t and dxy_t in macro_data and not macro_data[dxy_t].empty:
                    dxy_a = _norm_idx(macro_data[dxy_t]).reindex(price_idx, method='ffill').bfill()
                    df['Spec_Feat'] = (-dxy_a['Close']).fillna(0)

            elif m_type == 'commodity_inverse':
                dxy_t = YIELD_TICKERS.get('DXY')
                if dxy_t and dxy_t in macro_data and not macro_data[dxy_t].empty:
                    dxy_a = _norm_idx(macro_data[dxy_t]).reindex(price_idx, method='ffill').bfill()
                    df['Spec_Feat'] = dxy_a['Close'].rolling(20).corr(df['Returns']).fillna(0)

        except Exception as macro_err:
            logger.debug(f"  Macro enrichment failed for {ticker}: {macro_err} — using zero padding")
            df['Spec_Feat'] = 0.0

    # Fill any residual NaNs in core features before dropna
    for col in features_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill().fillna(0)

    df = df.dropna(subset=features_cols)
    if df.empty:
        return None

    return df[features_cols].values  # shape: (N, N_FEATURES=6)


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
