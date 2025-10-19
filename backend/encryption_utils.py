from Crypto.Cipher import AES
import base64
import os
from dotenv import load_dotenv

# Load environment variables (ensure backend .env is used and overrides any existing values)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

# Get encryption key from environment
KEY = os.getenv("ENCRYPTION_KEY", "mymitra-encryption-key-32chars!!").strip()

# Validate key length
if len(KEY) != 32:
    raise ValueError(f"ENCRYPTION_KEY must be exactly 32 characters long! Current length: {len(KEY)}")

def encrypt_data(data: str) -> str:
    cipher = AES.new(KEY.encode(), AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    return base64.b64encode(nonce + ciphertext).decode()

def decrypt_data(encrypted_data: str) -> str:
    raw = base64.b64decode(encrypted_data)
    nonce = raw[:16]
    ciphertext = raw[16:]
    cipher = AES.new(KEY.encode(), AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt(ciphertext).decode()
