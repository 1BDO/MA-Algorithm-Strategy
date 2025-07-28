# trading_strategy.py
# Implement the trading strategy logic

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('trading_strategy')

class TradingStrategy:
    def __init__(self, api_client, data_processor, product_id, bankroll,
                 win_probability, risk_reward_ratio, kelly_fraction):
        self.api_client = api_client
        self.data_processor = data_processor
        self.product_id = product_id
        self.bankroll = bankroll
        self.win_probability = win_probability
        self.risk_reward_ratio = risk_reward_ratio
        self.kelly_fraction = kelly_fraction
        self.active_position = None
        self.initial_equity = None
    
    def determine_trend(self, current_price, ma_200, ma_50):
        """Determine market trend based on moving averages"""
        if current_price > ma_200:
            return 'uptrend'
        elif current_price < ma_200:
            return 'downtrend'
        else:
            return 'neutral'
    
    def check_entry_conditions(self, current_price, trend, ma_200, ma_50):
        """Check if entry conditions are met"""
        if trend == 'uptrend' and current_price < ma_50 and current_price > ma_200:
            return 'buy'
        elif trend == 'downtrend' and current_price > ma_50 and current_price < ma_200:
            return 'sell'
        else:
            return None
    
    def calculate_position_size(self, current_price, atr):
        """Calculate position size using the Kelly Criterion"""
        p = self.win_probability
        q = 1 - p
        b = self.risk_reward_ratio
        kelly_percentage = (b * p - q) / b * self.kelly_fraction
        stop_loss_distance = 2 * atr
        risk_per_trade = kelly_percentage * self.bankroll
        product = self.api_client.get_product(self.product_id)
        lot_size = float(product.get('lot_size', 1))
        position_size = int(risk_per_trade / (lot_size * stop_loss_distance * current_price))
        position_size = max(1, position_size)
        position_value = position_size * lot_size * current_price
        if position_value <= 100000:
            initial_margin_rate = 0.005
        else:
            k = 2.5e-8
            additional_position = position_value - 100000
            additional_margin_rate = k * additional_position
            initial_margin_rate = 0.005 + additional_margin_rate
        initial_margin_required = position_value * initial_margin_rate
        if initial_margin_required > self.bankroll:
            position_size = int(self.bankroll / (initial_margin_rate * lot_size * current_price))
            position_size = max(1, position_size)
            logger.warning(f"Position size reduced to {position_size} due to margin constraints")
        return {
            'position_size': position_size,
            'lot_size': lot_size,
            'stop_loss_distance': stop_loss_distance,
            'position_value': position_size * lot_size * current_price,
            'margin_required': initial_margin_required
        }
    
    def place_orders(self, entry_side, position_details, current_price):
        """Place entry, stop-loss, and take-profit orders"""
        position_size = position_details['position_size']
        stop_loss_distance = position_details['stop_loss_distance']
        if entry_side == 'buy':
            stop_loss_price = current_price - stop_loss_distance
            take_profit_price = current_price + (self.risk_reward_ratio * stop_loss_distance)
            logger.info(f"Long entry at {current_price}, SL: {stop_loss_price}, TP: {take_profit_price}")
        else:
            stop_loss_price = current_price + stop_loss_distance
            take_profit_price = current_price - (self.risk_reward_ratio * stop_loss_distance)
            logger.info(f"Short entry at {current_price}, SL: {stop_loss_price}, TP: {take_profit_price}")
        try:
            entry_order = self.api_client.place_order(
                product_id=self.product_id,
                size=position_size,
                side=entry_side,
                order_type='LIMIT',
                limit_price=str(current_price),
                time_in_force='GTC'
            )
            logger.info(f"Entry order placed: {entry_order}")
            stop_side = 'sell' if entry_side == 'buy' else 'buy'
            stop_loss_order = self.api_client.place_stop_order(
                product_id=self.product_id,
                size=position_size,
                side=stop_side,
                order_type='MARKET',
                stop_price=str(stop_loss_price),
                time_in_force='GTC'
            )
            logger.info(f"Stop loss order placed: {stop_loss_order}")
            take_profit_order = self.api_client.place_stop_order(
                product_id=self.product_id,
                size=position_size,
                side=stop_side,
                order_type='MARKET',
                stop_price=str(take_profit_price),
                time_in_force='GTC'
            )
            logger.info(f"Take profit order placed: {take_profit_order}")
            self.active_position = {
                'entry_side': entry_side,
                'entry_price': current_price,
                'position_size': position_size,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'entry_order_id': entry_order.get('id'),
                'stop_loss_order_id': stop_loss_order.get('id'),
                'take_profit_order_id': take_profit_order.get('id'),
                'entry_time': datetime.now()
            }
            return True
        except Exception as e:
            logger.error(f"Error placing orders: {e}")
            try:
                self.api_client.cancel_all_orders(self.product_id)
            except:
                pass
            return False
    
    def update_trailing_stop_loss(self, current_price):
        """Update stop loss order to trail price movements"""
        if not self.active_position:
            return False
        position = self.api_client.get_position(self.product_id)
        if not position:
            return False
        entry_side = self.active_position['entry_side']
        current_stop = self.active_position['stop_loss_price']
        if entry_side == 'buy':
            indicators = self.data_processor.get_latest_indicators()
            new_stop = current_price - (2 * indicators['atr'])
            if new_stop > current_stop:
                logger.info(f"Updating trailing stop: {current_stop} -> {new_stop}")
                self.api_client.cancel_order(self.active_position['stop_loss_order_id'])
                stop_loss_order = self.api_client.place_stop_order(
                    product_id=self.product_id,
                    size=self.active_position['position_size'],
                    side='sell',
                    order_type='MARKET',
                    stop_price=str(new_stop),
                    time_in_force='GTC'
                )
                self.active_position['stop_loss_price'] = new_stop
                self.active_position['stop_loss_order_id'] = stop_loss_order.get('id')
                return True
        elif entry_side == 'sell':
            indicators = self.data_processor.get_latest_indicators()
            new_stop = current_price + (2 * indicators['atr'])
            if new_stop < current_stop:
                logger.info(f"Updating trailing stop: {current_stop} -> {new_stop}")
                self.api_client.cancel_order(self.active_position['stop_loss_order_id'])
                stop_loss_order = self.api_client.place_stop_order(
                    product_id=self.product_id,
                    size=self.active_position['position_size'],
                    side='buy',
                    order_type='MARKET',
                    stop_price=str(new_stop),
                    time_in_force='GTC'
                )
                self.active_position['stop_loss_price'] = new_stop
                self.active_position['stop_loss_order_id'] = stop_loss_order.get('id')
                return True
        return False
    
    def check_portfolio_stop_loss(self, portfolio_stop_loss_percent, balances_data):
        """Check if portfolio equity has dropped below the stop loss threshold"""
        if not isinstance(balances_data, (dict, list)):
            logger.error(f"Invalid balances_data received for portfolio stop loss check: {type(balances_data)}")
            return False

        current_equity = 0
        if isinstance(balances_data, list):
            for balance_entry in balances_data:
                if isinstance(balance_entry, dict):
                    current_equity += float(balance_entry.get('usd_value', 0))
        elif isinstance(balances_data, dict):
            for asset, details in balances_data.items():
                if isinstance(details, dict):
                    current_equity += float(details.get('usd_value', 0))

        if current_equity == 0:
            logger.warning("Calculated current equity is zero, cannot check portfolio stop loss.")
            return False

        if self.initial_equity is None:
            self.initial_equity = current_equity
            logger.info(f"Set initial equity for portfolio stop loss: {self.initial_equity}")
            return False

        equity_change_percent = ((current_equity - self.initial_equity) / self.initial_equity) * 100
        logger.info(f"Portfolio Equity Check: Initial={self.initial_equity:.2f}, Current={current_equity:.2f}, Change={equity_change_percent:.2f}%")

        if equity_change_percent <= -portfolio_stop_loss_percent:
            logger.warning(f"PORTFOLIO STOP LOSS TRIGGERED: {equity_change_percent:.2f}% equity change")
            self.liquidate_portfolio()
            return True

        return False

    def liquidate_portfolio(self):
        """Cancels all orders and closes the position for the tracked product_id."""
        logger.warning("Attempting to liquidate portfolio (cancel orders, close position)...")
        try:
            logger.info(f"Cancelling all orders for product {self.product_id}...")
            cancel_resp = self.api_client.cancel_all_orders(product_id=self.product_id)
            logger.info(f"Cancel all orders response: {cancel_resp}")
            logger.info(f"Checking position for product {self.product_id} to close...")
            position = self.api_client.get_position(self.product_id)
            if position and isinstance(position, dict) and float(position.get('size', 0)) != 0:
                size_to_close = abs(float(position.get('size', 0)))
                side_to_close = 'sell' if float(position.get('size', 0)) > 0 else 'buy'
                logger.warning(f"Closing position: Side={side_to_close}, Size={size_to_close}")
                close_order = self.api_client.place_order(
                    product_id=self.product_id,
                    size=size_to_close,
                    side=side_to_close,
                    order_type='market'
                )
                logger.info(f"Position close order response: {close_order}")
            else:
                logger.info("No position found or size is zero, nothing to close.")
            self.active_position = None
            logger.warning("Portfolio liquidation actions complete.")
        except Exception as e:
            logger.error(f"Error during portfolio liquidation: {e}")
            import traceback
            logger.error(traceback.format_exc())
