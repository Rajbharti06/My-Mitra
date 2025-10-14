from Crypto.Cipher import AES
import base64
import os

KEY = os.getenv("AES_KEY", "32_byte_random_key_here!!")  # Store securely

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
