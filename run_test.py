# run_test.py
# Script to run the backtest and API connection test

import logging
import sys
import ccxt
from delta_api import DeltaApiClient
from config import API_KEY, API_SECRET, BASE_URL, SYMBOL



# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_run.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_runner')

def test_ccxt_connection():
    """Test connection to Delta Exchange via CCXT"""
    try:
        logger.info("Testing CCXT connection to Delta Exchange...")
        exchange = ccxt.delta()
        tickers = exchange.fetch_tickers()
        logger.info(f"CCXT connection successful. Found {len(tickers)} tickers.")
        
        # Test BTC/USD ticker specifically
        btc_ticker = exchange.fetch_ticker('BTCUSD')
        logger.info(f"BTC/USD ticker data: Last price = {btc_ticker['last']}")
        
        return True
    except Exception as e:
        logger.error(f"CCXT connection failed: {e}")
        return False

def test_api_connection():
    """Test connection using custom Delta API client"""
    if not API_KEY or not API_SECRET:
        logger.error("API_KEY or API_SECRET not set. Skipping API connection test.")
        return False
    
    try:
        logger.info("Testing direct API connection to Delta Exchange...")
        api_client = DeltaApiClient(BASE_URL, API_KEY, API_SECRET)
        
        # Test getting ticker
        ticker = api_client.get_ticker(SYMBOL)
        logger.info(f"API connection successful. {SYMBOL} last price: {ticker.get('last_price')}")
        
        # Test getting product details
        product = api_client.get_product(27)  # BTC perpetual
        logger.info(f"Product details: {product.get('symbol')}, Lot size: {product.get('lot_size')}")
        
        return True
    except Exception as e:
        logger.error(f"API connection failed: {e}")
        logger.error("Make sure your IP is whitelisted and your clock is synchronized")
        return False

def run_tests():
    """Run all tests"""
    logger.info("Starting tests...")
    
    # Test CCXT connection (doesn't require API keys)
    ccxt_success = test_ccxt_connection()
    
    # Test custom API client
    api_success = test_api_connection()
    
    # Print summary
    logger.info("\n====== Test Results ======")
    logger.info(f"CCXT Connection: {'SUCCESS' if ccxt_success else 'FAILED'}")
    logger.info(f"API Connection: {'SUCCESS' if api_success else 'FAILED'}")
    
    if not ccxt_success or not api_success:
        logger.info("\nTroubleshooting tips:")
        logger.info("1. If CCXT failed: Check your internet connection and proxy settings")
        logger.info("2. If API failed but CCXT succeeded: Most likely an authentication issue")
        logger.info("   - Make sure your API keys are correct")
        logger.info("   - Ensure your IP is whitelisted in Delta Exchange")
        logger.info("   - Sync your system clock with an NTP server")
        logger.info("   - Check that you're using production API keys with production URL")
    
    logger.info("\nRun the backtest script to test strategy performance")

if __name__ == "__main__":
    run_tests()