import os, base64, json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from config import Config

def get_key():
    k = Config.AES_KEY
    return (k.encode() if isinstance(k, str) else k)[:32].ljust(32, b'\0')

def encrypt(data):
    iv = os.urandom(16)
    text = json.dumps(data) if isinstance(data, dict) else str(data)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(text.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(get_key()), modes.CBC(iv), backend=default_backend())
    enc = cipher.encryptor()
    ct = enc.update(padded) + enc.finalize()
    return {'encrypted_data': base64.b64encode(ct).decode(), 'iv': base64.b64encode(iv).decode()}

def decrypt(ct, iv):
    cipher = Cipher(algorithms.AES(get_key()), modes.CBC(base64.b64decode(iv)), backend=default_backend())
    dec = cipher.decryptor()
    pt = dec.update(base64.b64decode(ct)) + dec.finalize()
    unpad = padding.PKCS7(128).unpadder()
    data = unpad.update(pt) + unpad.finalize()
    try: return {'decrypted_data': json.loads(data.decode())}
    except: return {'decrypted_data': data.decode()}

def b64_encode(data):
    txt = json.dumps(data) if isinstance(data, dict) else str(data)
    return {'encoded_data': base64.b64encode(txt.encode()).decode()}

def b64_decode(enc):
    dec = base64.b64decode(enc).decode()
    try: return {'decoded_data': json.loads(dec)}
    except: return {'decoded_data': dec}

def gen_dh():
    from cryptography.hazmat.primitives.asymmetric import dh
    from cryptography.hazmat.primitives import serialization
    params = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())
    priv = params.generate_private_key()
    pub = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return {'public_key': pub.decode(), 'session_id': base64.b64encode(os.urandom(16)).decode()}
