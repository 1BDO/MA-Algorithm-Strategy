import requests
import urllib3
import json
from requests.exceptions import SSLError

# Suppress only the single InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_api_connection(verify_ssl=True):
    """
    Test connection to Delta Exchange API
    Args:
        verify_ssl (bool): Whether to verify SSL certificates
    """
    url = "https://testnet-api.delta.exchange/v2/tickers?symbol=BTCUSD"
    
    print(f"\nTesting connection with SSL verification {'enabled' if verify_ssl else 'disabled'}...")
    
    try:
        response = requests.get(url, verify=verify_ssl)
        response.raise_for_status()
        
        # Pretty print the response
        data = response.json()
        print("\nConnection successful!")
        print("Response data:")
        print(json.dumps(data, indent=2))
        return True
        
    except SSLError as e:
        print(f"\nSSL Error occurred: {str(e)}")
        return False
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        return False

def main():
    print("Delta Exchange API Connection Test")
    print("=================================")
    
    # First try with SSL verification
    success = test_api_connection(verify_ssl=True)
    
    if not success:
        print("\nTrying again with SSL verification disabled...")
        print("WARNING: This is not secure and should only be used for testing!")
        test_api_connection(verify_ssl=False)
        print("\nNOTE: For production use, please fix SSL certificate issues instead of disabling verification.")

if __name__ == "__main__":
    main() 