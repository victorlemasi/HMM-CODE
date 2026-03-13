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
from hmm_analysis import detect_breakout, get_dynamic_exit_levels, calculate_atr, get_trigger_price
from config import CURRENCY_PAIRS, MAJORS_ENTRY_FILTER

# ─── Configuration ─────────────────────────────────────────────────────────────
BACKTEST_PERIOD = "6mo"          # Historical data to fetch
BACKTEST_INTERVAL = "1h"         # Bar interval
TRAIN_WINDOW = 1200               # Bars used to train HMM before each signal (Goldilocks zone)
STEP_SIZE = 24                   # Re-fit HMM every N bars (24 = daily)
TRANSACTION_COST = 0.0002        # 2 pips per round trip (cost per trade)
# ──────────────────────────────────────────────────────────────────────────────


def run_backtest_for_pair(ticker: str, df: pd.DataFrame, macro_data: dict = None) -> dict:
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

    # Walk-forward loop
    for t in range(TRAIN_WINDOW, total_bars, STEP_SIZE):
        train_slice = df.iloc[t - TRAIN_WINDOW:t].copy()

        try:
            is_breakout, direction, regime, _, current_atr = detect_breakout(train_slice, ticker=ticker, macro_data=macro_data)
        except Exception:
            continue

        desired = 0
        if regime in ('Trend Breakout', 'Mean Reversion'):
            desired = 1 if direction == 'LONG' else -1

        # Calculate levels for the NEW desired position
        current_price = df['Close'].iloc[t]
        tp_level, sl_level = get_dynamic_exit_levels(regime, current_price, current_atr, direction, ticker=ticker)
        
        # 1.2 Candle Filter: Calculate Trigger Price for Majors
        trigger_price = None
        if ticker in MAJORS_ENTRY_FILTER and regime == "Trend Breakout":
            trigger_price = get_trigger_price(df.iloc[:t], regime, direction, current_atr)

        # ── Intra-step Simulation ──────────────────────────────────────────
        # Check each bar until the next re-training step for TP/SL hits
        for sub_t in range(t, min(t + STEP_SIZE, total_bars)):
            high = df['High'].iloc[sub_t]
            low = df['Low'].iloc[sub_t]
            close = df['Close'].iloc[sub_t]

            # If we had a position, check for exit
            if position != 0:
                hit_tp = (position == 1 and high >= entry_tp) or (position == -1 and low <= entry_tp)
                hit_sl = (position == 1 and low <= entry_sl) or (position == -1 and high >= entry_sl)

                if hit_tp or hit_sl:
                    exit_price = entry_tp if hit_tp else entry_sl
                    raw_ret = position * (exit_price / entry_price - 1)
                    net_ret = raw_ret - TRANSACTION_COST
                    trades.append({
                        'Ticker': ticker,
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
                # 1.2 Candle Logic (Majors): Strict 1-bar trigger window
                can_enter = True
                if trigger_price:
                    # check if hit in the FIRST sub-step
                    if sub_t == t:
                        if desired == 1: # LONG
                            can_enter = (high >= trigger_price)
                        else: # SHORT
                            can_enter = (low <= trigger_price)
                        
                        if not can_enter:
                            # Trigger NOT hit in the immediate next hour -> Cancel for this 24h step
                            desired = 0
                    else:
                        # Should have been handled in sub_t == t; skip if reached here
                        can_enter = False
                
                if can_enter:
                    position = desired
                    # For trigger entries, entry price is the trigger level or current open
                    entry_price = trigger_price if trigger_price else df['Close'].iloc[sub_t]
                    entry_tp = tp_level
                    entry_sl = sl_level
                    entry_regime = regime
                    entry_bar_idx = sub_t
                    # Once entered, we don't re-enter in the same sub-loop until next main step
                    desired = 0 

    if not trades:
        return {'ticker': ticker, 'trades': 0, 'total_return': 0,
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
        'ticker': ticker,
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

    # Fetch all data upfront as a batch (correct API: list of tickers)
    print("\nFetching historical data for all pairs...")
    all_data = fetch_data(CURRENCY_PAIRS, period=BACKTEST_PERIOD, interval=BACKTEST_INTERVAL)
    
    print("\nTracing macro context (Yields/Commodities)...")
    macro_data = get_macro_data(interval=BACKTEST_INTERVAL, period=BACKTEST_PERIOD)
    print(f"Data ready for {len(all_data)} pairs and macro context.\n")

    all_results = []
    all_trade_logs = []

    for ticker in CURRENCY_PAIRS:
        if ticker not in all_data:
            print(f"  {ticker}: SKIPPED (fetch failed)")
            continue

        print(f"  Backtesting {ticker}...", end=" ", flush=True)
        result = run_backtest_for_pair(ticker, all_data[ticker], macro_data=macro_data)
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

        all_results.append({
            'Ticker': result['ticker'],
            'Trades': result['trades'],
            'Total_Return_%': round(result['total_return'] * 100, 2),
            'Win_Rate_%': round(result['win_rate'] * 100, 1),
            'Max_Drawdown_%': round(result['max_drawdown'] * 100, 2),
            'Sharpe_Ratio': round(result['sharpe'], 2),
        })

        if result.get('trade_log') is not None:
            all_trade_logs.append(result['trade_log'])

    if not all_results:
        print("\nNo results to report.")
        return

    # ── Aggregate Summary ───────────────────────────────────────────────────
    df_summary = pd.DataFrame(all_results).sort_values('Total_Return_%', ascending=False)

    print("\n" + "=" * 60)
    print("  AGGREGATE RESULTS (sorted by return)")
    print("=" * 60)
    print(df_summary.to_string(index=False))

    avg_return = df_summary['Total_Return_%'].mean()
    avg_wr = df_summary['Win_Rate_%'].mean()
    avg_dd = df_summary['Max_Drawdown_%'].mean()
    avg_sharpe = df_summary['Sharpe_Ratio'].mean()
    total_trades = df_summary['Trades'].sum()

    print("\n--- Portfolio Averages ---")
    print(f"  Total Trades    : {total_trades}")
    print(f"  Avg Return      : {avg_return:+.2f}%")
    print(f"  Avg Win Rate    : {avg_wr:.1f}%")
    print(f"  Avg Max Drawdown: {avg_dd:.2f}%")
    print(f"  Avg Sharpe Ratio: {avg_sharpe:.2f}")

    # ── Save Results ────────────────────────────────────────────────────────
    out_file = 'backtest_results.csv'
    df_summary.to_csv(out_file, index=False)

    if all_trade_logs:
        all_trades_df = pd.concat(all_trade_logs, ignore_index=True)
        all_trades_df.to_csv('backtest_trade_log.csv', index=False)

    print(f"\n  Results saved to '{out_file}' and 'backtest_trade_log.csv'.")
    print("=" * 60)


if __name__ == "__main__":
    main()
