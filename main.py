# main.py
# Main execution script

import time
import schedule
import logging
import sys
from datetime import datetime

from config import (
    API_KEY, API_SECRET, BASE_URL, SYMBOL, PRODUCT_ID, TIMEFRAME, BANKROLL,
    WIN_PROBABILITY, RISK_REWARD_RATIO, KELLY_FRACTION, PORTFOLIO_STOP_LOSS_PERCENT
)
from delta_api import DeltaApiClient
from data_processor import DataProcessor
from trading_strategy import TradingStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('main')

def check_credentials():
    """Check if API credentials are set"""
    if not API_KEY or not API_SECRET:
        logger.error("API credentials not set. Please set DELTA_API_KEY and DELTA_API_SECRET in .env file.")
        return False
    return True

def initialize_components():
    """Initialize API client, data processor, and trading strategy"""
    try:
        api_client = DeltaApiClient(BASE_URL, API_KEY, API_SECRET)
        logger.info("Attempting to fetch ticker data...")
        response = api_client.get_ticker(SYMBOL)
        ticker_data = None
        if response and response.get('success') is True:
            results = response.get('result', [])
            for item in results:
                if isinstance(item, dict) and item.get('symbol') == SYMBOL:
                    ticker_data = item
                    break
            if ticker_data:
                price_value = ticker_data.get('mark_price') or ticker_data.get('close')
                if price_value is not None:
                    logger.info(f"API connection successful. Using price value: {price_value}")
                else:
                    logger.error(f"Could not extract 'mark_price' or 'close' from ticker data: {ticker_data}")
                    return None, None, None
            else:
                logger.error(f"Could not find symbol '{SYMBOL}' in API response results: {results}")
                return None, None, None
        else:
            logger.error(f"API call to get ticker was unsuccessful or returned invalid data: {response}")
            return None, None, None
        
        data_processor = DataProcessor(SYMBOL, TIMEFRAME)
        data_processor.fetch_historical_data(days=365)
        data_processor.calculate_indicators()
        strategy = TradingStrategy(
            api_client=api_client,
            data_processor=data_processor,
            product_id=PRODUCT_ID,
            bankroll=BANKROLL,
            win_probability=WIN_PROBABILITY,
            risk_reward_ratio=RISK_REWARD_RATIO,
            kelly_fraction=KELLY_FRACTION
        )
        return api_client, data_processor, strategy
    
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        return None, None, None

def check_trading_conditions():
    """Check if trading conditions are met and execute trades"""
    try:
        logger.info("Checking trading conditions")
        response = api_client.get_ticker(SYMBOL)
        ticker_data = None
        current_price = None
        if response and response.get('success') is True:
            results = response.get('result', [])
            for item in results:
                if isinstance(item, dict) and item.get('symbol') == SYMBOL:
                    ticker_data = item
                    break
            if not ticker_data:
                logger.warning(f"Could not find symbol '{SYMBOL}' in API response for conditions check.")
                return
        else:
            logger.warning(f"API call unsuccessful or invalid data for conditions check: {response}")
            return

        # Extract price from ticker_data
        price_str = ticker_data.get('mark_price') or ticker_data.get('close')
        if price_str is not None:
            try:
                current_price = float(price_str)
                logger.info(f"Using current price: {current_price}")
            except (ValueError, TypeError) as e:
                logger.error(f"Could not convert price '{price_str}' to float: {e}")
                return
        else:
            logger.warning(f"Could not retrieve valid price using 'mark_price' or 'close' from ticker data: {ticker_data}")
            return
        
        if current_price is None:
            logger.error("current_price is None, cannot proceed with strategy logic.")
            return
        
        indicators = data_processor.get_latest_indicators()
        ma_200 = indicators['ma_200']
        ma_50 = indicators['ma_50']
        atr = indicators['atr']
        
        # --- Check if we have an active position ---
        position = api_client.get_position(PRODUCT_ID)
        has_position = position and float(position.get('size', 0)) != 0
        
        if has_position:
            strategy.update_trailing_stop_loss(current_price)
        else:
            trend = strategy.determine_trend(current_price, ma_200, ma_50)
            logger.info(f"Current trend: {trend}, Price: {current_price}, MA200: {ma_200}, MA50: {ma_50}")
            entry_side = strategy.check_entry_conditions(current_price, trend, ma_200, ma_50)
            if entry_side:
                logger.info(f"Entry conditions met for {entry_side} position")
                position_details = strategy.calculate_position_size(current_price, atr)
                logger.info(f"Position details: {position_details}")
                strategy.place_orders(entry_side, position_details, current_price)
        
        # --- Check portfolio stop loss ---
        logger.info("Checking portfolio stop loss...")
        balances_response = api_client.get_balances()
        logger.info(f"Balances response: {balances_response}")
        if isinstance(balances_response, dict) and balances_response.get('success') is True:
            # Attempt to calculate total equity using available fields
            balances_result = balances_response.get('result', [])
            current_equity = 0.0
            for balance_entry in balances_result:
                if isinstance(balance_entry, dict):
                    # Prioritize 'usd_value' if available; otherwise use 'balance'
                    if 'usd_value' in balance_entry:
                        current_equity += float(balance_entry.get('usd_value', 0))
                    elif 'balance' in balance_entry:
                        current_equity += float(balance_entry.get('balance', 0))
            logger.info(f"Calculated current equity: {current_equity}")
            strategy.check_portfolio_stop_loss(PORTFOLIO_STOP_LOSS_PERCENT, balances_result)
        elif isinstance(balances_response, dict):
            logger.error(f"Failed API call to get balances: {balances_response.get('error')}")
        else:
            logger.error(f"Unexpected response type received from get_balances: {type(balances_response)}")
        
    except Exception as e:
        logger.error(f"Error checking trading conditions: {e}")

def update_daily_data():
    """Update daily data at market close"""
    try:
        logger.info("Updating daily data")
        response = api_client.get_ticker(SYMBOL)
        ticker_data = None
        if response and response.get('success') is True:
            results = response.get('result', [])
            for item in results:
                if isinstance(item, dict) and item.get('symbol') == SYMBOL:
                    ticker_data = item
                    break
            if not ticker_data:
                logger.warning(f"Could not find symbol '{SYMBOL}' in API response for daily data update.")
                return
        else:
            logger.warning(f"API call unsuccessful or invalid data for daily update: {response}")
            return
        
        price_str = ticker_data.get('mark_price') or ticker_data.get('close')
        if price_str is not None:
            try:
                current_price = float(price_str)
                logger.info(f"Using current price for daily update: {current_price}")
            except (ValueError, TypeError) as e:
                logger.error(f"Could not convert price '{price_str}' to float during daily update: {e}")
                return
        else:
            logger.warning(f"Could not retrieve valid price for daily update from ticker data: {ticker_data}")
            return
        
        data_processor.update_daily_data(current_price)
        logger.info("Daily data updated successfully")
    
    except Exception as e:
        logger.error(f"Error updating daily data: {e}")

def main():
    """Main function to run the trading bot"""
    global api_client, data_processor, strategy
    logger.info("Starting Delta Trading Bot")
    if not check_credentials():
        return
    api_client, data_processor, strategy = initialize_components()
    if not all([api_client, data_processor, strategy]):
        logger.error("Failed to initialize one or more components. Exiting.")
        return
    schedule.every(15).minutes.do(check_trading_conditions)
    schedule.every().day.at("23:59").do(update_daily_data)
    check_trading_conditions()
    logger.info("Trading bot running. Press Ctrl+C to exit.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Trading bot shutting down")

if __name__ == "__main__":
    main()
