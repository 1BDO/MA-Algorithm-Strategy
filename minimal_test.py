# minimal_test.py
import requests
import certifi
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

url = 'https://api.india.delta.exchange'
#url = 'https://google.com' # You can also try a different known-good site
cert_path = certifi.where()

logging.info(f"Attempting GET request to: {url}")
logging.info(f"Using CA bundle: {cert_path}")

try:
    response = requests.get(url, verify=cert_path, timeout=15)
    response.raise_for_status()
    logging.info(f"Success! Status Code: {response.status_code}")
    # logging.info(f"Response JSON: {response.json()}") # Optionally print response
except requests.exceptions.SSLError as e:
    logging.error(f"SSL Error during minimal test: {e}")
except requests.exceptions.RequestException as e:
    logging.error(f"Request Error during minimal test: {e}")
except Exception as e:
    logging.error(f"An unexpected error occurred: {e}")