from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import base64
import json

KEY = b'0123456789abcdef0123456789abcdef'

def encrypt(data):
    plaintext = json.dumps(data).encode() if isinstance(data, dict) else str(data).encode()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return {'encrypted_data': base64.b64encode(ciphertext).decode(), 'iv': base64.b64encode(iv).decode()}

def decrypt(enc_b64, iv_b64):
    try:
        ciphertext = base64.b64decode(enc_b64)
        iv = base64.b64decode(iv_b64)
        cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
        return {'decrypted_data': json.loads(plaintext.decode())}
    except Exception as e:
        return {'decrypted_data': f"Error: {str(e)}"}

def b64_encode(data):
    s = json.dumps(data) if isinstance(data, dict) else str(data)
    return {'encoded_data': base64.b64encode(s.encode()).decode()}

def b64_decode(data):
    try:
        return {'decoded_data': json.loads(base64.b64decode(data).decode())}
    except:
        return {'decoded_data': base64.b64decode(data).decode()}

def gen_dh():
    return {
        'public_key': "-----BEGIN PUBLIC KEY-----\nMII... (Simulated DH Key)\n-----END PUBLIC KEY-----",
        'session_id': base64.b64encode(os.urandom(8)).decode()
    }
