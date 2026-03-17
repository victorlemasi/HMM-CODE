"""
backtest.py - Standalone Walk-Forward Backtest for HMM Regime Strategy
=======================================================================
This script is completely independent from main.py.
It reuses data_fetcher.py and hmm_analysis.py to simulate historical
HMM-based trades and measure strategy performance.

Strategy Logic:
  - Walk-forward: Train HMM on a rolling window, then trade the NEXT bar.
  - ENTER LONG  when regime is 'Breakout'  with direction LONG
  - ENTER SHORT when regime is 'Breakout'  with direction SHORT
  - ENTER LONG  when regime is 'Trend'     with direction LONG
  - ENTER SHORT when regime is 'Trend'     with direction SHORT
  - EXIT (flat) when regime is 'Stable' or 'Consolidation'

Output:
  - Console: Per-pair summary + aggregate stats
  - File:    backtest_results.csv
"""

import warnings
import numpy as np
import pandas as pd
from datetime import datetime

# Suppress hmmlearn convergence noise
warnings.filterwarnings("ignore")

# Reuse existing project modules (read-only, no changes needed)
from data_fetcher import fetch_data, get_macro_data
from hmm_analysis import detect_breakout, get_dynamic_exit_levels, calculate_atr, get_trigger_price, calculate_z_score, calculate_mahalanobis_distance
from macro_bouncer import check_fundamental_gatekeeper, get_macro_weight
from config import CURRENCY_PAIRS, MAJORS_FIX_LIST, WATCHDOG_TICKERS, WATCHDOG_JUMP_THRESHOLDS, LUNCH_ZONE, MAJORS_MIN_CONFIDENCE

# ─── Configuration ─────────────────────────────────────────────────────────────
BACKTEST_PERIOD = "6mo"          # Historical data to fetch
BACKTEST_INTERVAL = "1h"         # Bar interval
TRAIN_WINDOW = 1200               # Bars used to train HMM before each signal (Goldilocks zone)
STEP_SIZE = 24                   # Re-fit HMM every N bars (24 = daily)
TRANSACTION_COST = 0.0002        # 2 pips per round trip (cost per trade)
# ──────────────────────────────────────────────────────────────────────────────


