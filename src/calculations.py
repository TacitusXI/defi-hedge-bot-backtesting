import math

def calc_lp_value(eth_price: float, k: float) -> float:
    """
    Calculate the theoretical LP value for a constant-product pool.
    
    :param eth_price: The current ETH price.
    :param k: The constant product (e.g., 5 ETH * 10,000 USDC).
    :return: The LP value.
    """
    return 2 * math.sqrt(k * eth_price)

def calc_hold_value(eth_price: float) -> float:
    """
    Calculate the value of holding the assets (5 ETH + 10,000 USDC).
    
    :param eth_price: The current ETH price.
    :return: The holding value.
    """
    return 5 * eth_price + 10000
