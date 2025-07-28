# test_ssl_core.py
import ssl
import socket
import certifi

hostname = 'pypi.org'
port = 443
context = ssl.create_default_context(cafile=certifi.where())

print(f"Attempting to connect to {hostname}:{port} using certifi bundle: {certifi.where()}")

try:
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print(f"Successfully connected to {hostname}:{port}")
            print(f"Cipher used: {ssock.cipher()}")
            cert = ssock.getpeercert()
            # print(f"Peer certificate: {cert}") # Optional: print full cert
            print("SSL Verification seems OK using certifi bundle directly.")

except ssl.SSLCertVerificationError as e:
    print(f"\nERROR: SSL Verification Failed! Reason: {e}")
except Exception as e:
    print(f"\nERROR: An unexpected error occurred: {e}")