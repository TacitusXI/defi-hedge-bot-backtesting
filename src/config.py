from datetime import datetime

# Time settings
BINANCE_DEFAULT_SINCE = int(datetime(2024, 1, 1).timestamp() * 1000)

# Uniswap and Graph API settings
UNISWAP_POOL_ADDRESS = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
GRAPH_URL = (
    "https://gateway.thegraph.com/api/cf408901eb42841aec6fea82de29b9a4/"
    "subgraphs/id/A3Np3RQbaBA6oKJgiwDJeo5T3zrYfGHPWFYayMwtNDum"
)

# Strategy parameters
FEE_RATE = 0.001  # 0.1% fee per trade
IL_THRESHOLD = 3.0  # Impermanent loss threshold (percentage)
ALPHA = 0.5         # Hedge fraction (short 50% of ETH exposure)
INITIAL_K = 50000.0  # k = 5 ETH * 10,000 USDC
