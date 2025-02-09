import ccxt
import pandas as pd
import requests
import time
import logging
from typing import Optional
from src.config import BINANCE_DEFAULT_SINCE, GRAPH_URL

def fetch_binance_candles(
    symbol: str = 'ETH/USDC',
    timeframe: str = '15m',
    since: Optional[int] = None,
    end_time: Optional[int] = None,
) -> pd.DataFrame:
    """
    Fetch historical candlestick data from Binance using pagination.
    
    :param symbol: Trading pair symbol (default 'ETH/USDC')
    :param timeframe: Timeframe for candles (default '15m')
    :param since: Start timestamp in milliseconds (default Jan 1, 2024)
    :param end_time: End timestamp in milliseconds (optional)
    :return: DataFrame with OHLCV data
    """
    binance = ccxt.binance({'enableRateLimit': True})
    if since is None:
        since = BINANCE_DEFAULT_SINCE

    all_candles = []
    while True:
        candles = binance.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        if not candles:
            break
        all_candles.extend(candles)
        last_ts = candles[-1][0]
        if end_time and last_ts >= end_time:
            break
        if last_ts == since:
            break
        since = last_ts + 1

    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    if end_time:
        df = df[df['timestamp'] <= pd.to_datetime(end_time, unit='ms')]
    return df

def fetch_uniswap_pool_data_paginated(
    pool_address: str, start_timestamp: int, end_timestamp: int
) -> pd.DataFrame:
    """
    Fetch Uniswap pool swap data from The Graph using timestamp pagination.
    
    :param pool_address: Pool address (string)
    :param start_timestamp: Start Unix timestamp in seconds
    :param end_timestamp: End Unix timestamp in seconds
    :return: DataFrame with swap data
    """
    url = GRAPH_URL
    pool_address = pool_address.lower()
    all_data = []
    limit = 1000
    current_timestamp = start_timestamp
    iteration = 0

    while True:
        iteration += 1
        query = f"""
        {{
          swaps(first: {limit}, orderBy: timestamp, orderDirection: asc, where: {{
            pair: "{pool_address}",
            timestamp_gte: {current_timestamp},
            timestamp_lte: {end_timestamp}
          }}) {{
            id
            timestamp
            amount0In
            amount1In
            amount0Out
            amount1Out
          }}
        }}
        """
        try:
            response = requests.post(url, json={'query': query}, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logging.error("Request error (iteration %d): %s", iteration, e)
            break

        try:
            result = response.json()
        except Exception as e:
            logging.error("JSON decode error (iteration %d): %s", iteration, e)
            break

        if "data" not in result or "swaps" not in result["data"]:
            logging.error("Unexpected result structure (iteration %d): %s", iteration, result)
            break

        data_chunk = result["data"]["swaps"]
        if not data_chunk:
            logging.info("Iteration %d: No new data, ending pagination.", iteration)
            break

        logging.info("Iteration %d: Retrieved %d records.", iteration, len(data_chunk))
        all_data.extend(data_chunk)
        last_timestamp = int(data_chunk[-1]["timestamp"])

        if last_timestamp >= end_timestamp:
            logging.info("Reached end of period in iteration %d.", iteration)
            break

        if last_timestamp < current_timestamp:
            logging.warning("No forward progress in iteration %d.", iteration)
            break

        current_timestamp = last_timestamp + 1
        time.sleep(0.2)

    df = pd.DataFrame(all_data)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    return df

def fetch_uniswap_pool_state_data(
    pool_address: str, start_timestamp: int, end_timestamp: int
) -> pd.DataFrame:
    """
    Fetch Uniswap pool state data (pair hour data) using skip-based pagination.
    
    :param pool_address: Pool address (string)
    :param start_timestamp: Start Unix timestamp in seconds
    :param end_timestamp: End Unix timestamp in seconds
    :return: DataFrame with pool state data
    """
    url = GRAPH_URL
    pool_address = pool_address.lower()
    all_data = []
    skip = 0
    limit = 1000

    while True:
        query = f"""
        {{
          pairHourDatas(first: {limit}, skip: {skip}, where: {{
            pair: "{pool_address}",
            hourStartUnix_gte: {start_timestamp},
            hourStartUnix_lte: {end_timestamp}
          }}) {{
            hourStartUnix
            reserve0
            reserve1
          }}
        }}
        """
        try:
            response = requests.post(url, json={'query': query}, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logging.error("Error fetching pool state data: %s", e)
            break

        try:
            result = response.json()
        except Exception as e:
            logging.error("JSON decode error while fetching pool state: %s", e)
            break

        if "data" not in result or "pairHourDatas" not in result["data"]:
            logging.error("Unexpected result structure when fetching pool state: %s", result)
            break

        data_chunk = result["data"]["pairHourDatas"]
        if not data_chunk:
            break  # No more data
        all_data.extend(data_chunk)
        skip += limit

    df = pd.DataFrame(all_data)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['hourStartUnix'], unit='s')
        df['usdc_reserve'] = df['reserve0'].astype(float)
        df['eth_reserve'] = df['reserve1'].astype(float)
        df = df[['timestamp', 'eth_reserve', 'usdc_reserve']]
    return df
