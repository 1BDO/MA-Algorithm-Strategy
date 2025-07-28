# test_official_client.py
import logging
from delta_rest_client import DeltaRestClient, OrderType, TimeInForce # Import necessary things
from config import API_KEY, API_SECRET, BASE_URL, SYMBOL # Import your config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"Testing with official DeltaRestClient...")
logging.info(f"Using Base URL: {BASE_URL}")
logging.info(f"Using API Key: {API_KEY[:5]}...") # Log only prefix for security

try:
    # Initialize the official client
    delta_client = DeltaRestClient(
        base_url=BASE_URL,
        api_key=API_KEY,
        api_secret=API_SECRET
    )

    # Try a simple public endpoint first (like get_ticker)
    logging.info(f"Attempting to get ticker for {SYMBOL}...")
    ticker_response = delta_client.get_ticker(SYMBOL)
    logging.info(f"Ticker Response: {ticker_response}") # Print the full response

    # Optional: Try an authenticated endpoint (like get_balances)
    # logging.info("Attempting to get balances...")
    # balances_response = delta_client.get_balances() # Needs correct asset_id if required by lib V2
    # logging.info(f"Balances Response: {balances_response}")

    logging.info("Official client test completed successfully (connection likely okay).")

except Exception as e:
    logging.error(f"Error using official DeltaRestClient: {e}")
    import traceback
    logging.error(traceback.format_exc()) # Print full traceback for errors