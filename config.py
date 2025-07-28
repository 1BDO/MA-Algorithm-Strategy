# config.py
# Store configuration and credentials

# config.py
import os
from dotenv import load_dotenv

# Print the current working directory for debugging
print("Current working directory:", os.getcwd())

# Load environment variables from .env file
load_dotenv()

# Debug prints to see if the variables are loaded
api_key = os.getenv('DELTA_API_KEY')
api_secret = os.getenv('DELTA_API_SECRET')
print("Loaded API Key:", api_key)
print("Loaded API Secret:", api_secret)

# API configuration
BASE_URL = os.getenv('DELTA_BASE_URL', 'https://cdn-ind.testnet.deltaex.org')
API_KEY = api_key
API_SECRET = api_secret

# Trading parameters
SYMBOL = 'BTCUSD'
PRODUCT_ID = 27  # BTC perpetual
TIMEFRAME = '1d'
BANKROLL = float(os.getenv('BANKROLL', '1000'))
WIN_PROBABILITY = 0.6
RISK_REWARD_RATIO = 3
KELLY_FRACTION = 0.5  # Using half Kelly for safety
PORTFOLIO_STOP_LOSS_PERCENT = 10  # Liquidate all if equity drops by this percentage

# Check if API credentials are missing and raise an error if so
if not API_KEY or not API_SECRET:
    raise ValueError("API credentials not set. Please set DELTA_API_KEY and DELTA_API_SECRET in .env file.")


'''

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# API configuration
API_KEY = os.getenv('wq08c0WRtaD0vmwLh5duDYyJReXL65')
API_SECRET = os.getenv('3aw2RISnAu9MZvy0jpeZZFVX76oDY3EMDXnBqlA8hizys3oRQFyfA4kKa40T')
BASE_URL = os.getenv('DELTA_BASE_URL', 'https://testnet-api.delta.exchange')  # Default to testnet

# Trading parameters
SYMBOL = 'BTCUSD'
PRODUCT_ID = 27  # BTC perpetual
TIMEFRAME = '1d'
BANKROLL = float(os.getenv('BANKROLL', '1000'))
WIN_PROBABILITY = 0.6
RISK_REWARD_RATIO = 3
KELLY_FRACTION = 0.5  # Using half Kelly for safety
PORTFOLIO_STOP_LOSS_PERCENT = 10  # Liquidate all if equity drops by this percentage

'''





