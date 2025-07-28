# delta_api.py
# Custom API client implementation with proper authentication

import hmac
import hashlib
import datetime
import json
import time
import requests
import logging
from urllib.parse import urlencode
import certifi

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('delta_api')

class DeltaApiClient:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.cert_path = certifi.where()
        logger.info(f"Initializing Delta API client with base URL: {base_url}")
        logger.info(f"Using CA bundle path: {self.cert_path}")

    # Signature generation remains unchanged
    def _generate_signature(self, method: str, timestamp: str, request_path: str, query_string: str, payload_string: str) -> str:
        """Generates the HMAC SHA256 signature according to Delta spec."""
        message = method + timestamp + request_path + query_string + payload_string
        logger.debug(f"Signature Base String: {message}")
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        logger.debug(f"Generated Signature: {signature}")
        return signature

    def make_request(self, method, endpoint, params=None, data=None):
        """Make an authenticated request to the Delta API"""
        request_path = endpoint
        full_url = f"{self.base_url}{request_path}"
        timestamp_seconds = int(time.time())
        timestamp_str = str(timestamp_seconds)
        query_string_for_signature = ''
        if params:
            query_string_for_signature = '?' + urlencode(params)
        payload_string_for_signature = ''
        if data:
            payload_string_for_signature = json.dumps(data, separators=(',', ':'), sort_keys=True)
        signature = self._generate_signature(
            method=method.upper(),
            timestamp=timestamp_str,
            request_path=request_path,
            query_string=query_string_for_signature,
            payload_string=payload_string_for_signature
        )
        headers = {
            'API-Key': self.api_key,
            'Timestamp': timestamp_str,
            'Signature': signature,
            'User-Agent': 'DeltaExchangeClient/1.0',
            'Content-Type': 'application/json' if data else ''
        }
        if not data:
            del headers['Content-Type']

        logger.debug(f"Request URL: {full_url}")
        logger.debug(f"Request Method: {method}")
        logger.debug(f"Request Headers: {headers}")
        logger.debug(f"Request Params: {params}")
        logger.debug(f"Request Data (used for JSON): {data}")
        logger.debug(f"Using Verify Path: {self.cert_path}")

        try:
            if method == 'GET':
                response = requests.get(
                    full_url,
                    headers=headers,
                    params=params,
                    verify=self.cert_path
                )
            elif method in ['POST', 'PUT']:
                 response = requests.request(
                     method,
                     full_url,
                     headers=headers,
                     json=data,
                     params=params,
                     verify=self.cert_path
                 )
            elif method == 'DELETE':
                 response = requests.delete(
                     full_url,
                     headers=headers,
                     params=params,
                     verify=self.cert_path
                 )
            else:
                 logger.error(f"Unsupported HTTP method: {method}")
                 raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()

        except requests.exceptions.SSLError as ssl_err:
            logger.error(f"SSL Certificate Error during request to {full_url}: {ssl_err}")
            logger.error(f"Verify path used was: {self.cert_path}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"API Request Failed ({full_url}): {e}")
            if e.response is not None:
                logger.error(f"Response Status Code: {e.response.status_code}")
                try:
                     error_details = e.response.json()
                     logger.error(f"API Error Details: {error_details}")
                     if isinstance(error_details.get('error'), dict) and error_details['error'].get('code') == 'ip_not_whitelisted_for_api_key':
                          logger.critical("FATAL: IP address not whitelisted. Please update API Key settings on Delta Exchange.")
                except ValueError:
                     logger.error(f"Non-JSON Response Body: {e.response.text}")
            raise
        except Exception as e:
             logger.error(f"An unexpected error occurred during request: {e}")
             raise

    # --- API Endpoint methods remain the same except get_position ---

    def get_ticker(self, symbol):
        """Get current ticker data for a symbol"""
        return self.make_request('GET', '/v2/tickers', params={'symbol': symbol})

    def get_product(self, product_id):
        """Get product details"""
        return self.make_request('GET', f'/v2/products/{product_id}')

    def get_balances(self):
        """Get wallet balances"""
        return self.make_request('GET', '/v2/wallet/balances')

    # Deprecated: Standalone get_positions method is no longer used.
    # def get_positions(self):
    #     logger.warning("get_positions() called without filter, likely invalid for V2.")
    #     return None

    def get_position(self, product_id):
        """
        Get position for a specific product.
        Attempts filtered call first, falls back to fetching all and filtering locally
        if the filtered call fails (e.g., on certain testnets).
        Uses the /v2/positions/margined endpoint.
        """
        target_product_id = int(product_id)
        logger.info(f"Attempting to fetch margined position for product_id: {target_product_id}")
        
        position_data = None
        response = None
        
        # --- Attempt 1: Filtered call ---
        try:
            response = self.make_request(
                'GET', 
                '/v2/positions/margined', 
                params={'product_id': target_product_id}
            )
            
            if response and response.get('success'):
                positions = response.get('result', [])
                if positions and isinstance(positions, list) and len(positions) > 0:
                    # Assume first (and likely only) item is the correct one when filtered
                    position_data = positions[0] 
                    # Optional: Double check product_id just in case
                    if int(position_data.get('product_id', -1)) == target_product_id:
                         logger.info(f"Found position via filtered call: {position_data.get('symbol')}")
                         return position_data # Success!
                    else:
                         logger.warning("Filtered position call returned data for unexpected product_id.")
                         position_data = None # Reset if ID doesn't match
                else:
                     logger.info(f"No open position found for product_id {target_product_id} via filtered call.")
                     return None # Success, but no position exists
                 
            else:
                # API call succeeded structurally but returned success: false
                logger.warning(f"Filtered position call returned success=false or invalid data: {response}")
                # Proceed to fallback based on this failure

        except requests.exceptions.RequestException as e:
            # Check if it was a 4xx/5xx error, potentially indicating the filtered call isn't supported
            if e.response is not None:
                 logger.warning(f"Filtered position call failed with HTTP Status {e.response.status_code}. Will attempt fetching all positions.")
                 # Don't re-raise yet, just proceed to fallback
            else:
                 # Network error or other issue before getting a response
                 logger.error(f"Network or request error during filtered position call: {e}")
                 raise # Re-raise if it wasn't an HTTP error we can recover from
             
        except Exception as e:
            # Catch any other unexpected error during the first attempt
            logger.error(f"Unexpected error during filtered position call: {e}")
            # Depending on severity, either raise or proceed to fallback
            logger.warning("Proceeding to fetch all positions after unexpected error.")

        # --- Attempt 2: Fallback - Fetch all positions if first attempt didn't return data ---
        if position_data is None:
            logger.info("Filtered position call failed or returned no data. Fetching all positions as fallback...")
            try:
                response_all = self.make_request('GET', '/v2/positions/margined') # No parameters
                
                if response_all and response_all.get('success'):
                    all_positions = response_all.get('result', [])
                    if not all_positions:
                        logger.info("Fetched all positions: None are open.")
                        return None # No positions open at all
                        
                    # Filter locally
                    for pos in all_positions:
                        if isinstance(pos, dict) and int(pos.get('product_id', -1)) == target_product_id:
                            position_data = pos
                            logger.info(f"Found position via fallback and local filtering: {position_data.get('symbol')}")
                            break # Found it
                            
                    if position_data:
                        return position_data # Return the found position
                    else:
                        logger.info(f"No position found for product_id {target_product_id} after fetching all.")
                        return None # Target position doesn't exist among all positions
                else:
                     logger.error(f"Fallback call to fetch all positions failed or returned invalid data: {response_all}")
                     return None # Fallback also failed

            except Exception as e:
                logger.error(f"Error during fallback call to fetch all positions: {e}")
                # import traceback # Uncomment for detailed debug if needed
                # logger.error(traceback.format_exc())
                return None # Return None if fallback fails

        # Should ideally not reach here if logic is correct, but return None as final default
        return None

    def place_order(self, product_id, size, side, order_type, limit_price=None, stop_price=None, time_in_force='GTC'):
        """Place an order"""
        data = {
            'product_id': int(product_id),
            'size': int(size),
            'side': side,
            'order_type': order_type.lower(),
            'time_in_force': time_in_force
        }
        if limit_price:
            data['limit_price'] = str(limit_price)
        if stop_price:
            data['stop_price'] = str(stop_price)
        return self.make_request('POST', '/v2/orders', data=data)

    def cancel_order(self, order_id):
        """Cancel an order"""
        return self.make_request('DELETE', f'/v2/orders/{order_id}')

    def cancel_all_orders(self, product_id=None):
        """Cancel all orders, optionally for a specific product"""
        params = {}
        if product_id:
            params['product_id'] = int(product_id)
        return self.make_request('DELETE', '/v2/orders', params=params)
