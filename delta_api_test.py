import requests
import urllib3
import json
from datetime import datetime

# Suppress InsecureRequestWarning for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DeltaApiTestClient:
    def __init__(self, base_url, api_key=None, api_secret=None, verify_ssl=False):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.verify_ssl = verify_ssl
        
        if not verify_ssl:
            print("WARNING: SSL verification is disabled. This is not secure!")
    
    def make_request(self, method, endpoint, params=None):
        """
        Make a request to the Delta Exchange API
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(
                    url,
                    params=params,
                    verify=self.verify_ssl
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            raise
        except Exception as e:
            print(f"Request Error: {e}")
            raise
    
    def test_connection(self):
        """
        Test the connection to Delta Exchange API
        """
        try:
            response = self.make_request('GET', '/v2/tickers', params={'symbol': 'BTCUSD'})
            print("\nConnection test successful!")
            print("Response data:")
            print(json.dumps(response, indent=2))
            return True
        except Exception as e:
            print(f"\nConnection test failed: {e}")
            return False

def main():
    # Test configuration
    base_url = 'https://cdn-ind.testnet.deltaex.org'
    
    print("Delta Exchange API Test Client")
    print("=============================")
    
    # First try with SSL verification
    print("\nTesting with SSL verification enabled...")
    client = DeltaApiTestClient(base_url, verify_ssl=True)
    success = client.test_connection()
    
    if not success:
        print("\nTrying again with SSL verification disabled...")
        client = DeltaApiTestClient(base_url, verify_ssl=False)
        client.test_connection()

if __name__ == "__main__":
    main() 