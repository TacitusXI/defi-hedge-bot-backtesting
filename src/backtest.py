import pandas as pd
import matplotlib.pyplot as plt
import math

from datetime import datetime
from data_fetch import fetch_binance_candles, fetch_uniswap_pool_data_paginated
from calculations import calc_lp_value, calc_hold_value
from config import SYMBOL, TIMEFRAME, START_DATE_BINANCE, END_DATE_BINANCE, START_TIMESTAMP, END_TIMESTAMP, POOL_ADDRESS, K, IL_THRESHOLD, ALPHA, FEE_RATE

def main():
    # Fetch data
    df_eth = fetch_binance_candles(symbol=SYMBOL, timeframe=TIMEFRAME, since=START_DATE_BINANCE, end_time=END_DATE_BINANCE)
    df_eth.to_csv('../data/eth_candles.csv', index=False)
    print("Binance candle data saved to ../data/eth_candles.csv")
    
    df_state = fetch_uniswap_pool_data_paginated(POOL_ADDRESS, START_TIMESTAMP, END_TIMESTAMP)
    df_state.to_csv('../data/uniswap_pool_state.csv', index=False)
    print("Uniswap pool state data saved to ../data/uniswap_pool_state.csv")
    
    # Merge using asof merge on timestamp
    df = pd.merge_asof(
        df_state.sort_values('timestamp'),
        df_eth[['timestamp', 'close']].sort_values('timestamp'),
        on='timestamp',
        direction='backward'
    )
    df.rename(columns={'close': 'eth_price'}, inplace=True)
    df['eth_price'] = df['eth_price'].ffill()
    
    # Compute theoretical LP value, holding value, and impermanent loss percentage at each time step
    V_LP = []
    V_hold = []
    IL_pct = []  # Impermanent loss percentage relative to holding
    for index, row in df.iterrows():
        P = row['eth_price']
        lp_val = calc_lp_value(P, K)
        hold_val = calc_hold_value(P)
        V_LP.append(lp_val)
        V_hold.append(hold_val)
        IL = hold_val - lp_val
        IL_pct.append((IL / hold_val) * 100)
    df['V_LP'] = V_LP
    df['V_hold'] = V_hold
    df['IL_pct'] = IL_pct
    
    # --- Hedge Strategy Simulation ---
    # When IL_pct exceeds the threshold, we desire to open a short hedge.
    hedge_desired = []
    for index, row in df.iterrows():
        P = row['eth_price']
        # Current ETH exposure in the LP: x = sqrt(K / P)
        x = math.sqrt(K / P)
        if row['IL_pct'] > IL_THRESHOLD:
            hedge_desired.append(-ALPHA * x)  # negative indicates short
        else:
            hedge_desired.append(0.0)
    df['hedge_desired'] = hedge_desired
    
    # Execute hedge orders: immediate execution with a fee on the change in notional.
    hedge_position = []
    hedge_costs = []
    current_hedge = 0.0
    for index, row in df.iterrows():
        desired = row['hedge_desired']
        delta = desired - current_hedge
        cost = FEE_RATE * abs(delta) * row['eth_price']  # fee in USDC
        hedge_costs.append(cost)
        current_hedge = desired
        hedge_position.append(current_hedge)
    df['hedge_position'] = hedge_position
    df['hedge_cost'] = hedge_costs
    df['cumulative_hedge_cost'] = df['hedge_cost'].cumsum()
    
    # --- Hedge PnL Calculation ---
    # For a short hedge, profit = - pos * (P_i - P_{i+1})
    hedge_pnl = [0]
    for i in range(len(df) - 1):
        pos = df['hedge_position'].iloc[i]
        P_i = df['eth_price'].iloc[i]
        P_next = df['eth_price'].iloc[i+1]
        pnl = - pos * (P_i - P_next)
        hedge_pnl.append(hedge_pnl[-1] + pnl)
    df['cumulative_hedge_pnl'] = hedge_pnl
    
    # --- Investor Portfolio ---
    # Investor portfolio = LP value + cumulative hedge PnL - cumulative hedge costs
    investor_portfolio = []
    for i in range(len(df)):
        inv_val = df['V_LP'].iloc[i] + df['cumulative_hedge_pnl'].iloc[i] - df['cumulative_hedge_cost'].iloc[i]
        investor_portfolio.append(inv_val)
    df['investor_portfolio'] = investor_portfolio
    
    # Normalize by the initial holding value for comparison.
    initial_hold = df['V_hold'].iloc[0]
    df['V_LP_norm'] = df['V_LP'] / initial_hold
    df['V_hold_norm'] = df['V_hold'] / initial_hold
    df['investor_portfolio_norm'] = df['investor_portfolio'] / initial_hold
    
    print("Backtest complete. Sample results:")
    print(df.head())
    
    # --- Plotting Charts ---
    plt.figure(figsize=(16, 20))
    
    # 1. ETH Price
    plt.subplot(9, 1, 1)
    plt.plot(df['timestamp'], df['eth_price'], label='ETH Price')
    plt.title('ETH Price')
    plt.legend()
    
    # 2. Holding vs LP Value (Normalized)
    plt.subplot(9, 1, 2)
    plt.plot(df['timestamp'], df['V_hold_norm'], label='Holding Value (Normalized)')
    plt.plot(df['timestamp'], df['V_LP_norm'], label='LP Value (Normalized)')
    plt.title('Holding vs LP Value (Normalized)')
    plt.legend()
    
    # 3. Impermanent Loss (%)
    plt.subplot(9, 1, 3)
    plt.plot(df['timestamp'], df['IL_pct'], label='Impermanent Loss (%)')
    plt.axhline(y=IL_THRESHOLD, color='r', linestyle='--', label='IL Threshold')
    plt.title('Impermanent Loss (%)')
    plt.legend()
    
    # 4. Desired Hedge Position (ETH)
    plt.subplot(9, 1, 4)
    plt.plot(df['timestamp'], df['hedge_desired'], label='Desired Hedge (ETH)')
    plt.title('Desired Hedge Position (ETH)')
    plt.legend()
    
    # 5. Actual Hedge Position (ETH)
    plt.subplot(9, 1, 5)
    plt.plot(df['timestamp'], df['hedge_position'], label='Actual Hedge (ETH)')
    plt.title('Actual Hedge Position (ETH)')
    plt.legend()
    
    # 6. Cumulative Hedge Cost (USDC)
    plt.subplot(9, 1, 6)
    plt.plot(df['timestamp'], df['cumulative_hedge_cost'], label='Cumulative Hedge Cost (USDC)')
    plt.title('Cumulative Hedge Cost')
    plt.legend()
    
    # 7. Cumulative Hedge PnL (USDC)
    plt.subplot(9, 1, 7)
    plt.plot(df['timestamp'], df['cumulative_hedge_pnl'], label='Cumulative Hedge PnL (USDC)')
    plt.title('Cumulative Hedge PnL')
    plt.legend()
    
    # 8. Investor Portfolio Value (Normalized)
    plt.subplot(9, 1, 8)
    plt.plot(df['timestamp'], df['investor_portfolio_norm'], label='Investor Portfolio (Normalized)')
    plt.title('Investor Portfolio Value (Normalized)')
    plt.legend()
    
    # 9. Final Combined Chart: Holdings vs LP vs Investor Portfolio
    plt.subplot(9, 1, 9)
    plt.plot(df['timestamp'], df['V_hold_norm'], label='Pure Holdings (Normalized)', linewidth=2)
    plt.plot(df['timestamp'], df['V_LP_norm'], label='LP Value (Normalized)', linewidth=2)
    plt.plot(df['timestamp'], df['investor_portfolio_norm'], label='Investor Portfolio (Normalized)', linewidth=2)
    plt.title('Comparison: Holdings vs LP vs Investor Portfolio')
    plt.xlabel('Time')
    plt.ylabel('Normalized Value (Starting at 1.0)')
    plt.legend()
    
    plt.tight_layout()
    plt.show()
    
    df.to_csv('../data/backtest_results.csv', index=False)
    print("Backtest results saved to ../data/backtest_results.csv")

if __name__ == '__main__':
    main()