def run_backtest_for_pair(symbol: str, df: pd.DataFrame, macro_data: dict = None) -> dict:
    """
    Runs a walk-forward backtest for a single currency pair.
    Returns a dict of performance metrics.
    """
    if df is None or len(df) < TRAIN_WINDOW + STEP_SIZE:
        return None

    # Pre-compute log returns and ATR for the full series
    df['Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['ATR'] = calculate_atr(df)
    df = df.dropna()

    total_bars = len(df)
    trades = []
    position = 0          # 1 = long, -1 = short, 0 = flat
    entry_price = None
    entry_tp = None
    entry_sl = None
    entry_regime = None
    entry_bar_idx = None

    # Walk-forward loop
    for t in range(TRAIN_WINDOW, total_bars, STEP_SIZE):
        train_slice = df.iloc[t - TRAIN_WINDOW:t].copy()

        try:
            is_breakout, direction, regime, _, current_atr, prob = detect_breakout(train_slice, ticker=symbol, macro_data=macro_data)
        except Exception:
            continue

        desired = 0
        if regime in ('Trend Breakout', 'Mean Reversion'):
            direction_hmm = 'LONG' if direction == 'LONG' else 'SHORT'
            
            # --- APPLY MACRO WEIGHTING (Stochastic Logic) ---
            macro_weight = get_macro_weight(symbol, direction_hmm, macro_data)
            adjusted_prob = prob * macro_weight
            
            # --- LULL PENALTY (Efficiency Equilibrium) ---
            current_dt = df.index[t]
            hour = current_dt.hour
            is_major = symbol in MAJORS_FIX_LIST
            
            conf_thresh = MAJORS_MIN_CONFIDENCE if is_major else 0.7
            if is_major and LUNCH_ZONE[0] <= hour < LUNCH_ZONE[1]:
                conf_thresh = 0.90 # Extreme confidence required during London Lunch
            
            if adjusted_prob < conf_thresh:
                desired = 0
            else:
                # --- APPLY THE FUNDAMENTAL BOUNCER (Global Gatekeeper) ---
                macro_bias = check_fundamental_gatekeeper(symbol, df.index[t], macro_data)
                
                if "BEARISH_BIAS" in macro_bias and direction_hmm == "LONG":
                    desired = 0 
                elif "BULLISH_BIAS" in macro_bias and direction_hmm == "SHORT":
                    desired = 0 
                else:
                    desired = 1 if direction_hmm == 'LONG' else -1
        
        # --- SIMULATED WATCHDOG (Audit Sync) ---
        if symbol in WATCHDOG_TICKERS and desired != 0:
            if symbol == "GC=F":
                score = calculate_mahalanobis_distance(df.iloc[max(0, t-20):t+1])
            else:
                score = calculate_z_score(df['Close'].iloc[max(0, t-100):t+1])
                
            threshold = WATCHDOG_JUMP_THRESHOLDS.get(symbol, WATCHDOG_JUMP_THRESHOLDS['DEFAULT'])
            if abs(score) > threshold:
                desired = 0

        # Calculate levels for the NEW desired position
        current_price = df['Close'].iloc[t]
        macro_bias_val = check_fundamental_gatekeeper(symbol, df.index[t], macro_data) if desired != 0 else ""
        
        # Determine macro phase for trigger logic
        from main import check_macro_alignment
        macro_phase = check_macro_alignment(symbol, direction_hmm, macro_data) if desired != 0 else "TRAP_PHASE"
        
        is_scalp_active = (symbol == "CL=F" and "SCALP_ONLY" in macro_bias_val)
        tp_level, sl_level = get_dynamic_exit_levels(regime, current_price, current_atr, direction, ticker=symbol, is_scalp=is_scalp_active)
        
        # --- REGIME SHIFT EXIT ---
        if position != 0 and regime not in ('Trend Breakout', 'Mean Reversion'):
            exit_price = current_price
            raw_ret = position * (exit_price / entry_price - 1)
            net_ret = raw_ret - TRANSACTION_COST
            trades.append({
                'Ticker': symbol, 'Entry_Bar': entry_bar_idx, 'Exit_Bar': t,
                'Position': 'LONG' if position == 1 else 'SHORT',
                'Entry_Price': entry_price, 'Exit_Price': exit_price,
                'Regime': entry_regime, 'Net_Return': net_ret, 'Exit_Reason': 'REGIME_SHIFT'
            })
            position = 0; entry_price = None
        
        # 1.2 Candle Filter: Calculate Trigger Price for Majors
        trigger_price = None
        if symbol in MAJORS_FIX_LIST and regime == "Trend Breakout" and direction != "None":
            trigger_price = get_trigger_price(df.iloc[:t], regime, direction, current_atr, macro_phase=macro_phase)

        # ── Intra-step Simulation ──────────────────────────────────────────
        for sub_t in range(t, min(t + STEP_SIZE, total_bars)):
            high = df['High'].iloc[sub_t]
            low = df['Low'].iloc[sub_t]
            close = df['Close'].iloc[sub_t]

            # If we had a position, check for exit
            if position != 0:
                # --- WAR-TIME OVERRIDE: Time Limits (OIL: 4h, GOLD: 8h) ---
                time_limit = 8 if symbol == "GC=F" else 4
                if (symbol == "CL=F" or symbol == "GC=F") and (sub_t - entry_bar_idx) >= time_limit:
                    exit_reason = "TIME_EXIT"
                    exit_price = close
                    raw_ret = position * (exit_price / entry_price - 1)
                    net_ret = raw_ret - TRANSACTION_COST
                    trades.append({
                        'Ticker': symbol, 'Entry_Bar': entry_bar_idx, 'Exit_Bar': sub_t,
                        'Position': 'LONG' if position == 1 else 'SHORT',
                        'Entry_Price': entry_price, 'Exit_Price': exit_price,
                        'Regime': entry_regime, 'Net_Return': net_ret, 'Exit_Reason': exit_reason
                    })
                    position = 0; entry_price = None
                    continue

                # --- PARABOLIC SAR TRAILING STOPS (Efficiency Equilibrium) ---
                if symbol == "EURUSD=X":
                    pnl_atr = (close - entry_price) / current_atr if position == 1 else (entry_price - close) / current_atr
                    if pnl_atr > 0.5:
                        move = pnl_atr * 0.5 * current_atr
                        new_sl = entry_price + move if position == 1 else entry_price - move
                        entry_sl = max(entry_sl, new_sl) if position == 1 else min(entry_sl, new_sl)

                hit_tp = (position == 1 and high >= entry_tp) or (position == -1 and low <= entry_tp)
                hit_sl = (position == 1 and low <= entry_sl) or (position == -1 and high >= entry_sl)

                if hit_tp or hit_sl:
                    exit_price = entry_tp if hit_tp else entry_sl
                    raw_ret = position * (exit_price / entry_price - 1)
                    net_ret = raw_ret - TRANSACTION_COST
                    trades.append({
                        'Ticker': symbol,
                        'Entry_Bar': entry_bar_idx,
                        'Exit_Bar': sub_t,
                        'Position': 'LONG' if position == 1 else 'SHORT',
                        'Entry_Price': entry_price,
                        'Exit_Price': exit_price,
                        'Regime': entry_regime,
                        'Net_Return': net_ret,
                        'Exit_Reason': 'TP' if hit_tp else 'SL'
                    })
                    position = 0
                    entry_price = None

            # If flat, check if we should enter Based on the HMM signal from start of step
            if position == 0 and desired != 0:
                can_enter = True
                if trigger_price:
                    # --- SIGNAL EXPIRY (Differentiated: 3 bars FX / 2 bars Commodities) ---
                    expiry_offset = 2 if symbol.endswith("=X") else 1 
                    if sub_t <= t + expiry_offset:
                        can_enter = (high >= trigger_price) if desired == 1 else (low <= trigger_price)
                        if not can_enter and sub_t == t + expiry_offset:
                            desired = 0 # Cancel if not hit within limit
                    else:
                        can_enter = False
                
                if can_enter:
                    # --- WAR-TIME OVERRIDE: SCALP MODE for OIL ---
                    if symbol == "CL=F" and macro_bias_val == "SCALP_ONLY":
                        risk = current_atr * 2
                        entry_tp = current_price + (desired * risk)
                        entry_sl = current_price - (desired * risk)
                    else:
                        entry_tp = tp_level
                        entry_sl = sl_level

                    position = desired
                    entry_price = trigger_price if trigger_price else df['Close'].iloc[sub_t]
                    entry_regime = regime
                    entry_bar_idx = sub_t
                    desired = 0 

    if not trades:
        return {'ticker': symbol, 'trades': 0, 'total_return': 0,
                'win_rate': 0, 'max_drawdown': 0, 'sharpe': 0}

    df_trades = pd.DataFrame(trades)
    returns = df_trades['Net_Return'].values

    total_return = np.prod(1 + returns) - 1
    win_rate = np.mean(returns > 0)

    # Max drawdown using cumulative equity curve
    equity = np.cumprod(1 + returns)
    peak = np.maximum.accumulate(equity)
    drawdown = (equity - peak) / peak
    max_drawdown = drawdown.min()

    # Annualised Sharpe (assuming 1h bars → ~8760 bars/year)
    if returns.std() > 0:
        sharpe = (returns.mean() / returns.std()) * np.sqrt(8760 / STEP_SIZE)
    else:
        sharpe = 0

    return {
        'ticker': symbol,
        'trades': len(trades),
        'total_return': total_return,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'sharpe': sharpe,
        'trade_log': df_trades
    }


def main():
    print("=" * 60)
    print("  HMM Regime Strategy — Walk-Forward Backtest")
    print(f"  Period: {BACKTEST_PERIOD} | Interval: {BACKTEST_INTERVAL}")
    print(f"  Train Window: {TRAIN_WINDOW} bars | Step: {STEP_SIZE} bars")
    print("=" * 60)

    # Fetch all data upfront as a batch
    print("\nFetching historical data for all pairs...")
    all_market_data = fetch_data(CURRENCY_PAIRS, period=BACKTEST_PERIOD, interval=BACKTEST_INTERVAL)
    
    print("\nTracing macro context (Yields/Commodities)...")
    macro_context = get_macro_data(interval=BACKTEST_INTERVAL, period=BACKTEST_PERIOD)
    print(f"Data ready for {len(all_market_data)} pairs and macro context.\n")

    backtest_summaries = []
    all_trade_logs = []

    for active_symbol in CURRENCY_PAIRS:
        if active_symbol not in all_market_data:
            print(f"  {active_symbol}: SKIPPED (fetch failed)")
            continue

        print(f"  Backtesting {active_symbol}...", end=" ", flush=True)
        result = run_backtest_for_pair(active_symbol, all_market_data[active_symbol], macro_data=macro_context)
        if result is None:
            print("SKIPPED (insufficient data)")
            continue

        print(
            f"Trades: {result['trades']:>3} | "
            f"Return: {result['total_return']:>+.2%} | "
            f"Win Rate: {result['win_rate']:.0%} | "
            f"MaxDD: {result['max_drawdown']:.2%} | "
            f"Sharpe: {result['sharpe']:.2f}"
        )

        backtest_summaries.append({
            'Ticker': result['ticker'],
            'Trades': result['trades'],
            'Total_Return_%': round(result['total_return'] * 100, 2),
            'Win_Rate_%': round(result['win_rate'] * 100, 1),
            'Max_Drawdown_%': round(result['max_drawdown'] * 100, 2),
            'Sharpe_Ratio': round(result['sharpe'], 2),
        })

        if result.get('trade_log') is not None:
            all_trade_logs.append(result['trade_log'])

    if not backtest_summaries:
        print("\nNo results to report.")
        return

    # ── Aggregate Summary ───────────────────────────────────────────────────
    final_summary_df = pd.DataFrame(backtest_summaries).sort_values('Total_Return_%', ascending=False)

    print("\n" + "=" * 60)
    print("  AGGREGATE RESULTS (sorted by return)")
    print("=" * 60)
    print(final_summary_df.to_string(index=False))

    print("\n--- Portfolio Averages ---")
    print(f"  Total Trades    : {final_summary_df['Trades'].sum()}")
    print(f"  Avg Return      : {final_summary_df['Total_Return_%'].mean():+.2f}%")
    print(f"  Avg Win Rate    : {final_summary_df['Win_Rate_%'].mean():.1f}%")
    print(f"  Avg Max Drawdown: {final_summary_df['Max_Drawdown_%'].mean():.2f}%")
    print(f"  Avg Sharpe Ratio: {final_summary_df['Sharpe_Ratio'].mean():.2f}")

    # ── Save Results ────────────────────────────────────────────────────────
    final_summary_df.to_csv('backtest_results.csv', index=False)
    if all_trade_logs:
        pd.concat(all_trade_logs, ignore_index=True).to_csv('backtest_trade_log.csv', index=False)

    print(f"\n  Results saved to 'backtest_results.csv' and 'backtest_trade_log.csv'.")
    print("=" * 60)


if __name__ == "__main__":
    main()
