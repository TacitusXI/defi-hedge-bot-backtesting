import logging
import math
import pandas as pd
from datetime import datetime
from src.data_fetcher import fetch_binance_candles, fetch_uniswap_pool_data_paginated
from src.calculations import calc_lp_value, calc_hold_value
from src.plotting import plot_results
from src.config import UNISWAP_POOL_ADDRESS, FEE_RATE, IL_THRESHOLD, ALPHA, INITIAL_K

def simulate_backtest() -> None:
    """
    Perform backtesting of LP performance and a simple hedge strategy.
    """
    # Define time interval: Jan 1, 2024 – Jan 1, 2025
    start_dt = datetime(2024, 1, 1)
    end_dt = datetime(2025, 1, 1)
    since_binance = int(start_dt.timestamp() * 1000)
    end_time_binance = int(end_dt.timestamp() * 1000)
    start_timestamp = int(start_dt.timestamp())
    end_timestamp = int(end_dt.timestamp())

    # Fetch Binance candlestick data
    logging.info("Fetching Binance candlestick data...")
    df_eth = fetch_binance_candles(symbol='ETH/USDC', since=since_binance, end_time=end_time_binance)
    df_eth.to_csv('data/eth_candles.csv', index=False)
    logging.info("Binance data saved to data/eth_candles.csv")

    # Fetch Uniswap pool swap data
    logging.info("Fetching Uniswap pool swap data...")
    df_pool = fetch_uniswap_pool_data_paginated(UNISWAP_POOL_ADDRESS, start_timestamp, end_timestamp)
    df_pool.to_csv('data/uniswap_pool_data.csv', index=False)
    logging.info("Uniswap swap data saved to data/uniswap_pool_data.csv")

    # Merge data: assign each swap the latest available ETH price
    df_merged = pd.merge_asof(
        df_pool.sort_values('timestamp'),
        df_eth[['timestamp', 'close']].sort_values('timestamp'),
        on='timestamp',
        direction='backward'
    )
    df_merged.rename(columns={'close': 'eth_price'}, inplace=True)
    df_merged['eth_price'] = df_merged['eth_price'].ffill()

    # Compute LP Value, Holding Value, and Impermanent Loss
    V_LP, V_hold, IL_pct = [], [], []
    for _, row in df_merged.iterrows():
        price = row['eth_price']
        lp_val = calc_lp_value(price, INITIAL_K)
        hold_val = calc_hold_value(price)
        V_LP.append(lp_val)
        V_hold.append(hold_val)
        il = hold_val - lp_val
        IL_pct.append((il / hold_val) * 100)
    df_merged['V_LP'] = V_LP
    df_merged['V_hold'] = V_hold
    df_merged['IL_pct'] = IL_pct

    # Hedge Strategy Simulation
    hedge_desired = []
    for _, row in df_merged.iterrows():
        price = row['eth_price']
        eth_exposure = math.sqrt(INITIAL_K / price)
        if row['IL_pct'] > IL_THRESHOLD:
            hedge_desired.append(-ALPHA * eth_exposure)
        else:
            hedge_desired.append(0.0)
    df_merged['hedge_desired'] = hedge_desired

    # Simulate hedge orders (immediate execution with fees)
    hedge_position = []
    hedge_costs = []
    current_hedge = 0.0
    for _, row in df_merged.iterrows():
        desired = row['hedge_desired']
        delta = desired - current_hedge
        cost = FEE_RATE * abs(delta) * row['eth_price']
        hedge_costs.append(cost)
        current_hedge = desired
        hedge_position.append(current_hedge)
    df_merged['hedge_position'] = hedge_position
    df_merged['hedge_cost'] = hedge_costs
    df_merged['cumulative_hedge_cost'] = df_merged['hedge_cost'].cumsum()

    # Calculate cumulative hedge PnL (for short hedge)
    hedge_pnl = [0.0]
    for i in range(len(df_merged) - 1):
        pos = df_merged['hedge_position'].iloc[i]
        price_current = df_merged['eth_price'].iloc[i]
        price_next = df_merged['eth_price'].iloc[i+1]
        pnl = -pos * (price_current - price_next)
        hedge_pnl.append(hedge_pnl[-1] + pnl)
    df_merged['cumulative_hedge_pnl'] = hedge_pnl

    # Compute investor portfolio value: LP value + cumulative hedge PnL - cumulative hedge costs
    investor_portfolio = []
    for i in range(len(df_merged)):
        inv_val = df_merged['V_LP'].iloc[i] + df_merged['cumulative_hedge_pnl'].iloc[i] - df_merged['cumulative_hedge_cost'].iloc[i]
        investor_portfolio.append(inv_val)
    df_merged['investor_portfolio'] = investor_portfolio

    # Normalize values relative to the initial holding value.
    initial_hold = df_merged['V_hold'].iloc[0]
    df_merged['V_LP_norm'] = df_merged['V_LP'] / initial_hold
    df_merged['V_hold_norm'] = df_merged['V_hold'] / initial_hold
    df_merged['investor_portfolio_norm'] = df_merged['investor_portfolio'] / initial_hold

    logging.info("Backtest complete. Sample data:")
    logging.info("\n%s", df_merged.head())

    # Plot and save results
    plot_results(df_merged)
    df_merged.to_csv('data/backtest_results.csv', index=False)
    logging.info("Backtest results saved to data/backtest_results.csv")
