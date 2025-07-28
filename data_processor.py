# data_processor.py
# Handle historical data fetching and processing

import pandas as pd
import numpy as np
import ccxt
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('data_processor')

class DataProcessor:
    def __init__(self, symbol, timeframe):
        self.symbol = symbol
        self.timeframe = timeframe
        self.df = None
        self.exchange_ccxt = ccxt.delta()
    
    def fetch_historical_data(self, days=365):
        """Fetch historical OHLCV data using CCXT"""
        logger.info(f"Fetching {days} days of historical data for {self.symbol}")
        
        try:
            since = self.exchange_ccxt.milliseconds() - (days * 24 * 60 * 60 * 1000)
            ohlcv = self.exchange_ccxt.fetch_ohlcv(self.symbol, self.timeframe, since=since)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            self.df = df
            logger.info(f"Fetched {len(df)} records of historical data")
            return self.df
        
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise
    
    def calculate_indicators(self):
        """Calculate technical indicators on the dataframe"""
        if self.df is None or len(self.df) == 0:
            logger.error("No data available to calculate indicators")
            return None
        
        logger.info("Calculating technical indicators")
        
        # Calculate moving averages
        self.df['ma_200'] = self.df['close'].rolling(window=200).mean()
        self.df['ma_50'] = self.df['close'].rolling(window=50).mean()
        
        # Calculate ATR (simplified version)
        self.df['tr'] = np.maximum(
            self.df['high'] - self.df['low'],
            np.maximum(
                abs(self.df['high'] - self.df['close'].shift(1)),
                abs(self.df['low'] - self.df['close'].shift(1))
            )
        )
        self.df['atr'] = self.df['tr'].rolling(window=14).mean()
        
        # Drop NaN values
        self.df = self.df.dropna()
        
        logger.info("Indicators calculated successfully")
        return self.df
    
    def update_daily_data(self, latest_price=None):
        """Add today's data to the dataframe and recalculate indicators"""
        if self.df is None:
            logger.warning("Cannot update data: No historical data loaded")
            return None
        
        today = datetime.now().strftime('%Y-%m-%d')
        if latest_price is None:
            try:
                # Fetch latest ticker data
                ticker = self.exchange_ccxt.fetch_ticker(self.symbol)
                latest_price = ticker['last']
            except Exception as e:
                logger.error(f"Error fetching latest price: {e}")
                return None
        
        # Check if we already have today's data
        if today in self.df.index:
            # Update today's close price
            self.df.loc[today, 'close'] = latest_price
        else:
            # Add new row for today
            new_row = pd.DataFrame(
                [[latest_price, latest_price, latest_price, latest_price, 0]],
                columns=['open', 'high', 'low', 'close', 'volume'],
                index=[pd.to_datetime(today)]
            )
            self.df = pd.concat([self.df, new_row])
        
        # Recalculate indicators
        return self.calculate_indicators()
    
    def get_latest_indicators(self):
        """Get the latest indicator values"""
        if self.df is None or len(self.df) == 0:
            logger.error("No data available to get indicators")
            return None
        
        last_row = self.df.iloc[-1]
        return {
            'ma_200': last_row['ma_200'],
            'ma_50': last_row['ma_50'],
            'atr': last_row['atr'],
            'close': last_row['close']
        }
    