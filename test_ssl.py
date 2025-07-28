import requests
import certifi
import json

def test_ssl_connection():
    try:
        # Test connection with explicit SSL certificate verification
        response = requests.get(
            "https://testnet-api.delta.exchange/v2/tickers?symbol=BTCUSD",
            verify=certifi.where()
        )
        
        # Print response status and data
        print(f"Connection Status: {response.status_code}")
        print("Response Data:")
        print(json.dumps(response.json(), indent=2))
        
        return True
    except requests.exceptions.SSLError as ssl_err:
        print(f"SSL Error: {ssl_err}")
        return False
    except Exception as e:
        print(f"Other Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing SSL connection to Delta Exchange API...")
    success = test_ssl_connection()
    print(f"\nTest {'succeeded' if success else 'failed'}") 