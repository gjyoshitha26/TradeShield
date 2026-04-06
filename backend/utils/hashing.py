import bcrypt
import hmac
import hashlib
import json

def hash_pass(password):
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode(), salt)
    return {
        'hash': hashed.decode(),
        'salt_rounds': 12
    }

def verify_pass(password, hashed):
    return {
        'verified': bcrypt.checkpw(password.encode(), hashed.encode())
    }

def sign(data):
    msg = json.dumps(data).encode()
    signature = hmac.new(b'secret-key', msg, hashlib.sha256).hexdigest()
    return {'signature': signature}

def verify_sig(data, signature):
    msg = json.dumps(data).encode()
    expected = hmac.new(b'secret-key', msg, hashlib.sha256).hexdigest()
    return {'signature_valid': hmac.compare_digest(signature, expected)}
