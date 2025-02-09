import matplotlib.pyplot as plt
import pandas as pd
from src.config import IL_THRESHOLD

def plot_results(df: pd.DataFrame) -> None:
    """
    Plot various charts for the backtest results.
    
    :param df: DataFrame containing backtest results.
    """
    plt.figure(figsize=(16, 20))

    # 1. ETH Price
    plt.subplot(9, 1, 1)
    plt.plot(df['timestamp'], df['eth_price'], label='ETH Price')
    plt.title('ETH Price')
    plt.legend()

    # 2. Normalized Holding vs. LP Value
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

    # 9. Combined Chart: Holdings vs LP vs Investor Portfolio
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
